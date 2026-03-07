from typing import Optional, Any, Dict

from core.models import Application, AppAIProvider
from .factories.ai_provider_factory import AIProviderFactory


class AIService:

    def __init__(self):
        self.provider_factory = AIProviderFactory()

    def get_provider_for_app(self, application: Application, context: str = 'widget',
                           capability: str = 'text') -> Optional[Any]:
        try:
            config = AppAIProvider.objects.filter(
                application=application,
                context=context,
                capability=capability,
                is_active=True,
                ai_provider__is_builtin=True
            ).select_related('ai_provider').first()

            if not config:
                config = AppAIProvider.objects.filter(
                    application=application,
                    context=context,
                    capability=capability,
                    is_active=True
                ).select_related('ai_provider').order_by('priority').first()

            if not config:
                return None

            ai_provider = config.ai_provider

            provider_instance = self.provider_factory.create_provider(
                provider_type=ai_provider.provider,
                api_key=ai_provider.provider_api_key,
                config=ai_provider.metadata or {}
            )

            return provider_instance

        except Exception as e:
            print(f"Error getting AI provider: {e}")
            return None

    def generate_content(self, application: Application, contents: str,
                        model: Optional[str] = None, context: str = 'widget',
                        capability: str = 'text', **kwargs) -> Optional[str]:
        provider = self.get_provider_for_app(application, context, capability)
        if not provider:
            return None

        if model is None:
            config = AppAIProvider.objects.filter(
                application=application,
                context=context,
                capability=capability,
                is_active=True
            ).select_related('ai_provider').order_by('priority').first()

            if config and config.external_model_id:
                model = config.external_model_id
            else:
                supported_models = provider.get_models()
                model = supported_models[0]['name'] if supported_models else 'default'

        try:
            return provider.generate_content(model, contents, **kwargs)
        except Exception as e:
            print(f"Error generating content: {e}")
            return None

    def validate_provider_connection(self, application: Application,
                                   context: str = 'widget',
                                   capability: str = 'text') -> tuple[bool, list[Dict[str, Any]]]:
        provider = self.get_provider_for_app(application, context, capability)
        if not provider:
            return False, []

        try:
            return provider.validate_connection()
        except Exception:
            return False, []
