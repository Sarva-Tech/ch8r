import uuid
from django.db import (models)
from django.contrib.auth.models import User
from django.db.models import Q

TONE_CHOICES = ["professional", "friendly", "formal", "casual"]
RESPONSE_STYLE_CHOICES = ["balanced", "concise", "detailed", "step_by_step"]
PROMPT_CONFIG_DEFAULTS = {
    "tone": "professional",
    "response_style": "balanced",
    "custom_instructions": "",
    "role": "customer service assistant",
    "behavior": "answer user questions politely and competently",
}


class Application(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    name = models.CharField(max_length=255)
    prompt_config = models.JSONField(default=dict)

    def __str__(self):
        return self.name

    def get_prompt_config(self) -> dict:
        """Returns PROMPT_CONFIG_DEFAULTS merged with stored prompt_config values."""
        return {**PROMPT_CONFIG_DEFAULTS, **(self.prompt_config or {})}
