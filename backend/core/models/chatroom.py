import uuid
from django.db import models


class ChatRoom(models.Model):
    MODE_CHOICES = [('ai', 'AI Mode'), ('direct', 'Direct Mode')]

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='chatrooms')
    ai_provider = models.ForeignKey('AIProvider', on_delete=models.SET_NULL, null=True, blank=True)
    model = models.CharField(max_length=255, null=True, blank=True)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='ai', db_column='chat_mode')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
