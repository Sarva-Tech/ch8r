import json
from typing import Optional, Dict, Any
from pydantic import BaseModel
import pydantic_core
import openai
from ...contracts.ai_provider_contract import AIProviderContract
from core.agent_response_schema import SupportAgentResponse

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
        has_tool_history = any(m.get("role") == "tool" for m in messages)

        try:
            if tools:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
                usage_metadata = self._extract_usage(response)
                choice = response.choices[0]

                if choice.finish_reason == "tool_calls":
                    raw_tool_calls = [
                        {
                            "id": tc.id,
                            "name": tc.function.name,
                            "args": json.loads(tc.function.arguments),
                        }
                        for tc in (choice.message.tool_calls or [])
                    ]
                    messages.append({
                        "role": "assistant",
                        "content": choice.message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in (choice.message.tool_calls or [])
                        ],
                    })
                    return choice.message.content or "", raw_tool_calls, usage_metadata

                return self._parse_structured_response(choice, response_schema, self._extract_usage(response))

            elif has_tool_history:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                )
                usage_metadata = self._extract_usage(response)
                choice = response.choices[0]
                return self._parse_structured_response(choice, response_schema, usage_metadata)

            else:
                completion = self.client.beta.chat.completions.parse(
                    model=model,
                    messages=messages,
                    response_format=response_schema,
                )
                usage_metadata = self._extract_usage(completion)
                message = completion.choices[0].message

                if message.refusal:
                    raise ValueError(f"OpenAI refused the request: {message.refusal}")

                return message.parsed, [], usage_metadata

        except openai.AuthenticationError as e:
            raise ValueError(f"Invalid OpenAI API key: {e}")
        except openai.RateLimitError as e:
            raise ValueError(f"OpenAI rate limit exceeded: {e}")
        except openai.APIError as e:
            raise ValueError(f"OpenAI API error: {e}")

    def _parse_structured_response(self, choice, response_schema, usage_metadata):
        raw = choice.message.content or ""
        stripped = raw.strip()

        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[-1]
            if stripped.rstrip().endswith("```"):
                stripped = stripped.rstrip()[:-3].rstrip()

        brace_idx = stripped.find("{")
        if brace_idx > 0:
            stripped = stripped[brace_idx:]
        last_brace = stripped.rfind("}")
        if last_brace != -1 and last_brace < len(stripped) - 1:
            stripped = stripped[:last_brace + 1]

        if not stripped.startswith("{"):
            stripped = json.dumps({
                "answer": raw.strip(),
                "status": "ANSWERED",
                "escalation": False,
                "reason_for_escalation": "",
                "sentiment_score": 50,
                "escalation_score": 0,
                "criticality_score": 0,
            })

        try:
            parsed = response_schema.model_validate_json(stripped)
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

    def classify_intent(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None,
        response_schema: type[BaseModel],
    ) -> tuple:
        try:
            completion = self.client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                response_format=response_schema,
            )
            usage_metadata = self._extract_usage(completion)
            message = completion.choices[0].message

            if message.refusal:
                raise ValueError(f"OpenAI refused the request: {message.refusal}")

            return message.parsed, usage_metadata

        except pydantic_core._pydantic_core.ValidationError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Structured output failed for intent classification, falling back to manual parsing: {e}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            usage_metadata = self._extract_usage(response)
            choice = response.choices[0]
            return self._parse_structured_response(choice, response_schema, usage_metadata)
        except openai.AuthenticationError as e:
            raise ValueError(f"Invalid OpenAI API key: {e}")
        except openai.RateLimitError as e:
            raise ValueError(f"OpenAI rate limit exceeded: {e}")
        except openai.APIError as e:
            raise ValueError(f"OpenAI API error: {e}")

    def generate_final_response(
        self,
        model: str,
        messages: list[dict],
        response_schema: type[BaseModel],
    ) -> tuple:
        try:
            has_tool_history = any(m.get("role") == "tool" for m in messages)

            if has_tool_history:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format={"type": "json_object"},
                )
                usage_metadata = self._extract_usage(response)
                choice = response.choices[0]
                return self._parse_structured_response(choice, response_schema, usage_metadata)
            else:
                completion = self.client.beta.chat.completions.parse(
                    model=model,
                    messages=messages,
                    response_format=response_schema,
                )
                usage_metadata = self._extract_usage(completion)
                message = completion.choices[0].message

                if message.refusal:
                    raise ValueError(f"OpenAI refused the request: {message.refusal}")

                return message.parsed, usage_metadata

        except openai.AuthenticationError as e:
            raise ValueError(f"Invalid OpenAI API key: {e}")
        except openai.RateLimitError as e:
            raise ValueError(f"OpenAI rate limit exceeded: {e}")
        except openai.APIError as e:
            raise ValueError(f"OpenAI API error: {e}")
