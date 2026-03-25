from django.contrib.auth.models import User
from django.db import models

from core.fields import EncryptedJSONField
from .base_model import BaseModel


class NotificationProfile(BaseModel):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20)
    config = EncryptedJSONField(default=dict, blank=True)
    is_enabled = models.BooleanField(default=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notification_profiles',
    )

    class Meta:
        ordering = ['name', 'created_at']
        indexes = [
            models.Index(fields=['owner', 'type']),
            models.Index(fields=['owner', 'is_enabled']),
        ]

    def __str__(self):
        return f"{self.name} ({self.type})"
