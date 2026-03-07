from typing import Optional, Dict, Any

from ..contracts.ai_provider_contract import AIProviderContract
from ..providers.ai.custom_provider import CustomProvider
from ..providers.ai.gemini_provider import GeminiProvider


class AIProviderFactory:
    PROVIDER_CLASSES = {
        'gemini': GeminiProvider,
        'custom': CustomProvider,
    }

    @staticmethod
    def create_provider(provider_type: str, api_key: str, config: Optional[Dict[str, Any]] = None) -> AIProviderContract:
        provider_class = AIProviderFactory.PROVIDER_CLASSES.get(provider_type.lower())

        if provider_class is None:
            supported_providers = list(AIProviderFactory.PROVIDER_CLASSES.keys())
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported providers: {supported_providers}"
            )

        try:
            return provider_class(api_key=api_key, config=config or {})
        except Exception as e:
            raise ValueError(f"Failed to create {provider_type} provider: {e}")

    @staticmethod
    def validate_provider(provider_type: str, api_key: str, config: Optional[Dict[str, Any]] = None) -> tuple[bool, list[Dict[str, Any]]]:
        provider_class = AIProviderFactory.PROVIDER_CLASSES.get(provider_type.lower())
        
        if provider_class is None:
            supported_providers = list(AIProviderFactory.PROVIDER_CLASSES.keys())
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported providers: {supported_providers}"
            )
        
        try:
            provider = provider_class(api_key=api_key, config=config or {})
            return provider.validate_connection()
        except Exception as e:
            return False, []

    @staticmethod
    def get_supported_providers() -> list[str]:
        return list(AIProviderFactory.PROVIDER_CLASSES.keys())
