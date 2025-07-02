from rest_framework import serializers

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

    class Meta:
        model = Application
        fields = ['id', 'uuid', 'name', 'owner_id', 'owner']