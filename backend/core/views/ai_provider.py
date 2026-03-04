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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        from core.services.factories.ai_provider_factory import AIProviderFactory
        
        factory = AIProviderFactory()
        try:
            main_fields = ['name', 'provider', 'provider_api_key']
            config = {}
            
            for field, value in validated_data.items():
                if field not in main_fields:
                    if field == 'timeout':
                        config[field] = int(value) if value is not None else None
                    else:
                        config[field] = str(value).strip() if value is not None else ''
            
            is_valid, models = factory.validate_provider(
                provider_type=validated_data['provider'],
                api_key=validated_data['provider_api_key'],
                config=config
            )
            
            if not is_valid:
                return Response(
                    {
                        'error': 'Failed to validate AI provider connection',
                        'details': 'Unable to connect to the AI provider with the provided credentials'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ai_provider = serializer.save()
            
            response_serializer = AIProviderSerializer(ai_provider)
            return Response(
                {
                    'ai_provider': response_serializer.data,
                    'validation': {
                        'is_valid': True,
                        'models': models
                    }
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to validate AI provider connection',
                    'details': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

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
