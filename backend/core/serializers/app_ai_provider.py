from rest_framework import serializers
from core.models.app_ai_provider import AppAIProvider
from core.models.ai_provider import AIProvider
from .ai_provider import AIProviderSerializer

class AppAIProviderSerializer(serializers.ModelSerializer):
    ai_provider = AIProviderSerializer(read_only=True)

    class Meta:
        model = AppAIProvider
        fields = [
            'id', 'uuid', 'ai_provider', 'context', 'capability',
            'priority', 'external_model_id', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uuid', 'priority', 'created_at', 'updated_at']


class AppAIProviderCreateSerializer(serializers.ModelSerializer):
    ai_provider_id = serializers.IntegerField(write_only=True)
    context = serializers.CharField()
    capability = serializers.CharField()
    external_model_id = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = AppAIProvider
        fields = ['ai_provider_id', 'context', 'capability', 'external_model_id']

    def to_representation(self, instance):
        return AppAIProviderSerializer(instance, context=self.context).data

    def validate_ai_provider_id(self, value):
        try:
            ai_provider = AIProvider.objects.get(id=value)
            if ai_provider.creator != self.context['request'].user and not ai_provider.is_builtin:
                raise serializers.ValidationError("You don't own this AI provider")
            return value
        except AIProvider.DoesNotExist:
            raise serializers.ValidationError("AI provider not found")

    def validate(self, data):
        return data

    def create(self, validated_data):
        ai_provider_id = validated_data.pop('ai_provider_id')
        ai_provider = AIProvider.objects.get(id=ai_provider_id)
        application = self.context['application']

        existing_configs = AppAIProvider.objects.filter(
            application=application,
            context=validated_data['context'],
            capability=validated_data['capability']
        ).order_by('-updated_at')

        if existing_configs.exists():
            config_to_keep = existing_configs.first()
            configs_to_delete = existing_configs[1:]

            if configs_to_delete:
                for config in configs_to_delete:
                    config.delete()

            config_to_keep.external_model_id = validated_data.get('external_model_id')
            config_to_keep.ai_provider = ai_provider
            config_to_keep.save()
            return config_to_keep

        return AppAIProvider.objects.create(
            application=application,
            ai_provider=ai_provider,
            **validated_data
        )

class AppAIProviderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppAIProvider
        fields = ['external_model_id']

    def to_representation(self, instance):
        return AppAIProviderSerializer(instance, context=self.context).data
