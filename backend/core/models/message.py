import uuid
from django.db import (models)

class Message(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    chatroom = models.ForeignKey('ChatRoom', on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    sender_identifier = models.CharField(max_length=255)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.uuid} in ChatRoom {self.chatroom.name}"
