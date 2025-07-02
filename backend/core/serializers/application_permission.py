from rest_framework import serializers

from core.models import Application, ApplicationPermission


class ApplicationPermissionSerializer(serializers.ModelSerializer):
    application = serializers.SlugRelatedField(slug_field='id', queryset=Application.objects.all())
    permissions = serializers.JSONField()

    class Meta:
        model = ApplicationPermission
        fields = ['id', 'application', 'permissions']

    def validate_permissions(self, value):
        allowed_keys = {"read", "write", "delete", "all"}
        if not isinstance(value, dict):
            raise serializers.ValidationError("Permissions must be a JSON object.")
        for key in value.keys():
            if key not in allowed_keys:
                raise serializers.ValidationError(f"Invalid permission: {key}")
            if not isinstance(value[key], bool):
                raise serializers.ValidationError(f"Permission '{key}' must be true or false.")
        return value
