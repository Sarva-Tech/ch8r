from rest_framework import serializers

from core.models.integration import Integration
from core.models.application import Application
from core.serializers.app_model import AppModelViewSerializer
from core.serializers.app_integration import AppIntegrationViewSerializer


class LoadAppConfigurationSerializer(serializers.ModelSerializer):
    llm_models = AppModelViewSerializer(source="model_configs", many=True, read_only=True)
    integrations = AppIntegrationViewSerializer(source="app_integrations", many=True, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "uuid", "name",
            "llm_models",
            "integrations",
        ]

class ConfigureAppIntegrationSerializer(serializers.Serializer):
    integration = serializers.SlugRelatedField(slug_field='uuid', queryset=Integration.objects.none())

    type = serializers.CharField()
    branch_name = serializers.CharField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user:
            self.fields['integration'].queryset = Integration.objects.filter(owner=user)

    def validate(self, attrs):
        integration = attrs['integration']
        app = self.context.get("application")
        branch_name = attrs.get("branch_name")

        if integration.owner != app.owner:
            raise serializers.ValidationError("Integration and application owner mismatch.")

        if integration.type != attrs["type"]:
            raise serializers.ValidationError(
                f"Integration type '{integration.type}' does not match '{attrs['type']}'"
            )

        if integration.type == "pms" and integration.provider.lower() == "github":
            if not branch_name:
                raise serializers.ValidationError("Branch is required for GitHub PMS integrations.")

        return attrs

    def validate_integration(self, value):
        app = self.context.get('application')
        if value.owner != app.owner:
            raise serializers.ValidationError("Integration and application owner mismatch.")
        return value