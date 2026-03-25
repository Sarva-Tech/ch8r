from rest_framework import serializers
from typing import Dict, Any

from core.models.app_integration import AppIntegration
from core.serializers.integration import IntegrationViewSerializer


class AppIntegrationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppIntegration
        fields = ['application', 'integration']
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        return attrs


class AppIntegrationViewSerializer(serializers.ModelSerializer):
    integration = IntegrationViewSerializer(read_only=True)

    class Meta:
        model = AppIntegration
        fields = [
            'id',
            'integration',
            'metadata',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance: AppIntegration) -> Dict[str, Any]:
        integration_data = IntegrationViewSerializer(instance.integration).data
        
        integration_data.update({
            'metadata': instance.metadata or {},
            'app_integration_uuid': str(instance.id)
        })
        
        return integration_data
