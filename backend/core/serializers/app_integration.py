from rest_framework import serializers

from core.models import AppIntegration
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