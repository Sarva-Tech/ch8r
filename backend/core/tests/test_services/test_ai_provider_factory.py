import pytest
from unittest.mock import Mock, patch

from core.services.factories.ai_provider_factory import AIProviderFactory


@pytest.mark.unit
class TestAIProviderFactory:
    def test_provider_classes_contains_expected_providers(self):
        assert 'gemini' in AIProviderFactory.PROVIDER_CLASSES
        assert 'custom' in AIProviderFactory.PROVIDER_CLASSES

    def test_create_provider_gemini(self):
        mock_provider = Mock()
        mock_gemini_class = Mock(return_value=mock_provider)

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'gemini': mock_gemini_class}):
            provider = AIProviderFactory.create_provider('gemini', 'test_api_key', {'model': 'gemini-pro'})

            mock_gemini_class.assert_called_once_with(api_key='test_api_key', config={'model': 'gemini-pro'})
            assert provider == mock_provider

    def test_create_provider_custom(self):
        mock_provider = Mock()
        mock_custom_class = Mock(return_value=mock_provider)

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'custom': mock_custom_class}):
            provider = AIProviderFactory.create_provider('custom', 'test_api_key', {'base_url': 'https://api.example.com'})

            mock_custom_class.assert_called_once_with(api_key='test_api_key', config={'base_url': 'https://api.example.com'})
            assert provider == mock_provider

    def test_create_provider_case_insensitive(self):
        mock_provider = Mock()
        mock_gemini_class = Mock(return_value=mock_provider)

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'gemini': mock_gemini_class}):
            provider = AIProviderFactory.create_provider('GEMINI', 'test_api_key')

            mock_gemini_class.assert_called_once_with(api_key='test_api_key', config={})
            assert provider == mock_provider

    def test_create_provider_with_none_config(self):
        mock_provider = Mock()
        mock_gemini_class = Mock(return_value=mock_provider)

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'gemini': mock_gemini_class}):
            provider = AIProviderFactory.create_provider('gemini', 'test_api_key', None)

            mock_gemini_class.assert_called_once_with(api_key='test_api_key', config={})
            assert provider == mock_provider

    def test_create_provider_unsupported_type(self):
        with pytest.raises(ValueError) as exc_info:
            AIProviderFactory.create_provider('unsupported_provider', 'test_api_key')

        assert "Unsupported provider type: unsupported_provider" in str(exc_info.value)
        assert "Supported providers:" in str(exc_info.value)

    def test_create_provider_initialization_error(self):
        mock_gemini_class = Mock(side_effect=Exception("Initialization failed"))

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'gemini': mock_gemini_class}):
            with pytest.raises(ValueError) as exc_info:
                AIProviderFactory.create_provider('gemini', 'test_api_key')

            assert "Failed to create gemini provider: Initialization failed" in str(exc_info.value)

    def test_validate_provider_gemini(self):
        mock_provider = Mock()
        mock_provider.validate_connection.return_value = (True, [{'test': 'result'}])
        mock_gemini_class = Mock(return_value=mock_provider)

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'gemini': mock_gemini_class}):
            is_valid, result = AIProviderFactory.validate_provider('gemini', 'test_api_key', {'model': 'gemini-pro'})

            assert is_valid is True
            assert result == [{'test': 'result'}]
            mock_provider.validate_connection.assert_called_once()

    def test_validate_provider_custom(self):
        mock_provider = Mock()
        mock_provider.validate_connection.return_value = (False, [])
        mock_custom_class = Mock(return_value=mock_provider)

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'custom': mock_custom_class}):
            is_valid, result = AIProviderFactory.validate_provider('custom', 'test_api_key')

            assert is_valid is False
            assert result == []
            mock_provider.validate_connection.assert_called_once()

    def test_validate_provider_case_insensitive(self):
        mock_provider = Mock()
        mock_provider.validate_connection.return_value = (True, [])
        mock_gemini_class = Mock(return_value=mock_provider)

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'gemini': mock_gemini_class}):
            is_valid, result = AIProviderFactory.validate_provider('GEMINI', 'test_api_key')

            assert is_valid is True
            assert result == []

    def test_validate_provider_with_none_config(self):
        mock_provider = Mock()
        mock_provider.validate_connection.return_value = (True, [])
        mock_gemini_class = Mock(return_value=mock_provider)

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'gemini': mock_gemini_class}):
            is_valid, result = AIProviderFactory.validate_provider('gemini', 'test_api_key', None)

            assert is_valid is True
            assert result == []

    def test_validate_provider_unsupported_type(self):
        with pytest.raises(ValueError) as exc_info:
            AIProviderFactory.validate_provider('unsupported_provider', 'test_api_key')

        assert "Unsupported provider type: unsupported_provider" in str(exc_info.value)
        assert "Supported providers:" in str(exc_info.value)

    def test_validate_provider_exception_handling(self):
        mock_gemini_class = Mock(side_effect=Exception("Validation failed"))

        with patch.object(AIProviderFactory, 'PROVIDER_CLASSES', {'gemini': mock_gemini_class}):
            is_valid, result = AIProviderFactory.validate_provider('gemini', 'test_api_key')

            assert is_valid is False
            assert result == []

    def test_get_supported_providers(self):
        providers = AIProviderFactory.get_supported_providers()

        assert isinstance(providers, list)
        assert 'gemini' in providers
        assert 'custom' in providers
