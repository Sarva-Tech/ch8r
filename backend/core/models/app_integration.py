from django.db import models
from core.models import Application, Integration

class AppIntegration(models.Model):
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="app_integrations"
    )
    integration = models.ForeignKey(
        Integration, on_delete=models.CASCADE, related_name="app_integrations"
    )
    metadata = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("application", "integration")

    def __str__(self):
        return f"{self.application.name} → {self.integration.name}"
