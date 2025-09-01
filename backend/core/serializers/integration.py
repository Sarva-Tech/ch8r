from rest_framework import serializers
from core.models import Integration

class IntegrationCreateSerializer(serializers.ModelSerializer):
    token = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Integration
        fields = ['name', 'type', 'provider', 'token']

    def create(self, validated_data):
        config_fields = {}
        if 'token' in validated_data:
            config_fields['token'] = validated_data.pop('token')

        integration = Integration(**validated_data)
        integration.owner = self.context['request'].user
        integration.config = config_fields
        integration.save()
        return integration

    def update(self, instance, validated_data):
        config_fields = {}
        if 'token' in validated_data:
            config_fields['token'] = validated_data.pop('token')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if config_fields:
            current_config = instance.config or {}
            current_config.update(config_fields)
            instance.config = current_config

        instance.save()
        return instance

class IntegrationViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = ['id', 'uuid', 'name', 'type', 'provider', 'metadata', 'created_at', 'updated_at']
