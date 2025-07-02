from rest_framework import serializers

from core.models import ChatroomParticipant
from core.models.chatroom import ChatRoom
from core.serializers import ApplicationViewSerializer
from core.serializers.message import ViewMessageSerializer

class ChatRoomViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['uuid', 'name']

class ChatRoomWithMessagesSerializer(serializers.ModelSerializer):
    application = ApplicationViewSerializer(read_only=True)
    messages = ViewMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['uuid', 'name', 'application', 'messages']

class ChatroomParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatroomParticipant
        fields = ['uuid', 'user_identifier', 'role', 'metadata']

class ChatRoomPreviewSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['uuid', 'name', 'last_message']

    def get_last_message(self, chatroom):
        last_msg = chatroom.messages.order_by('-created_at').first()
        return ViewMessageSerializer(last_msg).data if last_msg else None

class ChatRoomDetailSerializer(serializers.ModelSerializer):
    participants = ChatroomParticipantSerializer(many=True, read_only=True)
    messages = ViewMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['uuid', 'name', 'participants', 'messages']
