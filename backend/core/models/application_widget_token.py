import secrets

from django.db import models

from core.models import Application


class ApplicationWidgetToken(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='widget_tokens')
    key = models.CharField(max_length=128, unique=True, default=secrets.token_urlsafe)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    label = models.CharField(max_length=100, blank=True, null=True)
