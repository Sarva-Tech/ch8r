from rest_framework import serializers

from core.models import LLMModel
from core.models.application import Application
from core.serializers.knowledge_base import KnowledgeBaseViewSerializer
from core.serializers.user import UserViewSerializer

class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['name']

class ApplicationViewSerializer(serializers.ModelSerializer):
    owner = UserViewSerializer(read_only=True)
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)

    llm_models = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ['id', 'uuid', 'name', 'owner_id', 'owner', 'llm_models']

    def get_llm_models(self, obj):
        llm_models = LLMModel.objects.filter(application_configs__application=obj).distinct()
        return [
            {
                "id": m.id,
                "uuid": m.uuid,
                "name": m.name,
                "model_name": m.model_name,
                "model_type": m.model_type,
                "is_default": m.is_default
            }
            for m in llm_models
        ]
