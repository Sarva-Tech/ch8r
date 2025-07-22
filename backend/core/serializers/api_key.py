from rest_framework import serializers
from core.models import ApplicationAPIKey, Application
import secrets

class APIKeySerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(queryset=Application.objects.all())
    name = serializers.CharField(max_length=255)
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=ApplicationAPIKey.PERMISSION_CHOICES),
        required=True
    )

    class Meta:
        model = ApplicationAPIKey
        fields = ['name', 'application', 'permissions']
        read_only_fields = ['api_key', 'created']

    def generate_api_key(self):
        return secrets.token_urlsafe(32)

    def create(self, validated_data):
        api_key_raw = self.generate_api_key()

        print(api_key_raw)
        application = validated_data['application']
        name = validated_data['name']
        permissions = validated_data['permissions']

        api_key_instance = ApplicationAPIKey(
            application=application,
            name=name,
            permissions=permissions
        )

        api_key_instance.set_api_key(api_key_raw)
        api_key_instance.save()

        return api_key_instance, api_key_raw
