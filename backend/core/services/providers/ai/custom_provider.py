import json
import requests
from typing import Optional, Dict, Any, List
from ...contracts.ai_provider_contract import AIProviderContract


class CustomProvider(AIProviderContract):
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, config)

        raise NotImplementedError("Not implemented")

    def generate_content(self, model: str, contents: str, **kwargs) -> str:
        raise NotImplementedError("Not implemented")

    def validate_connection(self) -> tuple[bool, List[str]]:
        raise NotImplementedError("Not implemented")

    def get_models(self) -> List[str]:
        raise NotImplementedError("Not implemented")
