import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel

from core.services.providers.ai.gemini_provider import GeminiProvider


class MockResponseSchema(BaseModel):
    answer: str


@pytest.mark.unit
class TestGeminiProvider:
    def test_init_with_api_key(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            provider = GeminiProvider('test_api_key')

            mock_client_class.assert_called_once_with(api_key='test_api_key')
            assert provider.client == mock_client

    def test_init_with_config(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            config = {'model': 'gemini-pro'}
            provider = GeminiProvider('test_api_key', config)

            mock_client_class.assert_called_once_with(api_key='test_api_key')
            assert provider.client == mock_client

    def test_init_failure(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client_class.side_effect = Exception("API key invalid")

            with pytest.raises(ValueError) as exc_info:
                GeminiProvider('test_api_key')

            assert "Failed to initialize Gemini client: API key invalid" in str(exc_info.value)

    def test_generate_text(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_response = Mock()
            mock_response.text = '{"answer": "test response", "status": "ANSWERED", "escalation": false, "reason_for_escalation": "", "sentiment_score": 50, "escalation_score": 0, "criticality_score": 0}'
            mock_client.models.generate_content.return_value = mock_response

            provider = GeminiProvider('test_api_key')
            result = provider.generate_text('gemini-pro', 'test content')

            mock_client.models.generate_content.assert_called_once()
            assert result.answer == "test response"

    def test_generate_text_api_error(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.models.generate_content.side_effect = Exception("API error")

            provider = GeminiProvider('test_api_key')

            with pytest.raises(ValueError) as exc_info:
                provider.generate_text('gemini-pro', 'test content')

            assert "Gemini API error: API error" in str(exc_info.value)

    def test_validate_connection_success(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_models = [Mock()]
            mock_client.models.list.return_value = mock_models

            provider = GeminiProvider('test_api_key')
            is_valid, models = provider.validate_connection()

            assert is_valid is True
            assert len(models) > 0

    def test_validate_connection_failure(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.models.list.side_effect = Exception("Connection failed")

            provider = GeminiProvider('test_api_key')
            is_valid, models = provider.validate_connection()

            assert is_valid is False
            assert models == []

    def test_get_models_success(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_model = Mock()
            mock_model.name = 'gemini-pro'
            mock_client.models.list.return_value = [mock_model]

            provider = GeminiProvider('test_api_key')
            models = provider.get_models()

            assert len(models) == 1
            assert 'name' in models[0]

    def test_get_models_failure(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.models.list.side_effect = Exception("API error")

            provider = GeminiProvider('test_api_key')

            with pytest.raises(ValueError) as exc_info:
                provider.get_models()

            assert "Failed to retrieve models from Gemini API: API error" in str(exc_info.value)

    def test_embed(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_embedding = Mock()
            mock_embedding.values = [0.1, 0.2, 0.3]
            mock_result = Mock()
            mock_result.embeddings = [mock_embedding]
            mock_client.models.embed_content.return_value = mock_result

            provider = GeminiProvider('test_api_key')
            embeddings = provider.embed('embedding-model', ['test text'])

            mock_client.models.embed_content.assert_called_once_with(model='embedding-model', contents=['test text'])
            assert len(embeddings) == 1
            assert embeddings[0] == [0.1, 0.2, 0.3]

    def test_embed_error(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.models.embed_content.side_effect = Exception("Embedding failed")

            provider = GeminiProvider('test_api_key')

            with pytest.raises(ValueError) as exc_info:
                provider.embed('embedding-model', ['test text'])

            assert "Gemini embedding error: Embedding failed" in str(exc_info.value)

    def test_extract_usage_with_metadata(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            provider = GeminiProvider('test_api_key')

            mock_response = Mock()
            mock_usage = Mock()
            mock_usage.prompt_token_count = 10
            mock_usage.candidates_token_count = 5
            mock_usage.total_token_count = 15
            mock_response.usage_metadata = mock_usage

            usage = provider._extract_usage(mock_response)

            assert usage['prompt_tokens'] == 10
            assert usage['completion_tokens'] == 5
            assert usage['total_tokens'] == 15

    def test_extract_usage_without_metadata(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            provider = GeminiProvider('test_api_key')

            mock_response = Mock()
            delattr(mock_response, 'usage_metadata')

            usage = provider._extract_usage(mock_response)

            assert usage == {}

    def test_generate_with_conversation_simple(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_response = Mock()
            mock_response.text = '{"answer": "response"}'
            mock_response.candidates = None
            mock_client.models.generate_content.return_value = mock_response

            provider = GeminiProvider('test_api_key')
            messages = [{'role': 'user', 'content': 'Hello'}]

            result, tool_calls, usage = provider.generate_with_conversation(
                'gemini-pro',
                messages,
                None,
                MockResponseSchema
            )

            assert result.answer == "response"
            assert tool_calls == []

    def test_generate_with_conversation_with_tools(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_response = Mock()
            mock_response.text = '{"answer": "response"}'
            mock_response.candidates = None
            mock_client.models.generate_content.return_value = mock_response

            provider = GeminiProvider('test_api_key')
            messages = [{'role': 'user', 'content': 'Hello'}]
            tools = [{'function': {'name': 'test_tool', 'parameters': {'type': 'object'}}}]

            result, tool_calls, usage = provider.generate_with_conversation(
                'gemini-pro',
                messages,
                tools,
                MockResponseSchema
            )

            assert result.answer == "response"
            assert tool_calls == []

    def test_generate_with_conversation_with_system_message(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_response = Mock()
            mock_response.text = '{"answer": "response"}'
            mock_response.candidates = None
            mock_client.models.generate_content.return_value = mock_response

            provider = GeminiProvider('test_api_key')
            messages = [
                {'role': 'system', 'content': 'You are a helpful assistant'},
                {'role': 'user', 'content': 'Hello'}
            ]

            result, tool_calls, usage = provider.generate_with_conversation(
                'gemini-pro',
                messages,
                None,
                MockResponseSchema
            )

            assert result.answer == "response"

    def test_generate_with_conversation_with_tool_response(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_response = Mock()
            mock_response.text = '{"answer": "response"}'
            mock_response.candidates = None
            mock_client.models.generate_content.return_value = mock_response

            provider = GeminiProvider('test_api_key')
            messages = [
                {'role': 'tool', 'tool_call_id': '123', 'name': 'test_tool', 'content': 'tool result'}
            ]

            result, tool_calls, usage = provider.generate_with_conversation(
                'gemini-pro',
                messages,
                None,
                MockResponseSchema
            )

            assert result.answer == "response"

    def test_generate_with_conversation_with_function_call(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_fc = Mock()
            mock_fc.name = 'test_function'
            mock_fc.args = {'param': 'value'}

            mock_part = Mock()
            mock_part.function_call = mock_fc
            mock_part.text = None

            mock_content = Mock()
            mock_content.parts = [mock_part]

            mock_candidate = Mock()
            mock_candidate.content = mock_content

            mock_response = Mock()
            mock_response.candidates = [mock_candidate]
            mock_response.text = None
            mock_response.usage_metadata = None
            mock_client.models.generate_content.return_value = mock_response

            provider = GeminiProvider('test_api_key')
            messages = [{'role': 'user', 'content': 'Hello'}]

            result, tool_calls, usage = provider.generate_with_conversation(
                'gemini-pro',
                messages,
                None,
                MockResponseSchema
            )

            assert len(tool_calls) == 1
            assert tool_calls[0]['name'] == 'test_function'
            assert tool_calls[0]['args'] == {'param': 'value'}

    def test_generate_with_conversation_api_error(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.models.generate_content.side_effect = Exception("API error")

            provider = GeminiProvider('test_api_key')
            messages = [{'role': 'user', 'content': 'Hello'}]

            with pytest.raises(ValueError) as exc_info:
                provider.generate_with_conversation('gemini-pro', messages, None, MockResponseSchema)

            assert "Gemini API error: API error" in str(exc_info.value)

    def test_generate_with_tools(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_response = Mock()
            mock_client.models.generate_content.return_value = mock_response

            provider = GeminiProvider('test_api_key')
            contents = [{'role': 'user', 'content': 'Hello'}]
            tool_schemas = [{'function': {'name': 'test_tool', 'parameters': {'type': 'object'}}}]

            result = provider.generate_with_tools('gemini-pro', contents, tool_schemas)

            mock_client.models.generate_content.assert_called_once()
            assert result == mock_response

    def test_generate_with_tools_with_system_message(self):
        with patch('core.services.providers.ai.gemini_provider.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_response = Mock()
            mock_client.models.generate_content.return_value = mock_response

            provider = GeminiProvider('test_api_key')
            contents = [
                {'role': 'system', 'parts': [{'text': 'You are helpful'}]},
                {'role': 'user', 'content': 'Hello'}
            ]
            tool_schemas = [{'function': {'name': 'test_tool', 'parameters': {'type': 'object'}}}]

            result = provider.generate_with_tools('gemini-pro', contents, tool_schemas)

            mock_client.models.generate_content.assert_called_once()
            assert result == mock_response
