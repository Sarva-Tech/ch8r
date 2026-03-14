import uuid

from rest_framework import serializers
from core.models import Message, AIProvider

class CreateMessageSerializer(serializers.Serializer):
    chatroom_identifier = serializers.CharField(required=False)
    sender_identifier = serializers.CharField(required=False)
    message = serializers.CharField()
    metadata = serializers.JSONField(required=False)
    send_to_participant = serializers.BooleanField(required=False, default=False)
    ai_provider = serializers.IntegerField(required=False)
    model = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.app_owner = kwargs.pop('app_owner', None)
        super().__init__(*args, **kwargs)

    def validate_ai_provider(self, value):
        if value is not None:
            try:
                ai_provider = AIProvider.objects.get(id=value, creator=self.app_owner)
            except AIProvider.DoesNotExist:
                raise serializers.ValidationError('Invalid AI provider')
        return value


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
            'ai_provider_id',
            'model',
            'created_at'
        ]
