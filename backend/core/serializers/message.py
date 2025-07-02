from rest_framework import serializers
from core.models import Message

class CreateMessageSerializer(serializers.Serializer):
    chatroom_identifier = serializers.UUIDField(required=False)
    sender_identifier = serializers.CharField(required=False)
    message = serializers.CharField()
    metadata = serializers.JSONField(required=False)

class ViewMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id',
            'uuid',
            'sender_identifier',
            'message',
            'metadata',
            'created_at'
        ]
