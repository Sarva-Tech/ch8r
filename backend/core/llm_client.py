from openai import OpenAI
from openai.types.shared_params import ResponseFormatJSONSchema

from typing import Optional, Any

class LLMClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def chat(self, messages: list, model: str, response_schema: Optional[ResponseFormatJSONSchema] = None, tools: Optional[any] = None):
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if response_schema:
            kwargs["response_format"] = response_schema

        if tools:
            kwargs["tools"] = tools

        response = client.chat.completions.create(**kwargs)
        return response

    def responses(self, messages: list, model: str, response_schema: Optional[ResponseFormatJSONSchema] = None, tools: Optional[Any] = None):
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        kwargs: dict[str, Any] = {
            "model": model,
            "input": messages,
            "temperature": 0.7
        }
        if tools:
            kwargs["tools"] = tools
        if response_schema:
            kwargs["response_format"] = response_schema
        return client.responses.create(**kwargs)

    def embed(self, messages: list[str], model: str):
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        embedding = client.embeddings.create(
            input=messages,
            model=model
        )
        return embedding.data[0].embedding
