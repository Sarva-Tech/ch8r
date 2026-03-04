from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import models
from core.serializers.ai_provider import AIProviderCreateSerializer, AIProviderSerializer
from core.models import AIProvider
from core.consts import SUPPORTED_AI_PROVIDERS

class AIProviderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'uuid'
    http_method_names = ['get', 'post', 'put','patch', 'delete']
    pagination_class = PageNumberPagination

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

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict):
            response.data['supported_ai_providers'] = SUPPORTED_AI_PROVIDERS
        else:
            response.data = {
                'results': response.data,
                'supported_ai_providers': SUPPORTED_AI_PROVIDERS
            }
        return response
