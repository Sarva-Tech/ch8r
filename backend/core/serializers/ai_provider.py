from rest_framework import serializers
from core.models.ai_provider import AIProvider

class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        exclude = ['provider_api_key']

class AIProviderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        fields = ['name', 'provider', 'base_url', 'provider_api_key', 'creator']
        read_only_fields = ['creator']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['provider_api_key'].required = False
            self.fields['provider_api_key'].allow_blank = True
            self.fields.pop('provider', None)

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        api_key = validated_data.pop('provider_api_key', None)
        if api_key and isinstance(api_key, str) and api_key.strip():
            instance.provider_api_key = api_key

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
