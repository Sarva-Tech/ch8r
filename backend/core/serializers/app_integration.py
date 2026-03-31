from rest_framework import serializers

from core.models import Integration, AppIntegration
from core.models.tool_config import ToolConfig
from core.serializers.integration import IntegrationSerializer
from core.consts import SUPPORTED_INTEGRATIONS
from core.integrations.registry import INTEGRATION_TOOLS

class AppIntegrationSerializer(serializers.ModelSerializer):
    integration = IntegrationSerializer(read_only=True)

    class Meta:
        model = AppIntegration
        fields = ['uuid', 'integration', 'integration_type', 'metadata', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'integration', 'integration_type', 'metadata', 'is_active', 'created_at', 'updated_at']


AppIntegrationViewSerializer = AppIntegrationSerializer


class AppIntegrationCreateSerializer(serializers.ModelSerializer):
    integration_uuid = serializers.UUIDField(write_only=True)
    integration_type = serializers.CharField()
    metadata = serializers.JSONField(required=False)
    tools = serializers.DictField(child=serializers.DictField(), required=False, write_only=True)
    custom_tools = serializers.ListField(child=serializers.DictField(), required=False, write_only=True)

    class Meta:
        model = AppIntegration
        fields = ['integration_uuid', 'integration_type', 'metadata', 'tools', 'custom_tools']

    def to_representation(self, instance):
        return AppIntegrationSerializer(instance, context=self.context).data

    def validate_integration_uuid(self, value):
        try:
            integration = Integration.objects.get(uuid=value)
        except Integration.DoesNotExist:
            raise serializers.ValidationError("Integration not found")

        request = self.context['request']
        if integration.creator != request.user:
            raise serializers.ValidationError("You don't own this integration")

        self._integration = integration
        return value

    def validate(self, data):
        integration = self._integration
        provider = integration.provider
        entry = next((e for e in SUPPORTED_INTEGRATIONS if e['id'] == provider), None)

        if entry is None or data['integration_type'] not in entry['supported_types']:
            raise serializers.ValidationError(
                {"integration_type": f"Integration type '{data['integration_type']}' is not supported for provider '{provider}'"}
            )

        return data

    def create(self, validated_data):
        validated_data.pop('integration_uuid')
        integration = self._integration
        integration_type = validated_data.pop('integration_type')
        metadata = validated_data.pop('metadata', None)
        tools_data = validated_data.pop('tools', {})
        custom_tools_data = validated_data.pop('custom_tools', [])
        application = self.context['application']

        instance, _ = AppIntegration.objects.update_or_create(
            application=application,
            integration_type=integration_type,
            defaults={
                'integration': integration,
                'metadata': metadata,
                'is_active': True,
            }
        )

        if tools_data:
            integration_key = f"{integration.provider}_{integration_type}"
            valid_tools = INTEGRATION_TOOLS.get(integration_key, {})
            for tool_id, tool_state in tools_data.items():
                tool_name = tool_id.split(":", 1)[-1] if ":" in tool_id else tool_id
                if tool_name not in valid_tools:
                    continue
                scoped_tool_id = f"{integration_key}:{tool_name}"
                is_enabled = bool(tool_state.get("is_enabled", True))
                ToolConfig.objects.update_or_create(
                    app_integration=instance,
                    tool_id=scoped_tool_id,
                    defaults={"is_enabled": is_enabled},
                )

        if custom_tools_data:
            import uuid as uuid_lib
            for ct in custom_tools_data:
                ct_uuid = ct.get('uuid')
                is_enabled = bool(ct.get('is_enabled', True))
                if ct_uuid:
                    ToolConfig.objects.filter(
                        app_integration=instance,
                        uuid=ct_uuid,
                        is_builtin=False,
                    ).update(is_enabled=is_enabled)

        return instance
