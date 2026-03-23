from rest_framework import serializers

from core.models.app_integration import AppIntegration
from core.serializers.integration import IntegrationViewSerializer

class AppIntegrationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppIntegration
        fields = ['application', 'integration']

class AppIntegrationViewSerializer(serializers.ModelSerializer):
    integration = IntegrationViewSerializer(read_only=True)

    class Meta:
        model = AppIntegration
        fields = [
            'id',
            'integration',
            'metadata',
            'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        integration_data = IntegrationViewSerializer(instance.integration).data
        integration_data["metadata"] = instance.metadata
        integration_data["app_integration_uuid"] = str(instance.id)
        return integration_data
