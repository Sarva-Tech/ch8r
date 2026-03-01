from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from django.db import models
from core.serializers.ai_provider import AIProviderCreateSerializer, AIProviderSerializer
from core.models import AIProvider

class AIProviderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'uuid'
    http_method_names = ['get', 'post', 'put','patch', 'delete']

    queryset = AIProvider.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AIProviderCreateSerializer
        return AIProviderSerializer

    def get_queryset(self):
        user = self.request.user
        return AIProvider.objects.filter(
            models.Q(creator=user) | models.Q(is_builtin=True)
        )

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)