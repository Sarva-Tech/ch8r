import json
from rest_framework import serializers
from core.models import NotificationProfile
from core.services.encryption import encrypt


class NotificationProfileSerializer(serializers.ModelSerializer):
    config = serializers.JSONField()

    class Meta:
        model = NotificationProfile
        fields = ['id', 'uuid', 'type', 'config', 'created_at', 'name', 'owner']
        read_only_fields = ['id', 'created_at', 'owner']

    def create(self, validated_data):
        config = validated_data.pop('config', {})
        instance = NotificationProfile(**validated_data)
        instance.config = config
        instance.save()
        return instance

    def update(self, instance, validated_data):
        config = validated_data.pop('config', None)

        if 'name' in validated_data:
            instance.name = validated_data['name']

        if config is not None:
            current_config = getattr(instance, 'config', {}) or {}
            new_config = current_config.copy()

            if 'email' in config and config['email']:
                new_config['email'] = config['email']

            webhook_url = config.get('webhookUrl') or config.get('webhook_url')
            if webhook_url and isinstance(webhook_url, str) and webhook_url.strip():
                new_config['webhookUrl'] = webhook_url.strip()

            instance.config = new_config

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        config = getattr(instance, 'config', {}) or {}
        safe_config = {}
        if isinstance(config, dict):
            if 'email' in config:
                safe_config['email'] = config['email']
            if 'webhookUrl' in config:
                safe_config['webhookUrl'] = config['webhookUrl']
            if 'webhook_url' in config:
                safe_config['webhookUrl'] = config['webhook_url']
        representation['config'] = safe_config
        return representation