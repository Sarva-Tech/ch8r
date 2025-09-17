import json
from rest_framework import serializers
from core.models import NotificationProfile
from core.services.encryption import encrypt


class NotificationProfileSerializer(serializers.ModelSerializer):
    config = serializers.JSONField()

    class Meta:
        model = NotificationProfile
        fields = ['id', 'uuid', 'type', 'config', 'created_at', 'name']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        config = validated_data.pop('config', {})

        instance = NotificationProfile(**validated_data)

        encrypted_config = encrypt(config)
        instance._config = encrypt(encrypted_config)
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        config = getattr(instance, 'config', {})
        filtered_config = {}
        if isinstance(config, dict) and 'email' in config:
            filtered_config['email'] = config['email']

        representation['config'] = filtered_config
        return representation