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

from core.consts import LIVE_UPDATES_PREFIX
from core.models.application import Application
from core.models.chatroom import ChatRoom
from core.models.chatroom_participant import ChatroomParticipant
from core.models.message import Message

from core.serializers.message import CreateMessageSerializer, ViewMessageSerializer
from core.tasks import generate_bot_response
from core.tasks.message import AGENT_IDENTIFIER
from core.widget_auth import WidgetTokenAuthentication, IsAuthenticatedOrWidget
from core.permissions import HasAPIKeyPermission
from core.throttle import UserApplicationRateThrottle

logger = logging.getLogger(__name__)

def generate_chatroom_name(a, b):
    return f"chat:{':'.join(sorted([a, b]))}"

class SendMessageView(APIView):
    authentication_classes = [WidgetTokenAuthentication, SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrWidget | HasAPIKeyPermission]
    throttle_classes = [UserApplicationRateThrottle]

    def post(self, request, application_uuid):
        # Refactor
        if request.user and request.user.is_authenticated:
            app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        else:
            app = getattr(request, 'application', None)
            if not app or str(app.uuid) != str(application_uuid):
                return Response({'detail': 'Invalid or unauthorized widget token'}, status=403)

        serializer = CreateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        chatroom_uuid = data.get('chatroom_identifier')
        sender_id = data.get('sender_identifier')
        message_text = data['message']
        metadata = data.get('metadata', {})

        send_to_user = data['send_to_user']
        metadata['send_to_user'] = send_to_user

        if not chatroom_uuid and not sender_id:
            return Response(
                {"detail": "sender_identifier is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if chatroom_uuid != 'new_chat':
            chatroom = get_object_or_404(ChatRoom, uuid=chatroom_uuid, application=app)

            if sender_id and not ChatroomParticipant.objects.filter(chatroom=chatroom,
                                                                    user_identifier=sender_id).exists():
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
                    name=chatroom_name
                )

                ChatroomParticipant.objects.bulk_create([
                    ChatroomParticipant(chatroom=chatroom, user_identifier=sender_id, role='user'),
                    ChatroomParticipant(chatroom=chatroom, user_identifier=AGENT_IDENTIFIER, role='agent'),
                ])

        message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=sender_id,
            message=message_text,
            metadata=metadata
        )

        if send_to_user:
            channel_layer = get_channel_layer()
            participants = list(
                message.chatroom.participants.filter(
                    Q(role='user') & Q(user_identifier__startswith='anon_')
                ).values_list('user_identifier', flat=True)
            )

            for participant_id in participants:
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

        else:
            generate_bot_response.delay(message.id, app.uuid)

        response_data = ViewMessageSerializer(message).data
        response_data['message_status'] = 'message_sent'
        response_data['llm_processing'] = True
        response_data['chatroom_identifier'] = chatroom.uuid
        return Response(ViewMessageSerializer(message).data, status=status.HTTP_200_OK)
