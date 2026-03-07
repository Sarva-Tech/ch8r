from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.db import models
from core.serializers.ai_provider import AIProviderCreateSerializer, AIProviderSerializer
from core.models import AIProvider, AIProviderModels
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

    def _validate_ai_provider(self, validated_data, instance=None):
        from core.services.factories.ai_provider_factory import AIProviderFactory
        
        factory = AIProviderFactory()
        main_fields = ['name', 'provider', 'provider_api_key']
        config = {}
        
        if instance:
            current_data = {
                'name': instance.name,
                'provider': instance.provider,
                'provider_api_key': instance.provider_api_key
            }
            if instance.metadata:
                config.update(instance.metadata)
            update_data = {**current_data, **validated_data}
            if not update_data['provider_api_key']:
                update_data['provider_api_key'] = instance.provider_api_key
            validation_data = update_data
        else:
            validation_data = validated_data
        
        for field, value in validation_data.items():
            if field not in main_fields:
                config[field] = str(value).strip() if value is not None else ''
        
        is_valid, provider_models = factory.validate_provider(
            provider_type=validation_data['provider'],
            api_key=validation_data['provider_api_key'],
            config=config
        )
        
        return is_valid, provider_models

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        try:
            is_valid, provider_models = self._validate_ai_provider(validated_data)
            
            if not is_valid:
                return Response(
                    {
                        'error': 'Failed to validate AI provider connection',
                        'details': 'Unable to connect to the AI provider with the provided credentials'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ai_provider = serializer.save()
            
            AIProviderModels.objects.update_or_create(
                ai_provider=ai_provider,
                defaults={
                    'models_data': provider_models,
                    'creator': request.user
                }
            )
            
            response_serializer = AIProviderSerializer(ai_provider)
            return Response(
                {
                    'ai_provider': response_serializer.data,
                    'validation': {
                        'is_valid': True,
                        'models': provider_models
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

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        
        api_key_to_validate = validated_data.get('provider_api_key') or instance.provider_api_key
        
        if api_key_to_validate and api_key_to_validate.strip():
            try:
                is_valid, provider_models = self._validate_ai_provider(validated_data, instance)
                
                if not is_valid:
                    return Response(
                        {
                            'error': 'Failed to validate AI provider connection',
                            'details': 'Unable to connect to the AI provider with the provided credentials'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            except Exception as e:
                return Response(
                    {
                        'error': 'Failed to validate AI provider connection',
                        'details': str(e)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {
                    'error': 'API key is required',
                    'details': 'An API key must be provided to validate the AI provider connection'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_instance = serializer.save()
        
        AIProviderModels.objects.update_or_create(
            ai_provider=updated_instance,
            defaults={
                'models_data': provider_models,
                'creator': request.user
            }
        )
        
        response_serializer = AIProviderSerializer(updated_instance)
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "deleted"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def models(self, request, uuid=None):
        ai_provider = self.get_object()
        
        try:
            provider_models = AIProviderModels.objects.get(ai_provider=ai_provider)
            return Response({
                'ai_provider': AIProviderSerializer(ai_provider).data,
                'ai_provider_models': {
                    'id': provider_models.id,
                    'models_data': provider_models.models_data,
                    'created_at': provider_models.created_at,
                    'updated_at': provider_models.updated_at
                }
            })
        except AIProviderModels.DoesNotExist:
            return Response({
                'error': 'Models data not found for this AI provider'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Failed to retrieve models: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
