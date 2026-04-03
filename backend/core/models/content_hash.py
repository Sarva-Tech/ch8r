import hashlib
from django.db import models
from django.contrib.auth.models import User

from .base_model import BaseModel


class ContentHash(BaseModel):
    app = models.ForeignKey('Application', on_delete=models.CASCADE)
    content_hash = models.CharField(max_length=64)
    content_type = models.CharField(max_length=20)

    class Meta:
        unique_together = ['app', 'content_hash']
        indexes = [models.Index(fields=['app', 'content_hash'])]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.app.name} - {self.content_hash[:8]}... ({self.content_type})"

    @classmethod
    def generate_content_hash(cls, content: str) -> str:
        if not content:
            return hashlib.sha256(b'').hexdigest()

        content_bytes = content.encode('utf-8')
        return hashlib.sha256(content_bytes).hexdigest()
