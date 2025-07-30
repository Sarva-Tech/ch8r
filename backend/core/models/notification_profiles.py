import uuid
from django.db import models

class NotificationProfile(models.Model):
    TYPE_CHOICES = [
        ('email', 'Email'),
        ('slack', 'Slack'),
        ('discord', 'Discord'),
        ('whatsapp', 'WhatsApp'),
    ]

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    config = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.type.capitalize()} Notification Profile ({self.uuid})"
