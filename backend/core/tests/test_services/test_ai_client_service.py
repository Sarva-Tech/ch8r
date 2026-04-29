import pytest
from unittest.mock import Mock, patch

from core.services.ai_client_service import AIClientService


@pytest.mark.unit
class TestAIClientService:
    def test_init(self):
        service = AIClientService()

        assert service.provider_factory is not None

    @patch('core.services.ai_client_service.AIProviderFactory')
    def test_get_client_and_model_with_ai_provider_id(self, mock_factory_class):
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory

        mock_provider = Mock()
        mock_factory.create_provider.return_value = mock_provider

        mock_ai_provider = Mock()
        mock_ai_provider.provider = 'gemini'
        mock_ai_provider.provider_api_key = 'test_key'
        mock_ai_provider.metadata = {'model': 'gemini-pro'}

        with patch('core.services.ai_client_service.AIProvider.objects.get', return_value=mock_ai_provider):
            service = AIClientService()
            provider, model = service.get_client_and_model(
                app=Mock(),
                ai_provider_id=1,
                model='custom-model'
            )

            mock_factory.create_provider.assert_called_once_with(
                provider_type='gemini',
                api_key='test_key',
                config={'model': 'gemini-pro'}
            )
            assert provider == mock_provider
            assert model == 'custom-model'

    @patch('core.services.ai_client_service.AIProviderFactory')
    def test_get_client_and_model_with_invalid_ai_provider_id(self, mock_factory_class):
        from core.models import AIProvider

        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory

        with patch('core.services.ai_client_service.AIProvider.objects.get', side_effect=AIProvider.DoesNotExist()):
            service = AIClientService()
            provider, model = service.get_client_and_model(
                app=Mock(),
                ai_provider_id=999
            )

            assert provider is None
            assert model is None

    @patch('core.services.ai_client_service.AIProviderFactory')
    def test_get_client_and_model_without_ai_provider_id_with_config(self, mock_factory_class):
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory

        mock_provider = Mock()
        mock_provider.get_models.return_value = [{'name': 'gemini-pro'}]
        mock_factory.create_provider.return_value = mock_provider

        mock_ai_provider = Mock()
        mock_ai_provider.provider = 'gemini'
        mock_ai_provider.provider_api_key = 'test_key'
        mock_ai_provider.metadata = {}

        mock_config = Mock()
        mock_config.ai_provider = mock_ai_provider
        mock_config.external_model_id = 'gemini-pro'

        with patch.object(AIClientService, '_get_app_provider_config', return_value=mock_config):
            service = AIClientService()
            provider, model = service.get_client_and_model(
                app=Mock(),
                context='response',
                capability='text'
            )

            mock_factory.create_provider.assert_called_once()
            assert provider == mock_provider
            assert model == 'gemini-pro'

    @patch('core.services.ai_client_service.AIProviderFactory')
    def test_get_client_and_model_without_ai_provider_id_without_config(self, mock_factory_class):
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory

        with patch.object(AIClientService, '_get_app_provider_config', return_value=None):
            service = AIClientService()
            provider, model = service.get_client_and_model(
                app=Mock(),
                context='response',
                capability='text'
            )

            assert provider is None
            assert model is None

    @patch('core.services.ai_client_service.AIProviderFactory')
    def test_get_client_and_model_fallback_to_default_model(self, mock_factory_class):
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory

        mock_provider = Mock()
        mock_provider.get_models.return_value = []
        mock_factory.create_provider.return_value = mock_provider

        mock_ai_provider = Mock()
        mock_ai_provider.provider = 'gemini'
        mock_ai_provider.provider_api_key = 'test_key'
        mock_ai_provider.metadata = {}

        mock_config = Mock()
        mock_config.ai_provider = mock_ai_provider
        mock_config.external_model_id = None

        with patch.object(AIClientService, '_get_app_provider_config', return_value=mock_config):
            service = AIClientService()
            provider, model = service.get_client_and_model(
                app=Mock(),
                context='response',
                capability='text'
            )

            assert provider == mock_provider
            assert model == 'default'

    @patch('core.services.ai_client_service.AIProviderFactory')
    def test_get_client_and_model_get_models_exception(self, mock_factory_class):
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory

        mock_provider = Mock()
        mock_provider.get_models.side_effect = Exception("API error")
        mock_factory.create_provider.return_value = mock_provider

        mock_ai_provider = Mock()
        mock_ai_provider.provider = 'gemini'
        mock_ai_provider.provider_api_key = 'test_key'
        mock_ai_provider.metadata = {}

        mock_config = Mock()
        mock_config.ai_provider = mock_ai_provider
        mock_config.external_model_id = None

        with patch.object(AIClientService, '_get_app_provider_config', return_value=mock_config):
            service = AIClientService()
            provider, model = service.get_client_and_model(
                app=Mock(),
                context='response',
                capability='text'
            )

            assert provider == mock_provider
            assert model == 'default'

    @patch('core.services.ai_client_service.AIProviderFactory')
    def test_get_client_and_model_uses_first_available_model(self, mock_factory_class):
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory

        mock_provider = Mock()
        mock_provider.get_models.return_value = [{'name': 'gemini-pro'}, {'name': 'gemini-flash'}]
        mock_factory.create_provider.return_value = mock_provider

        mock_ai_provider = Mock()
        mock_ai_provider.provider = 'gemini'
        mock_ai_provider.provider_api_key = 'test_key'
        mock_ai_provider.metadata = {}

        mock_config = Mock()
        mock_config.ai_provider = mock_ai_provider
        mock_config.external_model_id = None

        with patch.object(AIClientService, '_get_app_provider_config', return_value=mock_config):
            service = AIClientService()
            provider, model = service.get_client_and_model(
                app=Mock(),
                context='response',
                capability='text'
            )

            assert provider == mock_provider
            assert model == 'gemini-pro'

    @patch('core.services.ai_client_service.AppAIProvider.objects')
    def test_get_app_provider_config_builtin_first(self, mock_objects):
        mock_app = Mock()
        mock_config = Mock()
        mock_config.ai_provider = Mock()

        mock_queryset = Mock()
        mock_queryset.select_related.return_value.first.return_value = mock_config
        mock_objects.filter.return_value = mock_queryset

        service = AIClientService()
        config = service._get_app_provider_config(mock_app, 'response', 'text')

        mock_objects.filter.assert_called_once_with(
            application=mock_app,
            context='response',
            capability='text',
            is_active=True,
            ai_provider__is_builtin=True
        )
        assert config == mock_config

    @patch('core.services.ai_client_service.AppAIProvider.objects')
    def test_get_app_provider_config_fallback_to_non_builtin(self, mock_objects):
        mock_app = Mock()
        mock_config = Mock()
        mock_config.ai_provider = Mock()

        mock_queryset_builtin = Mock()
        mock_queryset_builtin.select_related.return_value.first.return_value = None

        mock_queryset_fallback = Mock()
        mock_queryset_fallback.select_related.return_value.order_by.return_value.first.return_value = mock_config

        mock_objects.filter.side_effect = [mock_queryset_builtin, mock_queryset_fallback]

        service = AIClientService()
        config = service._get_app_provider_config(mock_app, 'response', 'text')

        assert mock_objects.filter.call_count == 2
        assert config == mock_config

    @patch('core.services.ai_client_service.AppAIProvider.objects')
    def test_get_app_provider_config_no_config_found(self, mock_objects):
        mock_app = Mock()

        mock_queryset_builtin = Mock()
        mock_queryset_builtin.select_related.return_value.first.return_value = None

        mock_queryset_fallback = Mock()
        mock_queryset_fallback.select_related.return_value.order_by.return_value.first.return_value = None

        mock_objects.filter.side_effect = [mock_queryset_builtin, mock_queryset_fallback]

        service = AIClientService()
        config = service._get_app_provider_config(mock_app, 'response', 'text')

        assert config is None

    @patch('core.services.ai_client_service.AppAIProvider.objects')
    def test_get_app_provider_config_with_different_context_and_capability(self, mock_objects):
        mock_app = Mock()
        mock_config = Mock()
        mock_config.ai_provider = Mock()

        mock_queryset = Mock()
        mock_queryset.select_related.return_value.first.return_value = mock_config
        mock_objects.filter.return_value = mock_queryset

        service = AIClientService()
        config = service._get_app_provider_config(mock_app, 'embedding', 'embedding')

        mock_objects.filter.assert_called_once_with(
            application=mock_app,
            context='embedding',
            capability='embedding',
            is_active=True,
            ai_provider__is_builtin=True
        )
        assert config == mock_config
