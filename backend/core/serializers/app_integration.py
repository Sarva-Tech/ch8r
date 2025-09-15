from rest_framework import serializers

from core.models.app_integration import AppIntegration
from core.serializers.integration import IntegrationViewSerializer

class AppIntegrationViewSerializer(serializers.ModelSerializer):
    integration = IntegrationViewSerializer(read_only=True)

    class Meta:
        model = AppIntegration
        fields = [
            'id', 'uuid',
            'integration',
            'metadata',
            'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        integration_data = IntegrationViewSerializer(instance.integration).data
        integration_data["metadata"] = instance.metadata
        integration_data["app_integration_uuid"] = str(instance.uuid)
        return integration_data
