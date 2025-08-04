import uuid
from django.db import models
from core.models.application import Application
from core.models.notification_profiles import NotificationProfile

class AppNotificationProfile(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="app_notification_profiles"
    )
    notification_profile = models.ForeignKey(
        NotificationProfile,
        on_delete=models.CASCADE,
        related_name="app_notification_profiles"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('application', 'notification_profile')

    def __str__(self):
        return f"{self.application.name} - {self.notification_profile.type}"
