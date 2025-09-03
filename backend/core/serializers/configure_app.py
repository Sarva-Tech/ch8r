from django.db.models import Q
from rest_framework import serializers

from core.models import LLMModel, AppModel, Integration, AppIntegration


class ConfigureAppModelSerializer(serializers.ModelSerializer):
    llm_model = serializers.SlugRelatedField(slug_field='uuid', queryset=LLMModel.objects.none())

    class Meta:
        model = AppModel
        fields = ['llm_model']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user:
            self.fields['llm_model'].queryset = LLMModel.objects.filter(
                Q(owner=user) | Q(is_default=True)
            )
        else:
            self.fields['llm_model'].queryset = LLMModel.objects.none()

    def validate(self, attrs):
        llm_model = attrs['llm_model']
        request_model_type = self.initial_data.get('model_type')

        if llm_model.model_type != request_model_type:
            raise serializers.ValidationError(
                f"LLM model type '{llm_model.model_type}' does not match the type '{request_model_type}'"
            )

        return attrs

    def validate_llm_model(self, value):
        app = self.context.get('application')
        if not value.is_default and value.owner != app.owner:
            raise serializers.ValidationError("Model and application owner mismatch.")
        return value

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
