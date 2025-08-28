from django.db import models

from core.models import LLMModel


class AppModel(models.Model):
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(
        "Application",
        on_delete=models.CASCADE,
        related_name="model_configs"
    )
    llm_model = models.ForeignKey(
        LLMModel,
        on_delete=models.CASCADE,
        related_name="application_bindings"
    )

    def __str__(self):
        return f"{self.application.name} - {self.llm_model.name}"
