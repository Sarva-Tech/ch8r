from typing import Optional, Dict, Any
from google import genai
from ...contracts.ai_provider_contract import AIProviderContract

class GeminiProvider(AIProviderContract):
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key, config)
        
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini client: {e}")

    def generate_text(self, model: str, contents: str, **kwargs) -> str:
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=contents
            )

            return response.text

        except Exception as e:
            raise ValueError(f"Gemini API error: {e}")

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
