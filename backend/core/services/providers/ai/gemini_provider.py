from typing import Optional
from google import genai
from ...contracts.ai_provider_contract import AIProviderContract


class GeminiProvider(AIProviderContract):
    SUPPORTED_MODELS = [
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        'gemini-1.0-pro',
        'gemini-pro-vision'
    ]
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini client: {e}")

    def generate_content(self, model: str, contents: str, **kwargs) -> str:
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}. Supported models: {self.SUPPORTED_MODELS}")

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=contents
            )

            return response.text

        except Exception as e:
            raise ValueError(f"Gemini API error: {e}")

    def validate_connection(self) -> tuple[bool, list[str]]:
        try:
            models = self.get_models()
            return True, models
        except Exception as e:
            return False, []

    def get_models(self) -> list[str]:
        try:
            models = list(self.client.models.list())
            return [model.name for model in models]
        except Exception as e:
            raise ValueError(f"Failed to retrieve models from Gemini API: {e}")
