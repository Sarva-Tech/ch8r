import hashlib
from django.db import models
from django.contrib.auth.models import User

from .base_model import BaseModel


class ContentHash(BaseModel):
    app = models.ForeignKey('Application', on_delete=models.CASCADE)
    content_hash = models.CharField(max_length=64)
    content_type = models.CharField(max_length=20)
    embedding = models.JSONField(null=True, blank=True, help_text="Cached embedding vector for this content")

    class Meta:
        unique_together = ['app', 'content_hash', 'content_type']
        indexes = [
            models.Index(fields=['app', 'content_hash']),
            models.Index(fields=['app', 'content_type']),
            models.Index(fields=['app', 'content_hash', 'content_type'])
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.app.name} - {self.content_hash[:8]}... ({self.content_type})"

    @classmethod
    def generate_content_hash(cls, content: str) -> str:
        if not content:
            return hashlib.sha256(b'').hexdigest()

        content_bytes = content.encode('utf-8')
        return hashlib.sha256(content_bytes).hexdigest()

    @classmethod
    def clear_embedding_cache(cls, app, content_type: str = None) -> int:
        queryset = cls.objects.filter(app=app)
        if content_type:
            queryset = queryset.filter(content_type=content_type)

        count = queryset.count()
        queryset.update(embedding=None)
        return count

    @classmethod
    def get_cache_stats(cls, app) -> dict:
        total = cls.objects.filter(app=app).count()
        cached = cls.objects.filter(app=app).exclude(embedding__isnull=True).count()

        return {
            'total_entries': total,
            'cached_embeddings': cached,
            'cache_hit_rate': f"{(cached / total * 100):.1f}%" if total > 0 else "0%"
        }
