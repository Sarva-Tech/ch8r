from django.db.models import Q
from rest_framework import serializers

from core.models.app_model import AppModel
from core.models.llm_model import LLMModel


class AppModelViewSerializer(serializers.ModelSerializer):
    from core.serializers import LLMModelViewSerializer

    llm_model = LLMModelViewSerializer(read_only=True)

    class Meta:
        model = AppModel
        fields = ["id", "llm_model"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data["llm_model"]


class ConfigureAppModelSerializer(serializers.Serializer):
    model_type = serializers.CharField()
    llm_model = serializers.SlugRelatedField(
        slug_field="uuid", queryset=LLMModel.objects.none()
    )

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user:
            fields['llm_model'].queryset = LLMModel.objects.filter(
                Q(owner=user) | Q(is_default=True)
            )
        else:
            fields['llm_model'].queryset = LLMModel.objects.none()
        return fields

    def validate(self, attrs):
        llm_model = attrs["llm_model"]
        request_model_type = attrs["model_type"]
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



class ConfigureAppModelsSerializer(serializers.Serializer):
    models = ConfigureAppModelSerializer(many=True)