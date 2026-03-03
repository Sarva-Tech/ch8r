import uuid
from django.db import models


class AppAIProvider(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    application = models.ForeignKey(
        "Application",
        on_delete=models.CASCADE,
        related_name="ai_provider_configs"
    )
    ai_provider = models.ForeignKey(
        "AIProvider",
        on_delete=models.CASCADE,
        related_name="application_configs"
    )

    context = models.CharField(max_length=50)
    capability = models.CharField(max_length=50, default='text')
    priority = models.PositiveIntegerField(default=100)
    external_model_id = models.CharField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['context', 'capability', 'priority']

    def __str__(self):
        return f"{self.application.name} - {self.ai_provider.name} ({self.context}:{self.capability})"

    def save(self, *args, **kwargs):
        if not self.priority or self.priority == 100:
            existing_configs = AppAIProvider.objects.filter(
                application=self.application,
                context=self.context,
                capability=self.capability
            ).exclude(id=self.id).order_by('-priority')

            if existing_configs.exists():
                self.priority = existing_configs.first().priority + 100
            else:
                self.priority = 100

        super().save(*args, **kwargs)
