from django.contrib.auth.models import User
from django.db import models

from .ai_provider import AIProvider
from .base_model import BaseModel


class AIProviderModels(BaseModel):
    ai_provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE, related_name='models')
    models_data = models.JSONField(blank=True, null=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['created_at']
        unique_together = ['ai_provider']