from django.db import models

from core.models import Application
from core.models.api_token import APIToken

class ApplicationPermission(models.Model):
    api_token = models.ForeignKey(APIToken, on_delete=models.CASCADE, related_name="app_permissions")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="token_permissions")
    permissions = models.JSONField(default=dict)

    class Meta:
        unique_together = ("api_token", "application")

    def has_permission(self, action):
        if self.permissions.get("all", False):
            return True
        return self.permissions.get(action, False)
