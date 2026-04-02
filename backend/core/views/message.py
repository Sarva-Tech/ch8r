from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
import logging

from core.consts import DASHBOARD_USER_ID_PREFIX, LIVE_UPDATES_PREFIX
from core.services.unread import mark_unread_for_participants, broadcast_unread_update
from core.models.application import Application
from core.models.chatroom import ChatRoom
from core.models.chatroom_participant import ChatroomParticipant
from core.models.message import Message
from core.models.ai_provider import AIProvider
from core.utils import normalize_model_name_by_provider

from core.serializers.message import CreateMessageSerializer, ViewMessageSerializer
from core.tasks import generate_bot_response
from core.tasks.message import AGENT_IDENTIFIER
from core.widget_auth import WidgetTokenAuthentication, IsAuthenticatedOrWidget
from core.permissions import HasAPIKeyPermission

logger = logging.getLogger(__name__)

def generate_chatroom_name(a, b):
    return f"chat:{':'.join(sorted([a, b]))}"

class SendMessageView(APIView):
    authentication_classes = [WidgetTokenAuthentication, SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrWidget | HasAPIKeyPermission]

    def post(self, request, application_uuid):
        if request.user and request.user.is_authenticated:
            app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        else:
            app = getattr(request, 'application', None)
            if not app or str(app.uuid) != str(application_uuid):
                return Response({'detail': 'Invalid or unauthorized widget token'}, status=403)

        platform = 'dashboard' if (request.user and request.user.is_authenticated) else 'widget'

        serializer = CreateMessageSerializer(data=request.data, app_owner=app.owner)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        chatroom_uuid = data.get('chatroom_identifier')
        sender_id = data.get('sender_identifier')
        message_text = data['message']
        metadata = data.get('metadata', {})

        is_internal = data.get('is_internal', False) if (request.user and request.user.is_authenticated) else False

        if platform == 'dashboard' and not is_internal and data.get('ai_mode', False):
            return Response(
                {'detail': 'AI mode is not permitted on external messages (is_internal=false).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ai_mode = data.get('ai_mode', False)
        ai_provider_id = data.get('ai_provider')
        model = data.get('model')

        if not chatroom_uuid and not sender_id:
            return Response(
                {"detail": "sender_identifier is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if chatroom_uuid != 'new_chat':
            chatroom = get_object_or_404(ChatRoom, uuid=chatroom_uuid, application=app)

            updated = False
            if ai_provider_id is not None and ai_provider_id != chatroom.ai_provider_id:
                chatroom.ai_provider_id = ai_provider_id
                updated = True
            if model is not None and model != chatroom.model:
                provider_name = ''
                if ai_provider_id:
                    try:
                        ai_provider = AIProvider.objects.only('provider').get(id=ai_provider_id)
                        provider_name = ai_provider.provider
                    except AIProvider.DoesNotExist:
                        pass
                model = normalize_model_name_by_provider(model, provider_name)
                chatroom.model = model
                updated = True
            if updated:
                chatroom.save()

            if sender_id and not ChatroomParticipant.objects.filter(
                chatroom=chatroom, user_identifier=sender_id
            ).exists():
                ChatroomParticipant.objects.create(
                    chatroom=chatroom,
                    user_identifier=sender_id,
                    role='user'
                )

        else:
            chatroom_name = generate_chatroom_name(sender_id, AGENT_IDENTIFIER)

            with transaction.atomic():
                chatroom = ChatRoom.objects.create(
                    application=app,
                    name=chatroom_name,
                    ai_provider_id=ai_provider_id,
                    model=model,
                )

                agent_identifier = metadata.get('human_agent_identifier', AGENT_IDENTIFIER)

                ChatroomParticipant.objects.bulk_create([
                    ChatroomParticipant(chatroom=chatroom, user_identifier=sender_id, role='user'),
                    ChatroomParticipant(chatroom=chatroom, user_identifier=agent_identifier, role='agent'),
                ])

        message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=sender_id,
            message=message_text,
            metadata=metadata,
            is_internal=is_internal,
            platform=platform,
            ai_mode=ai_mode,
            ai_provider_id=ai_provider_id,
            model=model,
        )

        unread_identifiers = mark_unread_for_participants(chatroom, sender_id, is_internal=is_internal)
        for user_identifier in unread_identifiers:
            broadcast_unread_update(user_identifier, str(chatroom.uuid), True, sender_id)

        channel_layer = get_channel_layer()

        def get_widget_participants():
            return list(
                message.chatroom.participants.filter(
                    user_identifier__startswith='widget_'
                ).exclude(
                    user_identifier=sender_id
                ).values_list('user_identifier', flat=True)
            )

        def get_dashboard_participants():
            return list(
                message.chatroom.participants.filter(
                    Q(user_identifier__startswith='dashboard_') | Q(role='human_agent')
                ).exclude(
                    user_identifier=sender_id
                ).values_list('user_identifier', flat=True)
            )

        def broadcast_to(participant_ids):
            for participant_id in participant_ids:
                group_name = f"{LIVE_UPDATES_PREFIX}_{participant_id}"
                try:
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            "type": "send.message",
                            "message": ViewMessageSerializer(message).data,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to send message to {group_name}: {str(e)}")

        if platform == 'widget':
            if ai_mode:
                # Widget already has the message optimistically; send to dashboard only
                broadcast_to(get_dashboard_participants())
                generate_bot_response.delay(message.id, app.uuid, ai_provider_id, model)
            else:
                broadcast_to(get_dashboard_participants())

        else:
            if is_internal:
                if ai_mode:
                    # Dashboard sent this — participants query already excludes sender
                    broadcast_to(get_dashboard_participants())
                    generate_bot_response.delay(message.id, app.uuid, ai_provider_id, model)
                else:
                    pass
            else:
                broadcast_to(get_widget_participants())

        # If a new chatroom was just created, notify dashboard participants so their
        # chatroom list updates live without a page refresh.
        if chatroom_uuid == 'new_chat':
            try:
                from core.serializers.chatroom import ChatRoomPreviewSerializer
                chatroom_data = ChatRoomPreviewSerializer(
                    chatroom, context={'user_identifier': sender_id}
                ).data
                dashboard_id = f"{DASHBOARD_USER_ID_PREFIX}_{app.owner.id}"
                group_name = f"{LIVE_UPDATES_PREFIX}_{dashboard_id}"
                try:
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {"type": "send.new.chatroom", "chatroom": chatroom_data},
                    )
                except Exception as e:
                    logger.warning(f"Failed to send new_chatroom to {group_name}: {e}")
            except Exception as e:
                logger.warning(f"Failed to broadcast new chatroom: {e}")

        response_data = ViewMessageSerializer(message).data
        response_data['message_status'] = 'message_sent'
        response_data['chatroom_identifier'] = str(chatroom.uuid)
        return Response(response_data, status=status.HTTP_200_OK)
