import uuid

from rest_framework import serializers
from core.models import Message

class CreateMessageSerializer(serializers.Serializer):
    chatroom_identifier = serializers.CharField(required=False)
    sender_identifier = serializers.CharField(required=False)
    message = serializers.CharField()
    metadata = serializers.JSONField(required=False)
    send_to_user = serializers.BooleanField(required=False, default=False)

    def validate_chatroom_identifier(self, value):
        if value == 'new_chat':
            return value
        try:
            return str(uuid.UUID(value))
        except ValueError:
            raise serializers.ValidationError('Must be a valid UUID or "new_chat"')


class ViewMessageSerializer(serializers.ModelSerializer):
    chatroom_identifier = serializers.UUIDField(source='chatroom.uuid', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'uuid',
            'sender_identifier',
            'chatroom_identifier',
            'message',
            'metadata',
            'created_at'
        ]
