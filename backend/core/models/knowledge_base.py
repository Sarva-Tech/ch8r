import uuid
from django.db import (models)

class KnowledgeBase(models.Model):
    SOURCE_CHOICES = [
        ('youtube', 'YouTube'),
        ('url', 'URL'),
        ('file', 'File'),
        ('text', 'Text')
    ]

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='knowledge_bases')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='file')
    path = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"KnowledgeBase {self.uuid} for Application {self.application_id}"
