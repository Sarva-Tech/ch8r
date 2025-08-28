import uuid

from django.contrib.auth.models import User
from django.db import models

class LLMModel(models.Model):
    class ModelType(models.TextChoices):
        TEXT = "text", "Text"
        EMBEDDING = "embedding", "Embedding"
        IMAGE = "image", "Image"
        RERANK = "rerank", "Re-Ranking"
        OTHER = "other", "Other"

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='models')

    name = models.CharField(max_length=255, unique=True)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    base_url = models.URLField(max_length=500, blank=True, null=True)
    model_name = models.CharField(max_length=255)

    model_type = models.CharField(max_length=50, choices=ModelType.choices)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.model_type})"

    @property
    def config(self):
        from core.services.encryption import decrypt_dict
        return decrypt_dict(self.api_key)

    @config.setter
    def config(self, value):
        from core.services.encryption import encrypt
        self.api_key = encrypt(value or "")

