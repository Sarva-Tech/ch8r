from django.db import (models)
from django.utils import timezone
from core.models import Application
import bcrypt

class ApplicationAPIKey(models.Model):
    READ = 'read'
    WRITE = 'write'
    DELETE = 'delete'

    PERMISSION_CHOICES = [
        (READ, 'Read'),
        (WRITE, 'Write'),
        (DELETE, 'Delete'),
    ]

    application = models.ForeignKey(Application, related_name="api_keys", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    hashed_api_key = models.CharField(max_length=255)
    permissions = models.JSONField(default=list)
    created = models.DateTimeField(default=timezone.now)

    def set_api_key(self, raw_api_key):
        self.hashed_api_key = bcrypt.hashpw(raw_api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_api_key(self, raw_api_key):
        return bcrypt.checkpw(raw_api_key.encode('utf-8'), self.hashed_api_key.encode('utf-8'))

    def has_permission(self, permission):
        return permission in self.permissions

    def save(self, *args, **kwargs):
        if not self.hashed_api_key:
            self.set_api_key(self.api_key)
            self.api_key = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.application.name}"