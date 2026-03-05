from rest_framework import serializers
from core.models.ai_provider import AIProvider
from core.consts import SUPPORTED_AI_PROVIDERS
from core.utils import extract_and_merge_fields

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
        provider = attrs.get('provider') or (self.instance.provider if self.instance else None)
        base_url = attrs.get('base_url')
        
        if self.instance is None and provider == 'custom':
            if base_url is None or not base_url.strip():
                raise serializers.ValidationError({
                    'base_url': 'Custom provider requires base url'
                })

        if self.instance is not None and base_url is not None and provider == 'custom' and not base_url.strip():
            raise serializers.ValidationError({
                'base_url': 'Custom provider requires base url'
            })
        
        return attrs

    def create(self, validated_data):
        metadata = extract_and_merge_fields(validated_data, ['name', 'provider', 'provider_api_key'])
        validated_data['metadata'] = metadata
        validated_data['creator'] = self.context['request'].user
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        api_key = validated_data.pop('provider_api_key', None)
        if api_key and isinstance(api_key, str) and api_key.strip():
            instance.provider_api_key = api_key

        metadata = extract_and_merge_fields(validated_data, ['name', 'provider'], instance.metadata or {})
        validated_data['metadata'] = metadata

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
