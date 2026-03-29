from django.contrib.auth.models import User
from django.db import models

from core.fields import EncryptedCharField

from .base_model import BaseModel


class Integration(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    provider = models.CharField(max_length=255)
    credentials = EncryptedCharField(max_length=2000)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} ({self.provider})"
