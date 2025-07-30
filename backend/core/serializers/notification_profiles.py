from rest_framework import serializers
from core.models import NotificationProfile

class NotificationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationProfile
        fields = ['id', 'type', 'config', 'created_at', 'name']
        read_only_fields = ['id', 'created_at']
