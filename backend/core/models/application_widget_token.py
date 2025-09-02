import secrets

from django.db import models

from core.models import Application

def generate_key():
    return "widget_" + secrets.token_urlsafe(32)


class ApplicationWidgetToken(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='widget_tokens')
    key = models.CharField(max_length=128, unique=True, default=generate_key)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    label = models.CharField(max_length=100, blank=True, null=True)
