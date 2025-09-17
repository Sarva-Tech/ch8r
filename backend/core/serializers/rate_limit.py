from rest_framework import serializers
from core.models import Application

class ApplicationRateLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["uuid", "custom_model_rate_limit_per_minute"]
