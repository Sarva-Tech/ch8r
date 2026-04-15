import json
from typing import Optional, Dict, Any
from pydantic import BaseModel
import openai
from ...contracts.ai_provider_contract import AIProviderContract
from core.agent_response_schema import SupportAgentResponse

EXCLUDED_PREFIXES = ("whisper", "tts", "dall-e", "davinci", "babbage", "text-embedding-ada")
EXCLUDED_SUFFIXES = ("-instruct",)


class OpenAIProvider(AIProviderContract):
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(api_key, config)
        base_url = self.config.get("base_url") if self.config else None
        try:
            kwargs: Dict[str, Any] = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self.client = openai.OpenAI(**kwargs)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")

    def validate_connection(self) -> tuple[bool, list[Dict[str, Any]]]:
        try:
            models = self.get_models()
            return True, models
        except Exception:
            return False, []

    def get_models(self) -> list[Dict[str, Any]]:
        try:
            raw_models = self.client.models.list().data
        except Exception as e:
            raise ValueError(f"Failed to retrieve models from OpenAI API: {e}")

        result = []
        for model in raw_models:
            model_id = model.id
            if any(model_id.startswith(p) for p in EXCLUDED_PREFIXES):
                continue
            if any(model_id.endswith(s) for s in EXCLUDED_SUFFIXES):
                continue
            result.append({
                "id": model_id,
                "name": model_id,
                "object": model.object,
                "created": model.created,
                "owned_by": model.owned_by,
            })
        return result

    def generate_with_conversation(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None,
        response_schema: type[BaseModel],
    ) -> tuple:
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        else:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "schema": response_schema.model_json_schema(),
                    "strict": True,
                },
            }

        try:
            response = self.client.chat.completions.create(**kwargs)
        except openai.AuthenticationError as e:
            raise ValueError(f"Invalid OpenAI API key: {e}")
        except openai.RateLimitError as e:
            raise ValueError(f"OpenAI rate limit exceeded: {e}")
        except openai.APIError as e:
            raise ValueError(f"OpenAI API error: {e}")

        usage_metadata = self._extract_usage(response)
        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            raw_tool_calls = []
            for tc in (choice.message.tool_calls or []):
                raw_tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": json.loads(tc.function.arguments),
                })
            return choice.message.content or "", raw_tool_calls, usage_metadata

        try:
            parsed = response_schema.model_validate_json(choice.message.content)
        except Exception as e:
            raise ValueError(f"Failed to parse OpenAI response as {response_schema.__name__}: {e}")

        return parsed, [], usage_metadata

    def _extract_usage(self, response) -> dict:
        usage: dict = {}
        try:
            meta = getattr(response, "usage", None)
            if meta is not None:
                for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                    val = getattr(meta, key, None)
                    if val is not None:
                        usage[key] = val
                details = getattr(meta, "prompt_tokens_details", None)
                if details is not None:
                    cached = getattr(details, "cached_tokens", None)
                    if cached is not None:
                        usage["cached_tokens"] = cached
        except Exception:
            pass
        return usage

    def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        try:
            response = self.client.embeddings.create(input=texts, model=model)
        except Exception as e:
            raise ValueError(f"OpenAI embedding error: {e}")
        sorted_data = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in sorted_data]

    def generate_text(self, model: str, contents: str, **kwargs) -> SupportAgentResponse:
        messages = [{"role": "user", "content": contents}]
        result, _, _ = self.generate_with_conversation(
            model=model,
            messages=messages,
            tools=None,
            response_schema=SupportAgentResponse,
        )
        return result
