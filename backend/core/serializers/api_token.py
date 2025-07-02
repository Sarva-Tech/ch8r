from rest_framework import serializers

from core.models import APIToken
from core.serializers.application_permission import ApplicationPermissionSerializer


class APITokenSerializer(serializers.ModelSerializer):
    app_permissions = ApplicationPermissionSerializer(many=True, read_only=True)

    class Meta:
        model = APIToken
        fields = ['id', 'name', 'key', 'is_active', 'is_root', 'created_at', 'app_permissions']
        read_only_fields = ['key', 'created_at']
