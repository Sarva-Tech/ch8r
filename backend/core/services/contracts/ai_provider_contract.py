from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel
    from core.agent_response_schema import SupportAgentResponse


class AIProviderContract(ABC):
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    def generate_text(self, model: str, contents: str, **kwargs) -> str:
        pass

    @abstractmethod
    def generate_with_conversation(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None,
        response_schema: "type[BaseModel]",
    ) -> "tuple[SupportAgentResponse, list[dict]]":
        """
        Send a structured conversation to the provider and return a parsed response.

        Returns (parsed_response, raw_tool_calls).
        raw_tool_calls is an empty list when no tool calls were requested.
        Each raw_tool_call dict has at minimum: {"name": str, "args": dict, "id": str}.
        """
        pass

    @abstractmethod
    def validate_connection(self) -> tuple[bool, list[Dict[str, Any]]]:
        pass

    @abstractmethod
    def get_models(self) -> list[Dict[str, Any]]:
        pass

    @abstractmethod
    def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        pass
