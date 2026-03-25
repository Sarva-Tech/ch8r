from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.db import models

from core.serializers.ai_provider import AIProviderCreateSerializer, AIProviderSerializer
from core.models import AIProvider, AIProviderModels
from core.consts import SUPPORTED_AI_PROVIDERS
from core.services.ai_client_service import AIClientService


class AIProviderViewSet(viewsets.ModelViewSet):

    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'uuid'
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    pagination_class = PageNumberPagination

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_service = AIClientService()

    def get_queryset(self):
        """Get queryset filtered by user"""
        user = self.request.user
        return AIProvider.objects.filter(
            models.Q(creator=user) | models.Q(is_builtin=True)
        )

    def get_serializer_class(self):
        """Get appropriate serializer based on action"""
        if self.action in ['create', 'update', 'partial_update']:
            return AIProviderCreateSerializer
        return AIProviderSerializer

    def create(self, request, *args, **kwargs):
        """Create a new AI provider with validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = self._create_ai_provider(serializer.validated_data, request.user)
            return Response(result, status=status.HTTP_201_CREATED)

        except Exception as e:
            return self._handle_validation_error(e)

    def _create_ai_provider(self, validated_data, user):
        """Create AI provider with validation"""
        is_valid, provider_models = self.ai_service.validate_ai_provider(validated_data)

        if not is_valid:
            raise ValueError('Failed to validate AI provider connection')

        ai_provider = self.get_serializer().create(validated_data)
        ai_provider.creator = user
        ai_provider.save()

        self._store_provider_models(ai_provider, provider_models, user)

        return self._format_creation_response(ai_provider, provider_models)

    def _store_provider_models(self, ai_provider, provider_models, user):
        """Store provider models in database"""
        AIProviderModels.objects.update_or_create(
            ai_provider=ai_provider,
            defaults={
                'models_data': provider_models,
                'creator': user
            }
        )

    def _format_creation_response(self, ai_provider, provider_models):
        """Format creation response"""
        response_serializer = AIProviderSerializer(ai_provider)
        return {
            'ai_provider': response_serializer.data,
            'validation': {
                'is_valid': True,
                'models': provider_models
            }
        }

    def list(self, request, *args, **kwargs):
        """List AI providers with supported providers info"""
        response = super().list(request, *args, **kwargs)
        return self._format_list_response(response)

    def _format_list_response(self, response):
        """Format list response with supported providers"""
        if isinstance(response.data, dict):
            response.data['supported_ai_providers'] = SUPPORTED_AI_PROVIDERS
        else:
            response.data = {
                'results': response.data,
                'supported_ai_providers': SUPPORTED_AI_PROVIDERS
            }
        return response

    def update(self, request, *args, **kwargs):
        """Update AI provider with validation"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            result = self._update_ai_provider(serializer, instance, request.user)
            return Response(result)

        except Exception as e:
            return self._handle_validation_error(e)

    def _update_ai_provider(self, serializer, instance, user):
        validated_data = serializer.validated_data

        api_key_to_validate = self._get_api_key_to_validate(validated_data, instance)

        if api_key_to_validate and api_key_to_validate.strip():
            is_valid, provider_models = self.ai_service.validate_ai_provider(
                validated_data, instance
            )

            if not is_valid:
                raise ValueError('Failed to validate AI provider connection')

            self._store_provider_models(instance, provider_models, user)

        updated_instance = serializer.save()

        return self._format_update_response(updated_instance)

    def _get_api_key_to_validate(self, validated_data, instance):
        """Get API key that needs validation"""
        return validated_data.get('provider_api_key') or instance.provider_api_key

    def _format_update_response(self, instance):
        """Format update response"""
        response_serializer = AIProviderSerializer(instance)
        return {
            'ai_provider': response_serializer.data,
            'message': 'AI provider updated successfully'
        }

    def _handle_validation_error(self, error):
        """Handle validation errors consistently"""
        return Response(
            {
                'error': 'Failed to validate AI provider connection',
                'details': str(error)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def all_models(self, request):
        user = request.user

        ai_providers = self.get_queryset().filter(creator=user)

        result = []
        for ai_provider in ai_providers:
            try:
                provider_models = AIProviderModels.objects.get(ai_provider=ai_provider)
                result.append({
                    'ai_provider': AIProviderSerializer(ai_provider).data,
                    'ai_provider_models': {
                        'id': provider_models.id,
                        'models_data': provider_models.models_data,
                        'created_at': provider_models.created_at,
                        'updated_at': provider_models.updated_at
                    }
                })
            except AIProviderModels.DoesNotExist:
                continue
            except Exception as e:
                print(f"Error retrieving models for provider {ai_provider.uuid}: {str(e)}")
                continue

        return Response({
            'providers': result
        })
