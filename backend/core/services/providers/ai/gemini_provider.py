import uuid
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

    def generate_with_conversation(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None,
        response_schema: type[BaseModel],
    ) -> tuple[SupportAgentResponse, list[dict]]:
        """
        Convert messages to Gemini format, call generate_content with schema + tools,
        and return (SupportAgentResponse, raw_tool_calls).

        raw_tool_calls is a list of dicts: {"name": str, "args": dict, "id": str}.
        When tool calls are present, parsed_response may be None.
        """
        ROLE_MAP = {"assistant": "model", "system": "system"}

        system_parts = []
        filtered_contents = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "system":
                system_parts.append(types.Part.from_text(text=content))
            elif role == "tool":
                # Tool result message — wrap as function response
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

        # Build tool declarations if provided
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

        # Gemini does not support response_mime_type + tools in the same request.
        # When tools are present: use tool-calling mode (no structured output).
        # When no tools: use structured JSON output mode.
        if gemini_tools:
            config = types.GenerateContentConfig(
                system_instruction=types.Content(parts=system_parts) if system_parts else None,
                tools=[gemini_tools],
            )
        else:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
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

        # Extract tool calls from the response
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
            # Tool calls present — return None for the parsed response.
            # The pipeline will execute tools and call us again without tools,
            # at which point we'll use structured output to get the final answer.
            return None, raw_tool_calls

        # No tool calls — parse the structured JSON response.
        # Gemini thinking models (e.g. 2.5 Flash) sometimes wrap the JSON in a
        # markdown code fence even when structured output is requested. Strip it.
        try:
            raw_text = response.text or ""
            stripped = raw_text.strip()
            if stripped.startswith("```"):
                stripped = stripped.split("\n", 1)[-1]
                if stripped.rstrip().endswith("```"):
                    stripped = stripped.rstrip()[:-3].rstrip()
            parsed = response_schema.model_validate_json(stripped)
        except Exception as e:
            raise ValueError(f"Failed to parse Gemini response as {response_schema.__name__}: {e}")

        return parsed, []

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
