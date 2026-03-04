from abc import ABC, abstractmethod
from typing import Optional


class AIProviderContract(ABC):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def generate_content(self, model: str, contents: str, **kwargs) -> str:
        pass

    @abstractmethod
    def validate_connection(self) -> tuple[bool, list[str]]:
        pass

    @abstractmethod
    def get_models(self) -> list[str]:
        pass
