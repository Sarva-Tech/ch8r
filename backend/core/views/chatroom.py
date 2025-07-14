from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework_api_key.permissions import HasAPIKey

from core.models.application import Application
from core.models.chatroom import ChatRoom

from core.serializers.chatroom import ChatRoomWithMessagesSerializer, ChatRoomDetailSerializer


class ChatRoomMessagesView(APIView):
    permission_classes = [IsAuthenticated | HasAPIKey]

    def get(self, request, application_uuid, chatroom_uuid):
        application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        chatroom = get_object_or_404(ChatRoom, uuid=chatroom_uuid, application=application)

        serializer = ChatRoomWithMessagesSerializer(chatroom)

        return Response(serializer.data)


class ChatRoomDetailView(APIView):
    def get(self, request, chatroom_uuid):
        try:
            chatroom = ChatRoom.objects.prefetch_related('messages', 'participants').get(uuid=chatroom_uuid)
        except ChatRoom.DoesNotExist:
            return Response({"detail": "ChatRoom not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChatRoomDetailSerializer(chatroom)
        return Response(serializer.data)
