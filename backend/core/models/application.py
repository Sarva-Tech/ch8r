import uuid
from django.db import (models)
from django.contrib.auth.models import User
from django.db.models import Q


class Application(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    name = models.CharField(max_length=255)
    custom_model_rate_limit_per_minute = models.IntegerField(default=10)

    def __str__(self):
        return self.name

    def get_model_by_type(self, model_type):
        app_model = (
            self.model_configs.filter(
                Q(llm_model__is_default=True) | Q(llm_model__owner=self.owner),
                llm_model__model_type=model_type
            )
            .select_related("llm_model")
            .first()
        )
        return app_model.llm_model if app_model else None
