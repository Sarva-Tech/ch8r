from rest_framework import serializers
from core.models.ai_provider import AIProvider

class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = ['id', 'uuid', 'name', 'provider', 'base_url', 'is_builtin', 'creator', 'created_at', 'updated_at']

class AIProviderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = ['name', 'provider', 'base_url', 'provider_api_key', 'creator']
        read_only_fields = ['creator']

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)

class AIProviderUpdateSerializer(serializers.ModelSerializer):
    provider_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = AIProvider
        fields = ['name', 'base_url', 'provider_api_key']
        read_only_fields = ['creator']

    def update(self, instance, validated_data):
        api_key = validated_data.pop('provider_api_key', None)
        if api_key:
            instance.provider_api_key = api_key

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
