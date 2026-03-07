from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AIProviderContract(ABC):
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    def generate_content(self, model: str, contents: str, **kwargs) -> str:
        pass

    @abstractmethod
    def validate_connection(self) -> tuple[bool, list[Dict[str, Any]]]:
        pass

    @abstractmethod
    def get_models(self) -> list[Dict[str, Any]]:
        pass
