from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class DataProcessor(ABC):
    @abstractmethod
    def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        pass


class IngestionService(ABC):
    @abstractmethod
    def ingest(self, owner: str, repo: str, since: Optional[str] = None) -> None:
        pass
    
    @abstractmethod
    def get_status(self) -> str:
        pass


class AIProviderInterface(ABC):
    @abstractmethod
    def create_client(self, api_key: str, config: Dict[str, Any]) -> Any:
        pass
    
    @abstractmethod
    def validate_connection(self, api_key: str, config: Dict[str, Any]) -> Tuple[bool, Any]:
        pass
    
    @abstractmethod
    def get_models(self) -> List[str]:
        pass


class RepositoryManagerInterface(ABC):
    @abstractmethod
    def get_or_create_repository(self, owner: str, repo: str) -> Any:
        pass
    
    @abstractmethod
    def update_ingestion_status(self, repository: Any, status: str) -> None:
        pass


class ValidationService(ABC):
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Any]:
        pass
    
    @abstractmethod
    def get_validation_errors(self, data: Dict[str, Any]) -> List[str]:
        pass


class EmbeddingService(ABC):
    @abstractmethod
    def create_embeddings(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    def create_sparse_embeddings(self, text: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def store_embeddings(self, embeddings: List[Any]) -> bool:
        pass
