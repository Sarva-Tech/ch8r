from django.db import models

from .base_model import BaseModel


class ContentQualityScore(BaseModel):
    content_type = models.CharField(max_length=20)
    quality_factors = models.JSONField()
    min_score = models.FloatField(default=0.3)
    
    class Meta:
        ordering = ['content_type']
    
    def __str__(self):
        return f"{self.content_type} - min_score: {self.min_score}"
