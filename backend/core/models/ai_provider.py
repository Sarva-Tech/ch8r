from django.contrib.auth.models import User
from django.db import models

from core.fields import EncryptedCharField

from .base_model import BaseModel

class AIProvider(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    provider = models.CharField(max_length=255)
    provider_api_key = EncryptedCharField(max_length=1000)
    base_url = models.CharField(max_length=100)
    is_builtin = models.BooleanField(default=False, blank=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_at']
