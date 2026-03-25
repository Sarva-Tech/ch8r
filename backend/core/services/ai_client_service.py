from typing import Optional, Tuple, Any, Dict

from core.models import Application, AIProvider, AppAIProvider
from .factories.ai_provider_factory import AIProviderFactory
from .ai_provider_validator import AIProviderValidator


class AIClientService:

    def __init__(self):
        self.provider_factory = AIProviderFactory()
        self.validator = AIProviderValidator()

    def get_client_and_model(
        self,
        app: Application,
        ai_provider_id: Optional[int] = None,
        model: Optional[str] = None,
        context: str = 'response',
        capability: str = 'text'
    ) -> Tuple[Optional[Any], Optional[str]]:
        provider_config = self._resolve_provider_config(app, ai_provider_id, context, capability)

        if not provider_config:
            return None, None

        client = self._create_client(provider_config)
        selected_model = model or provider_config.get('model')

        if not selected_model:
            selected_model = self._get_default_model(client)

        return client, selected_model

    def _resolve_provider_config(
        self,
        app: Application,
        ai_provider_id: Optional[int],
        context: str,
        capability: str
    ) -> Optional[Dict[str, Any]]:
        if ai_provider_id:
            return self._get_provider_by_id(ai_provider_id)
        else:
            return self._get_app_provider_config(app, context, capability)

    def _get_provider_by_id(self, ai_provider_id: int) -> Optional[Dict[str, Any]]:
        try:
            ai_provider = AIProvider.objects.get(id=ai_provider_id)
            return {
                'provider': ai_provider,
                'type': ai_provider.provider,
                'api_key': ai_provider.provider_api_key,
                'config': ai_provider.metadata or {}
            }
        except AIProvider.DoesNotExist:
            return None

    def _get_app_provider_config(
        self,
        app: Application,
        context: str,
        capability: str
    ) -> Optional[Dict[str, Any]]:
        try:
            config = self._get_app_provider(app, context, capability)
            if not config:
                return None

            return {
                'provider': config.ai_provider,
                'type': config.ai_provider.provider,
                'api_key': config.ai_provider.provider_api_key,
                'config': config.ai_provider.metadata or {},
                'model': config.external_model_id
            }
        except Exception:
            return None

    def _get_app_provider(self, app: Application, context: str, capability: str) -> Optional[AppAIProvider]:
        return app.app_ai_providers.filter(
            context=context,
            capability=capability
        ).first()

    def _create_client(self, provider_config: Dict[str, Any]) -> Optional[Any]:
        try:
            return self.provider_factory.create_provider(
                provider_type=provider_config['type'],
                api_key=provider_config['api_key'],
                config=provider_config['config']
            )
        except Exception:
            return None

    def _get_default_model(self, client: Any) -> Optional[str]:
        try:
            supported_models = client.get_models()
            return supported_models[0] if supported_models else None
        except Exception:
            return None

    def validate_ai_provider(
        self,
        validated_data: Dict[str, Any],
        instance: AIProvider = None
    ) -> Tuple[bool, Any]:
        main_data, config_data = self.validator.validate_ai_provider_data(validated_data, instance)

        is_valid, provider_models = self.validator.validate_provider_config(
            provider_type=main_data['provider'],
            api_key=main_data['provider_api_key'],
            config=config_data
        )

        return is_valid, provider_models if is_valid else None
