import json
import importlib

from rest_framework import serializers

from core.consts import SUPPORTED_INTEGRATIONS
from core.models import Integration


class IntegrationSerializer(serializers.ModelSerializer):
    supported_types = serializers.SerializerMethodField()

    class Meta:
        model = Integration
        exclude = ['credentials']

    def get_supported_types(self, obj):
        entry = next((p for p in SUPPORTED_INTEGRATIONS if p['id'] == obj.provider), None)
        return entry['supported_types'] if entry else []


# Alias for backward compatibility
IntegrationViewSerializer = IntegrationSerializer


class IntegrationCreateSerializer(serializers.ModelSerializer):
    token = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Integration
        fields = ['uuid', 'name', 'provider', 'token', 'creator']
        read_only_fields = ['uuid', 'creator']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['token'].required = False
            self.fields['token'].allow_blank = True
            self.fields['provider'].read_only = True

    def validate_provider(self, value):
        supported_ids = [p['id'] for p in SUPPORTED_INTEGRATIONS]
        if value not in supported_ids:
            raise serializers.ValidationError(
                f"Provider '{value}' is not supported. Supported providers are: {', '.join(supported_ids)}"
            )
        return value

    def validate(self, attrs):
        token = attrs.get('token')

        if token:
            provider = attrs.get('provider') or (self.instance.provider if self.instance else None)
            entry = next((p for p in SUPPORTED_INTEGRATIONS if p['id'] == provider), None)

            if entry and entry.get('validate'):
                module_path, func_name = entry['validate'].rsplit('.', 1)
                module = importlib.import_module(module_path)
                validator = getattr(module, func_name)

                valid, reason, account_metadata = validator({"token": token})
                if not valid:
                    # Store on instance so the view can return a clean response shape
                    self._credential_error = reason
                else:
                    self._account_metadata = account_metadata

        return attrs

    def create(self, validated_data):
        token = validated_data.pop('token')
        validated_data['credentials'] = json.dumps({"token": token})
        validated_data['creator'] = self.context['request'].user
        # Merge account metadata from validation if available
        if hasattr(self, '_account_metadata') and self._account_metadata:
            existing = validated_data.get('metadata') or {}
            validated_data['metadata'] = {**existing, 'account': self._account_metadata}
        return super().create(validated_data)

    def update(self, instance, validated_data):
        token = validated_data.pop('token', None)
        if token:
            validated_data['credentials'] = json.dumps({"token": token})
            if hasattr(self, '_account_metadata') and self._account_metadata:
                existing = instance.metadata or {}
                validated_data['metadata'] = {**existing, 'account': self._account_metadata}
        return super().update(instance, validated_data)
