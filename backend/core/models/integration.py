import uuid

from django.contrib.auth.models import User
from django.db import (models)

class Integration(models.Model):
    TYPE_CHOICES = [
        ("pms", "Project Management System"),
        ("crm", "Customer Relationship Management"),
        ("custom", "Custom Integration"),
    ]

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    provider = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='integrations')

    _config = models.TextField(db_column="config")
    metadata = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("type", "provider")

    def __str__(self):
        return f"{self.name} ({self.provider})"

    @property
    def config(self):
        from core.services.encryption import decrypt
        return decrypt(self._config)

    @config.setter
    def config(self, value):
        from core.services.encryption import encrypt
        self._config = encrypt(value or {})
