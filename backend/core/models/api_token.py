from django.db import models
from django.contrib.auth.models import User
import uuid, secrets

class APIToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_tokens")
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    is_active = models.BooleanField(default=True)
    is_root = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
