from rest_framework import serializers

from core.models import ChatroomParticipant, AIProvider
from core.models.chatroom import ChatRoom
from core.serializers import ApplicationViewSerializer
from core.serializers.message import ViewMessageSerializer
from core.serializers.ai_provider import AIProviderSerializer

class ChatRoomViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['uuid', 'name', 'ai_provider', 'model']

class ChatRoomWithMessagesSerializer(serializers.ModelSerializer):
    application = ApplicationViewSerializer(read_only=True)
    ai_provider = AIProviderSerializer(read_only=True)
    ai_model = serializers.CharField(source='model', read_only=True)
    messages = ViewMessageSerializer(many=True, read_only=True)
    chatroom = ChatRoomViewSerializer(read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['uuid', 'name', 'application', 'messages', 'ai_provider', 'ai_model', 'chatroom']

class ChatroomParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatroomParticipant
        fields = ['uuid', 'user_identifier', 'role', 'metadata']

class ChatRoomPreviewSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    has_unread = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['uuid', 'name', 'last_message', 'has_unread']

    def get_last_message(self, chatroom):
        last_msg = chatroom.messages.order_by('-created_at').first()
        return ViewMessageSerializer(last_msg).data if last_msg else None

    def get_has_unread(self, chatroom):
        user_identifier = self.context.get('user_identifier')
        if not user_identifier:
            return False
        result = ChatroomParticipant.objects.filter(
            chatroom=chatroom,
            user_identifier=user_identifier
        ).values_list('has_unread', flat=True).first()
        return result if result is not None else False

class ChatRoomDetailSerializer(serializers.ModelSerializer):
    participants = ChatroomParticipantSerializer(many=True, read_only=True)
    messages = ViewMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['uuid', 'name', 'participants', 'messages']
