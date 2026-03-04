from typing import Optional

from ...contracts.ai_provider_contract import AIProviderContract


class CustomProvider(AIProviderContract):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)

    def generate_content(self, model: str, contents: str, **kwargs) -> str:
        raise NotImplementedError(
            "Custom provider generate_content method not implemented. "
            "Please implement this method in your custom provider class."
        )

    def validate_connection(self) -> tuple[bool, list[str]]:
        raise NotImplementedError(
            "Custom provider validate_connection method not implemented. "
            "Please implement this method in your custom provider class."
        )

    def get_models(self) -> list[str]:
        raise NotImplementedError(
            "Custom provider get_supported_models method not implemented. "
            "Please implement this method in your custom provider class."
        )
