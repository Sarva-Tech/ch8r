from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from core.permissions import HasAPIKeyPermission
from core.models.application import Application
from core.models.chatroom import ChatRoom
from core.widget_auth import WidgetTokenAuthentication, IsAuthenticatedOrWidget
from core.consts import REGISTERED_USER_ID_PREFIX
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
            user_identifier = f"{REGISTERED_USER_ID_PREFIX}_{request.user.id}"
        else:
            user_identifier = (
                request.data.get('sender_identifier')
                or request.query_params.get('sender_identifier')
            )

        if user_identifier:
            mark_read_for_participant(chatroom, user_identifier)
            broadcast_unread_update(user_identifier, str(chatroom.uuid), False, user_identifier)

        serializer = ChatRoomWithMessagesSerializer(chatroom)
        return Response(serializer.data)


class ChatRoomDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]
    def get(self, request, chatroom_uuid):
        try:
            chatroom = ChatRoom.objects.prefetch_related('messages', 'participants').get(uuid=chatroom_uuid)
        except ChatRoom.DoesNotExist:
            return Response({"detail": "ChatRoom not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChatRoomDetailSerializer(chatroom)
        return Response(serializer.data)
