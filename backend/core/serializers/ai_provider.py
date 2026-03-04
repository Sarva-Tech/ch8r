from rest_framework import serializers
from core.models.ai_provider import AIProvider
from core.consts import SUPPORTED_AI_PROVIDERS

class AIProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIProvider
        exclude = ['provider_api_key']

class AIProviderCreateSerializer(serializers.ModelSerializer):
    base_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    name = serializers.CharField(max_length=500, required=True, allow_blank=False)

    class Meta:
        model = AIProvider
        fields = [
            'uuid', 'name', 'provider', 'provider_api_key',
            'base_url', 'creator'
        ]
        read_only_fields = ['uuid', 'creator']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['provider_api_key'].required = False
            self.fields['provider_api_key'].allow_blank = True
            self.fields.pop('provider', None)

    def validate_provider(self, value):
        supported_provider_ids = [p['id'] for p in SUPPORTED_AI_PROVIDERS]
        if value not in supported_provider_ids:
            supported_labels = [p['label'] for p in SUPPORTED_AI_PROVIDERS]
            raise serializers.ValidationError(
                f"Provider '{value}' is not supported. Supported providers are: {', '.join(supported_labels)}"
            )
        return value

    def validate(self, attrs):
        provider = attrs.get('provider')
        base_url = attrs.get('base_url', '')
        
        if provider == 'custom' and not base_url.strip():
            raise serializers.ValidationError({
                'base_url': 'Custom provider requires base_url'
            })
        
        return attrs

    def create(self, validated_data):
        main_fields = ['name', 'provider', 'provider_api_key']
        
        metadata = {}
        for field, value in validated_data.items():
            if field not in main_fields:
                metadata[field] = str(value).strip() if value is not None else ''
        
        for field in list(validated_data.keys()):
            if field not in main_fields:
                validated_data.pop(field)
        
        validated_data['metadata'] = metadata
        validated_data['creator'] = self.context['request'].user
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        api_key = validated_data.pop('provider_api_key', None)
        if api_key and isinstance(api_key, str) and api_key.strip():
            instance.provider_api_key = api_key

        main_fields = ['name', 'provider']
        
        new_metadata = {}
        for field, value in validated_data.items():
            if field not in main_fields:
                new_metadata[field] = str(value).strip() if value is not None else ''
        
        for field in list(validated_data.keys()):
            if field not in main_fields:
                validated_data.pop(field)
        
        existing_metadata = instance.metadata or {}
        for field, value in new_metadata.items():
            existing_metadata[field] = value
        validated_data['metadata'] = existing_metadata

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
