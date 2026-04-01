import uuid
from django.db import models


class ChatRoom(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='chatrooms')
    ai_provider = models.ForeignKey('AIProvider', on_delete=models.SET_NULL, null=True, blank=True)
    model = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalation_cooldown_hours = models.IntegerField(default=24)

    def __str__(self):
        return self.name
