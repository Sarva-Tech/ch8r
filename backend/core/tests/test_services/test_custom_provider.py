import pytest
from unittest.mock import Mock, patch
from pydantic import BaseModel

from core.services.providers.ai.custom_provider import CustomProvider


class MockResponseSchema(BaseModel):
    answer: str


@pytest.mark.unit
class TestCustomProvider:
    def test_init_raises_not_implemented(self):
        with pytest.raises(NotImplementedError) as exc_info:
            CustomProvider('test_api_key')

        assert "Not implemented" in str(exc_info.value)

    def test_init_with_config_raises_not_implemented(self):
        with pytest.raises(NotImplementedError) as exc_info:
            CustomProvider('test_api_key', {'model': 'custom'})

        assert "Not implemented" in str(exc_info.value)

    def test_generate_text_raises_not_implemented(self):
        with patch.object(CustomProvider, '__init__', lambda self, api_key, config=None: None):
            provider = CustomProvider('test_api_key')

            with pytest.raises(NotImplementedError) as exc_info:
                provider.generate_text('custom-model', 'test content')

            assert "Not implemented" in str(exc_info.value)

    def test_generate_with_conversation_with_user_messages(self):
        with patch.object(CustomProvider, '__init__', lambda self, api_key, config=None: None):
            provider = CustomProvider('test_api_key')
            provider.generate_text = Mock(return_value='{"answer": "response"}')

            messages = [
                {'role': 'system', 'content': 'You are helpful'},
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'Hi there'},
                {'role': 'user', 'content': 'How are you?'}
            ]

            result, tool_calls = provider.generate_with_conversation(
                'custom-model',
                messages,
                None,
                MockResponseSchema
            )

            provider.generate_text.assert_called_once_with('custom-model', 'How are you?')
            assert result == '{"answer": "response"}'
            assert tool_calls == []

    def test_generate_with_conversation_single_user_message(self):
        with patch.object(CustomProvider, '__init__', lambda self, api_key, config=None: None):
            provider = CustomProvider('test_api_key')
            provider.generate_text = Mock(return_value='{"answer": "response"}')

            messages = [
                {'role': 'user', 'content': 'Hello'}
            ]

            result, tool_calls = provider.generate_with_conversation(
                'custom-model',
                messages,
                None,
                MockResponseSchema
            )

            provider.generate_text.assert_called_once_with('custom-model', 'Hello')
            assert result == '{"answer": "response"}'
            assert tool_calls == []

    def test_generate_with_conversation_no_user_messages(self):
        with patch.object(CustomProvider, '__init__', lambda self, api_key, config=None: None):
            provider = CustomProvider('test_api_key')
            provider.generate_text = Mock(return_value='{"answer": "response"}')

            messages = [
                {'role': 'system', 'content': 'You are helpful'},
                {'role': 'assistant', 'content': 'Hi there'}
            ]

            result, tool_calls = provider.generate_with_conversation(
                'custom-model',
                messages,
                None,
                MockResponseSchema
            )

            provider.generate_text.assert_called_once_with('custom-model', '')
            assert result == '{"answer": "response"}'
            assert tool_calls == []

    def test_generate_with_conversation_empty_messages(self):
        with patch.object(CustomProvider, '__init__', lambda self, api_key, config=None: None):
            provider = CustomProvider('test_api_key')
            provider.generate_text = Mock(return_value='{"answer": "response"}')

            messages = []

            result, tool_calls = provider.generate_with_conversation(
                'custom-model',
                messages,
                None,
                MockResponseSchema
            )

            provider.generate_text.assert_called_once_with('custom-model', '')
            assert result == '{"answer": "response"}'
            assert tool_calls == []

    def test_validate_connection_raises_not_implemented(self):
        with patch.object(CustomProvider, '__init__', lambda self, api_key, config=None: None):
            provider = CustomProvider('test_api_key')

            with pytest.raises(NotImplementedError) as exc_info:
                provider.validate_connection()

            assert "Not implemented" in str(exc_info.value)

    def test_get_models_raises_not_implemented(self):
        with patch.object(CustomProvider, '__init__', lambda self, api_key, config=None: None):
            provider = CustomProvider('test_api_key')

            with pytest.raises(NotImplementedError) as exc_info:
                provider.get_models()

            assert "Not implemented" in str(exc_info.value)

    def test_embed_raises_not_implemented(self):
        with patch.object(CustomProvider, '__init__', lambda self, api_key, config=None: None):
            provider = CustomProvider('test_api_key')

            with pytest.raises(NotImplementedError) as exc_info:
                provider.embed('embedding-model', ['test text'])

            assert "Not implemented" in str(exc_info.value)
