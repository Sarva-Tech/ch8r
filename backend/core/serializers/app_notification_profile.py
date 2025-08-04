from rest_framework import serializers
from core.models.app_notification_profile import AppNotificationProfile
from core.serializers.notification_profiles import NotificationProfileSerializer

class AppNotificationProfileSerializer(serializers.ModelSerializer):
    notification_profile = NotificationProfileSerializer(read_only=True)
    notification_profile_id = serializers.PrimaryKeyRelatedField(
        source='notification_profile',
        queryset=AppNotificationProfile.notification_profile.field.related_model.objects.all(),
        write_only=True
    )

    class Meta:
        model = AppNotificationProfile
        fields = ['id', 'application', 'notification_profile', 'notification_profile_id', 'created_at']
        read_only_fields = ['id', 'created_at']
