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
    _config = models.TextField(db_column="config")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.type.capitalize()} Notification Profile ({self.uuid})"

    @property
    def config(self):
        from core.services.encryption import decrypt_dict
        return decrypt_dict(self._config)

    @config.setter
    def config(self, value):
        from core.services.encryption import encrypt_dict
        self._config = encrypt_dict(value or {})

