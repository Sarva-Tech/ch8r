from django.db.models import Q
from rest_framework import serializers

from core.models import AppModel, LLMModel
from core.serializers.llm_model import LLMModelViewSerializer


class AppModelCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppModel
        fields = ["application", "llm_model"]

class AppModelViewSerializer(serializers.ModelSerializer):
    llm_model = LLMModelViewSerializer()

    class Meta:
        model = AppModel
        fields = ["id", "llm_model"]

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
        if value.owner != app.owner:
            raise serializers.ValidationError("Model and application owner mismatch.")
        return value
