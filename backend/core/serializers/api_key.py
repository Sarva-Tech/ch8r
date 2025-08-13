from rest_framework import serializers
from core.models import ApplicationAPIKey, Application
from django.shortcuts import get_object_or_404
from uuid import UUID
import secrets

class APIKeySerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=ApplicationAPIKey.PERMISSION_CHOICES),
        required=True
    )

    class Meta:
        model = ApplicationAPIKey
        fields = ['name', 'permissions', 'id', 'created']
        read_only_fields = ['api_key', 'created', 'id']

    def generate_api_key(self):
        return secrets.token_urlsafe(32)

    def create(self, validated_data, *args, **kwargs):
        request = self.context.get('request')
        api_key_raw = self.generate_api_key()
        application_uuid = request.resolver_match.kwargs.get('application_uuid')

        try:
            application = get_object_or_404(Application, uuid=application_uuid)
        except ValueError:
            raise serializers.ValidationError("Invalid application.")

        name = validated_data['name']
        permissions = validated_data['permissions']

        api_key_instance = ApplicationAPIKey(
            application=application,
            name=name,
            permissions=permissions,
            owner=request.user
        )

        api_key_instance.set_api_key(api_key_raw)
        api_key_instance.save()

        return api_key_instance, api_key_raw
