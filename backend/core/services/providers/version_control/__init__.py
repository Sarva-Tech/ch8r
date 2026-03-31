from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class VCProvider(ABC):
    provider_name: str = ""

    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials

    @abstractmethod
    def validate_credentials(self) -> Tuple[bool, str, Dict[str, Any]]:
        pass

    @abstractmethod
    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_issues(self, owner: str, repo: str, state: str = 'all',
                   since: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_pull_requests(self, owner: str, repo: str, state: str = 'all',
                          since: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_pull_request_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def close(self):
        pass

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            from django.utils import timezone
            if dt_str.endswith('Z'):
                naive_dt = datetime.fromisoformat(dt_str.replace('Z', ''))
                return timezone.make_aware(naive_dt)
            return datetime.fromisoformat(dt_str)
        except Exception:
            from django.utils import timezone
            return timezone.now()


class VCProviderRegistry:
    _providers: Dict[str, type] = {}

    @classmethod
    def register(cls, provider_name: str, provider_class: type):
        if not issubclass(provider_class, VCProvider):
            raise ValueError(f"Provider class must inherit from VCProvider")
        cls._providers[provider_name] = provider_class

    @classmethod
    def get_provider(cls, provider_name: str, credentials: Dict[str, Any]) -> VCProvider:
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class(credentials)

    @classmethod
    def list_providers(cls) -> List[str]:
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, provider_name: str) -> bool:
        return provider_name in cls._providers


def register_provider(provider_name: str):
    def decorator(cls):
        VCProviderRegistry.register(provider_name, cls)
        cls.provider_name = provider_name
        return cls
    return decorator
