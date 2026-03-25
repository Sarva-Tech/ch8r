import uuid
from django.db import models
from django.contrib.auth.models import User

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
    _config = models.TextField(db_column="config")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_profiles')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.type.capitalize()} Notification Profile ({self.uuid})"

    @property
    def config(self):
        from core.services.encryption import decrypt
        return decrypt(self._config)

    @config.setter
    def config(self, value):
        from core.services.encryption import encrypt
        self._config = encrypt(value or {})

