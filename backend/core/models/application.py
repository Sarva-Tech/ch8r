import uuid
from django.db import (models)
from django.contrib.auth.models import User

class Application(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
