from typing import Optional, Dict, Any, List
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

    def generate_text(self, model: str, contents: str, **kwargs) -> SupportAgentResponse:
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=SupportAgentResponse.model_json_schema(),
                )
            )

            return SupportAgentResponse.model_validate_json(response.text)

        except Exception as e:
            raise ValueError(f"Gemini API error: {e}")

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
