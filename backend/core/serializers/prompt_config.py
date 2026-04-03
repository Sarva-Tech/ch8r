from rest_framework import serializers
from core.models.application import TONE_CHOICES, RESPONSE_STYLE_CHOICES


class PromptConfigSerializer(serializers.Serializer):
    tone = serializers.ChoiceField(choices=TONE_CHOICES)
    response_style = serializers.ChoiceField(choices=RESPONSE_STYLE_CHOICES)
    custom_instructions = serializers.CharField(
        max_length=1000,
        allow_blank=True,
        required=False,
        default=""
    )
    role = serializers.CharField(max_length=200, allow_blank=False, required=False, default="customer service assistant")
    behavior = serializers.CharField(max_length=500, allow_blank=False, required=False, default="answer user questions politely and competently")
