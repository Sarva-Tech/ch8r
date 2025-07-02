import uuid
from django.db import (models)

class ChatroomParticipant(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('ai_agent', 'AI Agent'),
        ('human_agent', 'Human Agent'),
    ]

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    chatroom = models.ForeignKey('ChatRoom', on_delete=models.CASCADE, related_name='participants')
    user_identifier = models.CharField(max_length=255)
    metadata = models.JSONField(blank=True, null=True)
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return f"Participant {self.user_identifier} in ChatRoom {self.chatroom_id}"