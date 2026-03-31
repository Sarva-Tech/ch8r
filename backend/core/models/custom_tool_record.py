import uuid
from django.core.exceptions import ValidationError
from django.db import models


class CustomToolRecord(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    app_integration = models.ForeignKey(
        "AppIntegration", on_delete=models.CASCADE, related_name="custom_tools"
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    url_schema = models.TextField()
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}
        if not self.title or not self.title.strip():
            errors["title"] = "Title must not be blank."
        if not self.description or not self.description.strip():
            errors["description"] = "Description must not be blank."
        if not self.url_schema or not self.url_schema.strip():
            errors["url_schema"] = "URL schema must not be blank."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title
