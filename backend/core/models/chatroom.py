import uuid
from django.db import models


class ChatRoom(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='chatrooms')

    def __str__(self):
        return self.name
