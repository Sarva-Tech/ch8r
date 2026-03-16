from rest_framework import serializers
from core.models import NotificationProfile
from core.consts import SUPPORTED_NOTIFICATION_PROVIDERS

PROVIDER_MAP = {p['id']: p for p in SUPPORTED_NOTIFICATION_PROVIDERS}


def validate_config_for_type(provider_type, config):
    if not isinstance(config, dict):
        raise serializers.ValidationError({'config': 'Must be a JSON object.'})

    provider = PROVIDER_MAP.get(provider_type)
    if not provider:
        raise serializers.ValidationError({'type': f'Unsupported provider: {provider_type}'})

    missing = [f for f in provider.get('required_fields', []) if not config.get(f)]
    if missing:
        raise serializers.ValidationError(
            {'config': f"Missing required fields: {', '.join(missing)}"}
        )

    if provider_type == 'email':
        email = config.get('email', '').strip()
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise serializers.ValidationError({'config': {'email': 'Enter a valid email address.'}})

    if provider_type in ('slack', 'discord'):
        url = config.get('webhookUrl', '').strip()
        if not url.startswith(('http://', 'https://')):
            raise serializers.ValidationError(
                {'config': {'webhookUrl': 'Must be a valid http/https URL.'}}
            )
        if provider_type == 'slack' and 'hooks.slack.com' not in url:
            raise serializers.ValidationError(
                {'config': {'webhookUrl': "Slack webhooks must contain 'hooks.slack.com'."}}
            )
        if provider_type == 'discord' and 'discord.com' not in url:
            raise serializers.ValidationError(
                {'config': {'webhookUrl': "Discord webhooks must contain 'discord.com'."}}
            )


class NotificationProfileSerializer(serializers.ModelSerializer):
    # Write-only: accepts config on create/update but never echoes it back
    config = serializers.JSONField(write_only=True)
    # Read-only: safe representation with no sensitive values
    config_meta = serializers.SerializerMethodField()

    class Meta:
        model = NotificationProfile
        fields = ['uuid', 'name', 'type', 'config', 'config_meta', 'is_enabled', 'owner', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'owner', 'created_at', 'updated_at']

    def get_config_meta(self, obj):
        config = obj.config or {}
        safe = {}
        if 'email' in config:
            safe['hasEmail'] = bool(config.get('email'))
        if 'webhookUrl' in config:
            safe['hasWebhookUrl'] = bool(config.get('webhookUrl'))
        return safe

    def validate(self, attrs):
        provider_type = attrs.get('type', getattr(self.instance, 'type', None))
        config = attrs.get('config', getattr(self.instance, 'config', None))

        if provider_type and config is not None:
            validate_config_for_type(provider_type, config)

        return attrs

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)
