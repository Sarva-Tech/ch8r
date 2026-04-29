import uuid
import copy
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig
from ...contracts.ai_provider_contract import AIProviderContract
from core.agent_response_schema import SupportAgentResponse


class GeminiProvider(AIProviderContract):
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, config)
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini client: {e}")

    def _clean_json_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        cleaned_schema = copy.deepcopy(schema)
        
        def remove_additional_properties(obj):
            if isinstance(obj, dict):
                keys_to_remove = ['additionalProperties', 'additional_properties']
                for key in keys_to_remove:
                    obj.pop(key, None)
                
                for value in obj.values():
                    remove_additional_properties(value)
            elif isinstance(obj, list):
                for item in obj:
                    remove_additional_properties(item)
        
        remove_additional_properties(cleaned_schema)
        return cleaned_schema

    def generate_text(self, model: str, contents: str, **kwargs) -> SupportAgentResponse:
        try:
            cleaned_schema = self._clean_json_schema(SupportAgentResponse.model_json_schema())
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=cleaned_schema,
                )
            )
            return SupportAgentResponse.model_validate_json(response.text)
        except Exception as e:
            raise ValueError(f"Gemini API error: {e}")

    def generate_with_conversation(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None,
        response_schema: type[BaseModel],
    ) -> tuple:
        ROLE_MAP = {"assistant": "model", "system": "system"}
        system_parts: list = []
        filtered_contents: list = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append(types.Part.from_text(text=content))
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                tool_name = msg.get("name", tool_call_id)
                filtered_contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": content},
                            )
                        ],
                    )
                )
            else:
                gemini_role = ROLE_MAP.get(role, role)
                filtered_contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=content)],
                    )
                )

        gemini_tools = None
        if tools:
            function_declarations = []
            for tool in tools:
                fn = tool.get("function", tool)
                function_declarations.append({
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
                })
            gemini_tools = types.Tool(function_declarations=function_declarations)

        if gemini_tools:
            config = types.GenerateContentConfig(
                system_instruction=types.Content(parts=system_parts) if system_parts else None,
                tools=[gemini_tools],
            )
        else:
            cleaned_schema = self._clean_json_schema(response_schema.model_json_schema())
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=cleaned_schema,
                system_instruction=types.Content(parts=system_parts) if system_parts else None,
            )

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=filtered_contents,
                config=config,
            )
        except Exception as e:
            raise ValueError(f"Gemini API error: {e}")

        usage_metadata = self._extract_usage(response)

        raw_tool_calls: list[dict] = []
        for candidate in response.candidates or []:
            for part in candidate.content.parts or []:
                if part.function_call:
                    fc = part.function_call
                    raw_tool_calls.append({
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                        "id": fc.name + "_" + uuid.uuid4().hex[:8],
                    })

        if raw_tool_calls:
            text_parts = []
            for candidate in response.candidates or []:
                for part in candidate.content.parts or []:
                    if hasattr(part, "text") and part.text and not part.function_call:
                        text_parts.append(part.text)
            model_text = "\n".join(text_parts).strip()
            return model_text, raw_tool_calls, usage_metadata

        try:
            raw_text = response.text or ""
            stripped = raw_text.strip()

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

            # If no JSON object found, wrap plain text in schema
            if not stripped.startswith("{"):
                import json
                wrapped = {
                    "answer": stripped,
                    "status": "ANSWERED",
                    "escalation": False,
                    "reason_for_escalation": "",
                    "sentiment_score": 50,
                    "escalation_score": 0,
                    "criticality_score": 0,
                }
                stripped = json.dumps(wrapped)

            parsed = response_schema.model_validate_json(stripped)
        except Exception as e:
            raise ValueError(f"Failed to parse Gemini response as {response_schema.__name__}: {e}")

        return parsed, [], usage_metadata

    def _extract_usage(self, response) -> dict:
        usage: dict = {}
        try:
            meta = getattr(response, "usage_metadata", None)
            if meta:
                mapping = {
                    "prompt_tokens": "prompt_token_count",
                    "completion_tokens": "candidates_token_count",
                    "total_tokens": "total_token_count",
                    "cached_tokens": "cached_content_token_count",
                }
                for key, attr in mapping.items():
                    val = getattr(meta, attr, None)
                    if val is not None:
                        usage[key] = val
        except Exception:
            pass
        return usage

    def generate_with_tools(self, model: str, contents: list, tool_schemas: List[dict]) -> types.GenerateContentResponse:
        ROLE_MAP = {"assistant": "model", "system": "system"}
        system_parts = []
        filtered_contents = []
        for msg in contents:
            role = msg.get("role", "") if isinstance(msg, dict) else getattr(msg, "role", "")
            if role == "system":
                parts = msg.get("parts", []) if isinstance(msg, dict) else getattr(msg, "parts", [])
                for p in parts:
                    text = p.get("text", "") if isinstance(p, dict) else getattr(p, "text", "")
                    if text:
                        system_parts.append(types.Part.from_text(text=text))
            else:
                gemini_role = ROLE_MAP.get(role, role)
                if isinstance(msg, dict):
                    filtered_contents.append({**msg, "role": gemini_role})
                else:
                    filtered_contents.append(msg)

        function_declarations = []
        for tool in tool_schemas:
            fn = tool.get("function", tool)
            function_declarations.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
            })

        gemini_tools = types.Tool(function_declarations=function_declarations)
        config = types.GenerateContentConfig(
            tools=[gemini_tools],
            system_instruction=types.Content(parts=system_parts) if system_parts else None,
        )
        return self.client.models.generate_content(
            model=model,
            contents=filtered_contents,
            config=config,
        )

    def validate_connection(self) -> tuple[bool, list[Dict[str, Any]]]:
        try:
            models = self.get_models()
            return True, models
        except Exception as e:
            return False, []

    def get_models(self) -> list[Dict[str, Any]]:
        try:
            models = list(self.client.models.list())
            serializable_models = []
            for model in models:
                model_dict = vars(model).copy()
                stringified_model = {key: str(value) for key, value in model_dict.items()}
                serializable_models.append(stringified_model)
            return serializable_models
        except Exception as e:
            raise ValueError(f"Failed to retrieve models from Gemini API: {e}")

    def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        try:
            result = self.client.models.embed_content(model=model, contents=texts)
            return [e.values for e in result.embeddings]
        except Exception as e:
            raise ValueError(f"Gemini embedding error: {e}")

    def classify_intent(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None,
        response_schema: type[BaseModel],
    ) -> tuple:
        ROLE_MAP = {"assistant": "model", "system": "system"}
        system_parts: list = []
        filtered_contents: list = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append(types.Part.from_text(text=content))
            else:
                gemini_role = ROLE_MAP.get(role, role)
                filtered_contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=content)],
                    )
                )

        cleaned_schema = self._clean_json_schema(response_schema.model_json_schema())
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=cleaned_schema,
            system_instruction=types.Content(parts=system_parts) if system_parts else None,
        )

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=filtered_contents,
                config=config,
            )
        except Exception as e:
            raise ValueError(f"Gemini API error: {e}")

        usage_metadata = self._extract_usage(response)

        try:
            raw_text = response.text or ""
            stripped = raw_text.strip()

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
                import json
                wrapped = {
                    "intent": "others",
                    "tools_to_call": [],
                    "reasoning": "Failed to parse structured response",
                    "kb_sufficient": True,
                    "sentiment_score": 50,
                    "escalation_score": 0,
                    "criticality_score": 0,
                }
                stripped = json.dumps(wrapped)

            parsed = response_schema.model_validate_json(stripped)
        except Exception as e:
            raise ValueError(f"Failed to parse Gemini response as {response_schema.__name__}: {e}")

        return parsed, usage_metadata

    def generate_final_response(
        self,
        model: str,
        messages: list[dict],
        response_schema: type[BaseModel],
    ) -> tuple:
        ROLE_MAP = {"assistant": "model", "system": "system"}
        system_parts: list = []
        filtered_contents: list = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append(types.Part.from_text(text=content))
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                tool_name = msg.get("name", tool_call_id)
                filtered_contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": content},
                            )
                        ],
                    )
                )
            else:
                gemini_role = ROLE_MAP.get(role, role)
                filtered_contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[types.Part.from_text(text=content)],
                    )
                )

        cleaned_schema = self._clean_json_schema(response_schema.model_json_schema())
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=cleaned_schema,
            system_instruction=types.Content(parts=system_parts) if system_parts else None,
        )

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=filtered_contents,
                config=config,
            )
        except Exception as e:
            raise ValueError(f"Gemini API error: {e}")

        usage_metadata = self._extract_usage(response)

        try:
            raw_text = response.text or ""
            stripped = raw_text.strip()

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
                import json
                wrapped = {
                    "answer": stripped,
                    "status": "ANSWERED",
                    "escalation": False,
                    "reason_for_escalation": "",
                    "sentiment_score": 50,
                    "escalation_score": 0,
                    "criticality_score": 0,
                }
                stripped = json.dumps(wrapped)

            parsed = response_schema.model_validate_json(stripped)
        except Exception as e:
            raise ValueError(f"Failed to parse Gemini response as {response_schema.__name__}: {e}")

        return parsed, usage_metadata
