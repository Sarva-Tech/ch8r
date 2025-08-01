import uuid

from django.contrib.auth.models import User
from django.db import (models)

class Integration(models.Model):
    CATEGORY_CHOICES = [
        ("project_management", "Project Management"),
        ("crm", "CRM"),
        ("other", "Other")
    ]

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    application = models.ForeignKey("Application", on_delete=models.CASCADE, related_name="integrations")
    provider = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    config = models.JSONField()
    metadata = models.JSONField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)