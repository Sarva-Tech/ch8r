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
from django.db import transaction
from core.serializers.chatroom import ChatRoomWithMessagesSerializer, ChatRoomDetailSerializer, ChatRoomUpdateSerializer, ChatRoomViewSerializer


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
            messages_qs = chatroom.messages.all().order_by('created_at')
        else:
            messages_qs = chatroom.messages.filter(is_internal=False).order_by('created_at')

        serializer = ChatRoomWithMessagesSerializer(chatroom, context={'messages_qs': messages_qs})
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

class ChatRoomUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]

    def patch(self, request, application_uuid, chatroom_uuid):
        application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        chatroom = get_object_or_404(ChatRoom, uuid=chatroom_uuid, application=application)

        serializer = ChatRoomUpdateSerializer(chatroom, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ChatRoomViewSerializer(chatroom).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, application_uuid, chatroom_uuid):
        return self.patch(request, application_uuid, chatroom_uuid)

    def delete(self, request, application_uuid, chatroom_uuid):
        application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        chatroom = get_object_or_404(ChatRoom, uuid=chatroom_uuid, application=application)

        try:
            with transaction.atomic():
                deleted_messages = chatroom.messages.all().count()
                chatroom.messages.all().delete()
                deleted_participants = chatroom.participants.all().count()
                chatroom.participants.all().delete()
                chatroom.delete()
            return Response({
                'detail': 'Chatroom deleted successfully',
                'deleted_messages': deleted_messages,
                'deleted_participants': deleted_participants
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'detail': 'Failed to delete chatroom',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
