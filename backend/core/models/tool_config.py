import uuid
from django.db import models


class ToolConfig(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    app_integration = models.ForeignKey(
        "AppIntegration", on_delete=models.CASCADE, related_name="tool_configs"
    )
    tool_id = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)
    is_builtin = models.BooleanField(default=True)

    title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    url_schema = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("app_integration", "tool_id")]

    def __str__(self):
        return f"{self.tool_id} ({'enabled' if self.is_enabled else 'disabled'})"
