import uuid

from django.db import models


class ChatroomClientProfile(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    chatroom = models.OneToOneField(
        'ChatRoom',
        on_delete=models.CASCADE,
        related_name='client_profile',
    )
    sender_identifier = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    region = models.CharField(max_length=128, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)
    browser = models.CharField(max_length=128, blank=True, null=True)
    domain = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.CharField(max_length=64, blank=True, null=True)
    timezone = models.CharField(max_length=128, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Client profile for chatroom {self.chatroom.uuid}"
