from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from core.permissions import HasAPIKeyPermission
from core.models.application import Application
from core.models.chatroom import ChatRoom
from core.models.chatroom_participant import ChatroomParticipant
from core.widget_auth import WidgetTokenAuthentication, IsAuthenticatedOrWidget
from core.consts import DASHBOARD_USER_ID_PREFIX
from core.services.unread import mark_read_for_participant, broadcast_unread_update

from core.serializers.chatroom import ChatRoomWithMessagesSerializer, ChatRoomDetailSerializer


class ChatRoomMessagesView(APIView):
    authentication_classes = [WidgetTokenAuthentication, SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrWidget | HasAPIKeyPermission]

    def get(self, request, application_uuid, chatroom_uuid):
        if request.user and request.user.is_authenticated:
            application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        else:
            application = getattr(request, 'application', None)
            if not application or str(application.uuid) != str(application_uuid):
                return Response({'detail': 'Invalid or unauthorized widget token'}, status=403)

        chatroom = get_object_or_404(ChatRoom, uuid=chatroom_uuid, application=application)

        if request.user and request.user.is_authenticated:
            user_identifier = f"{DASHBOARD_USER_ID_PREFIX}_{request.user.id}"
        else:
            user_identifier = (
                request.data.get('sender_identifier')
                or request.query_params.get('sender_identifier')
            )

        if user_identifier:
            mark_read_for_participant(chatroom, user_identifier)
            broadcast_unread_update(user_identifier, str(chatroom.uuid), False, user_identifier)

        if request.user and request.user.is_authenticated:
            messages_qs = chatroom.messages.all()
        else:
            messages_qs = chatroom.messages.filter(is_internal=False)

        serializer = ChatRoomWithMessagesSerializer(chatroom, context={'messages_qs': messages_qs})
        return Response(serializer.data)


class ChatRoomModeView(APIView):
    """PATCH /applications/{app_uuid}/chatrooms/{chatroom_uuid}/mode/
    Allows widget users and dashboard users to change the mode of a chatroom.
    """
    authentication_classes = [WidgetTokenAuthentication, SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrWidget | HasAPIKeyPermission]

    def patch(self, request, application_uuid, chatroom_uuid):
        if request.user and request.user.is_authenticated:
            application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        else:
            application = getattr(request, 'application', None)
            if not application or str(application.uuid) != str(application_uuid):
                return Response({'detail': 'Invalid or unauthorized widget token'}, status=403)

        chatroom = get_object_or_404(ChatRoom, uuid=chatroom_uuid, application=application)

        # Verify the requester is a participant
        sender_identifier = (
            request.data.get('sender_identifier')
            or request.query_params.get('sender_identifier')
        )
        if not request.user or not request.user.is_authenticated:
            if not sender_identifier:
                return Response({'detail': 'sender_identifier is required'}, status=status.HTTP_400_BAD_REQUEST)
            is_participant = ChatroomParticipant.objects.filter(
                chatroom=chatroom, user_identifier=sender_identifier
            ).exists()
            if not is_participant:
                return Response({'detail': 'Not a participant of this chatroom'}, status=status.HTTP_403_FORBIDDEN)

        mode = request.data.get('mode')
        if mode not in ('ai', 'direct'):
            return Response({'detail': 'mode must be "ai" or "direct"'}, status=status.HTTP_400_BAD_REQUEST)

        chatroom.mode = mode
        chatroom.save(update_fields=['mode'])

        return Response({'uuid': str(chatroom.uuid), 'mode': chatroom.mode})


class ChatRoomDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]
    def get(self, request, chatroom_uuid):
        try:
            chatroom = ChatRoom.objects.prefetch_related('messages', 'participants').get(uuid=chatroom_uuid)
        except ChatRoom.DoesNotExist:
            return Response({"detail": "ChatRoom not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChatRoomDetailSerializer(chatroom)
        return Response(serializer.data)
