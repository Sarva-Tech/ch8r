from rest_framework import serializers

from core.models import Integration, AppIntegration
from core.serializers.integration import IntegrationSerializer
from core.consts import SUPPORTED_INTEGRATIONS


class AppIntegrationSerializer(serializers.ModelSerializer):
    integration = IntegrationSerializer(read_only=True)

    class Meta:
        model = AppIntegration
        fields = ['uuid', 'integration', 'integration_type', 'metadata', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'integration', 'integration_type', 'metadata', 'is_active', 'created_at', 'updated_at']


AppIntegrationViewSerializer = AppIntegrationSerializer


class AppIntegrationCreateSerializer(serializers.ModelSerializer):
    integration_uuid = serializers.UUIDField(write_only=True)
    integration_type = serializers.CharField()
    metadata = serializers.JSONField(required=False)

    class Meta:
        model = AppIntegration
        fields = ['integration_uuid', 'integration_type', 'metadata']

    def to_representation(self, instance):
        return AppIntegrationSerializer(instance, context=self.context).data

    def validate_integration_uuid(self, value):
        try:
            integration = Integration.objects.get(uuid=value)
        except Integration.DoesNotExist:
            raise serializers.ValidationError("Integration not found")

        request = self.context['request']
        if integration.creator != request.user:
            raise serializers.ValidationError("You don't own this integration")

        self._integration = integration
        return value

    def validate(self, data):
        integration = self._integration
        provider = integration.provider
        entry = next((e for e in SUPPORTED_INTEGRATIONS if e['id'] == provider), None)

        if entry is None or data['integration_type'] not in entry['supported_types']:
            raise serializers.ValidationError(
                {"integration_type": f"Integration type '{data['integration_type']}' is not supported for provider '{provider}'"}
            )

        return data

    def create(self, validated_data):
        validated_data.pop('integration_uuid')
        integration = self._integration
        integration_type = validated_data.pop('integration_type')
        metadata = validated_data.pop('metadata', None)
        application = self.context['application']

        instance, _ = AppIntegration.objects.update_or_create(
            application=application,
            integration_type=integration_type,
            defaults={
                'integration': integration,
                'metadata': metadata,
                'is_active': True,
            }
        )
        return instance
