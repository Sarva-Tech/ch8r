from django.db import models


class AppModel(models.Model):
    id = models.AutoField(primary_key=True)
    application = models.ForeignKey(
        "Application",
        on_delete=models.CASCADE,
        related_name="model_configs"
    )
    llm_model = models.ForeignKey(
        "LLMModel",
        on_delete=models.CASCADE,
        related_name="application_configs"
    )

    def __str__(self):
        return f"{self.application.name} - {self.llm_model.name}"

    @classmethod
    def configure_defaults(cls, application):
        from core.models import LLMModel

        defaults = {
            LLMModel.ModelType.TEXT: LLMModel.get_default_by_type(LLMModel.ModelType.TEXT),
            LLMModel.ModelType.EMBEDDING: LLMModel.get_default_by_type(LLMModel.ModelType.EMBEDDING),
        }

        app_models = {}
        for model_type, llm_model in defaults.items():
            if llm_model:
                app_model, created = cls.objects.get_or_create(
                    application=application,
                    llm_model=llm_model
                )
                app_models[model_type] = app_model
            else:
                app_models[model_type] = None

        return app_models