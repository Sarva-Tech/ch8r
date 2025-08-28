from rest_framework import serializers
from core.models import LLMModel

class LLMModelViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMModel
        fields = [
            "id",
            "uuid",
            "name",
            "base_url",
            "model_name",
            "model_type",
            "is_default",
            "created_at",
            "owner"
        ]

class LLMModelCreateSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = LLMModel
        fields = [
            "name",
            "api_key",
            "base_url",
            "model_name",
            "model_type",
        ]

    def create(self, validated_data):
        api_key = validated_data.pop("api_key", None)

        instance = LLMModel(**validated_data)

        if api_key:
            instance.config = api_key
        instance.save()

        return instance

    def update(self, instance, validated_data):
        api_key = validated_data.pop("api_key", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if api_key is not None:
            instance.config = api_key
        instance.save()

        return instance