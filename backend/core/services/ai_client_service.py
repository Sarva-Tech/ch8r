from typing import Optional, Tuple, Any

from core.models import Application, AIProvider, AppAIProvider
from .factories.ai_provider_factory import AIProviderFactory


class AIClientService:

    def __init__(self):
        self.provider_factory = AIProviderFactory()

    def get_client_and_model(
        self,
        app: Application,
        ai_provider_id: Optional[int] = None,
        model: Optional[str] = None,
        context: str = 'response',
        capability: str = 'text'
    ) -> Tuple[Optional[Any], Optional[str]]:
        provider = None
        selected_model = model

        if ai_provider_id:
            try:
                ai_provider = AIProvider.objects.get(id=ai_provider_id)
                provider = self.provider_factory.create_provider(
                    provider_type=ai_provider.provider,
                    api_key=ai_provider.provider_api_key,
                    config=ai_provider.metadata or {}
                )
            except AIProvider.DoesNotExist:
                return None, None
        else:
            config = self._get_app_provider_config(app, context, capability)
            if config:
                ai_provider = config.ai_provider
                provider = self.provider_factory.create_provider(
                    provider_type=ai_provider.provider,
                    api_key=ai_provider.provider_api_key,
                    config=ai_provider.metadata or {}
                )
                if not selected_model and config.external_model_id:
                    selected_model = config.external_model_id

        if not provider:
            return None, None

        if not selected_model:
            try:
                supported_models = provider.get_models()
                selected_model = supported_models[0]['name'] if supported_models else 'default'
            except Exception:
                selected_model = 'default'

        return provider, selected_model

    def _get_app_provider_config(
        self,
        app: Application,
        context: str,
        capability: str
    ) -> Optional[AppAIProvider]:
        config = AppAIProvider.objects.filter(
            application=app,
            context=context,
            capability=capability,
            is_active=True,
            ai_provider__is_builtin=True
        ).select_related('ai_provider').first()

        if not config:
            config = AppAIProvider.objects.filter(
                application=app,
                context=context,
                capability=capability,
                is_active=True
            ).select_related('ai_provider').order_by('priority').first()

        return config
