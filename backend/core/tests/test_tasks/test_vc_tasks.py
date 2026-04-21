import pytest
from unittest.mock import Mock, patch

from core.tasks.vc_tasks import send_vc_ingestion_update, ingest_vc_repository_task
from core.consts import LIVE_UPDATES_PREFIX, DASHBOARD_USER_ID_PREFIX


@pytest.mark.unit
class TestSendVcIngestionUpdate:
    @patch('core.tasks.vc_tasks.async_to_sync')
    @patch('core.tasks.vc_tasks.get_channel_layer')
    def test_send_vc_ingestion_update_success(self, mock_get_channel_layer, mock_async_to_sync):
        mock_repository = Mock()
        mock_repository.id = 1
        mock_repository.full_name = 'owner/repo'
        mock_repository.provider = 'github_graphql'
        mock_repository.app_integration.application.owner.id = 123

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        def mock_async_to_sync_func(func):
            return func
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        send_vc_ingestion_update(mock_repository, 'completed')

        mock_async_to_sync.assert_called_once()
        mock_channel_layer.group_send.assert_called_once()
        call_args = mock_channel_layer.group_send.call_args
        assert call_args[0][0] == f'{LIVE_UPDATES_PREFIX}_{DASHBOARD_USER_ID_PREFIX}_123'
        assert call_args[0][1]['type'] == 'send.kb.updates'
        assert call_args[0][1]['data']['id'] == '1'
        assert call_args[0][1]['data']['repository'] == 'owner/repo'
        assert call_args[0][1]['data']['provider'] == 'github_graphql'
        assert call_args[0][1]['data']['ingestion_status'] == 'completed'

    @patch('core.tasks.vc_tasks.get_channel_layer')
    def test_send_vc_ingestion_update_channel_layer_none(self, mock_get_channel_layer):
        mock_repository = Mock()
        mock_repository.full_name = 'owner/repo'
        mock_get_channel_layer.return_value = None

        send_vc_ingestion_update(mock_repository, 'completed')

        mock_get_channel_layer.assert_called_once()

    @patch('core.tasks.vc_tasks.async_to_sync')
    @patch('core.tasks.vc_tasks.get_channel_layer')
    def test_send_vc_ingestion_update_exception(self, mock_get_channel_layer, mock_async_to_sync):
        mock_repository = Mock()
        mock_repository.full_name = 'owner/repo'
        mock_repository.app_integration.application.owner.id = 123

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        def mock_async_to_sync_func(func):
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                raise Exception('WebSocket error')
            return wrapper
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        send_vc_ingestion_update(mock_repository, 'completed')

        mock_channel_layer.group_send.assert_called_once()


@pytest.mark.unit
class TestIngestVcRepositoryTask:
    @patch('core.tasks.vc_tasks.send_vc_ingestion_update')
    @patch('core.tasks.vc_tasks.VCRepository')
    @patch('core.tasks.vc_tasks.VCIngestionService')
    @patch('core.tasks.vc_tasks.AppIntegration')
    @patch('core.tasks.vc_tasks.timezone')
    def test_ingest_vc_repository_task_success(self, mock_timezone, mock_app_integration_class, mock_vc_service_class, mock_vc_repository_class, mock_send_update):
        mock_timezone.now.return_value.isoformat.return_value = '2024-01-01T00:00:00Z'

        mock_app_integration = Mock()
        mock_app_integration.application.name = 'Test App'
        mock_app_integration.application.owner.id = 123
        mock_app_integration_class.objects.select_related.return_value.get.return_value = mock_app_integration

        mock_vc_service = Mock()
        mock_vc_service_class.return_value = mock_vc_service

        mock_repository = Mock()
        mock_repository.id = 1
        mock_repository.full_name = 'owner/repo'
        mock_repository.provider = 'github_graphql'
        mock_vc_repository_class.objects.get.return_value = mock_repository

        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3

        result = ingest_vc_repository_task(1, 'owner', 'repo', None, 'github_graphql')

        assert result['status'] == 'success'
        assert result['repository'] == 'owner/repo'
        assert result['provider'] == 'github_graphql'
        mock_vc_service.ingest_repository.assert_called_once_with('owner', 'repo', None)
        mock_send_update.assert_called_once_with(mock_repository, 'completed')

    @patch('core.tasks.vc_tasks.send_vc_ingestion_update')
    @patch('core.tasks.vc_tasks.VCRepository')
    @patch('core.tasks.vc_tasks.VCIngestionService')
    @patch('core.tasks.vc_tasks.AppIntegration')
    @patch('core.tasks.vc_tasks.timezone')
    def test_ingest_vc_repository_task_success_repository_not_found(self, mock_timezone, mock_app_integration_class, mock_vc_service_class, mock_vc_repository_class, mock_send_update):
        mock_timezone.now.return_value.isoformat.return_value = '2024-01-01T00:00:00Z'

        mock_app_integration = Mock()
        mock_app_integration.application.name = 'Test App'
        mock_app_integration_class.objects.select_related.return_value.get.return_value = mock_app_integration

        mock_vc_service = Mock()
        mock_vc_service_class.return_value = mock_vc_service

        mock_vc_repository_class.DoesNotExist = Exception
        mock_vc_repository_class.objects.get.side_effect = Exception('Not found')

        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3

        result = ingest_vc_repository_task(1, 'owner', 'repo', None, 'github_graphql')

        assert result['status'] == 'success'
        mock_send_update.assert_not_called()

    @patch('core.tasks.vc_tasks.VCIngestionService')
    @patch('core.tasks.vc_tasks.AppIntegration')
    def test_ingest_vc_repository_task_app_integration_not_found(self, mock_app_integration_class, mock_vc_service_class):
        mock_app_integration_class.DoesNotExist = Exception
        mock_app_integration_class.objects.select_related.return_value.get.side_effect = Exception('Not found')

        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3

        with pytest.raises(Exception):
            ingest_vc_repository_task(1, 'owner', 'repo', None, 'github_graphql')

    @patch('core.tasks.kb.send_kb_update')
    @patch('core.tasks.vc_tasks.send_vc_ingestion_update')
    @patch('core.tasks.vc_tasks.VCRepository')
    @patch('core.tasks.vc_tasks.VCIngestionService')
    @patch('core.tasks.vc_tasks.AppIntegration')
    def test_ingest_vc_repository_task_ingestion_failure_with_retry(self, mock_app_integration_class, mock_vc_service_class, mock_vc_repository_class, mock_send_update, mock_send_kb_update):
        mock_app_integration = Mock()
        mock_app_integration.application.name = 'Test App'
        mock_app_integration.application.owner.id = 123
        mock_app_integration_class.objects.select_related.return_value.get.return_value = mock_app_integration

        mock_vc_service = Mock()
        mock_vc_service_class.return_value = mock_vc_service
        mock_vc_service.ingest_repository.side_effect = Exception('Ingestion error')

        mock_repository = Mock()
        mock_repository.full_name = 'owner/repo'
        mock_repository.app_integration.application = mock_app_integration.application
        mock_vc_repository_class.objects.get.return_value = mock_repository

        mock_kb = Mock()
        mock_kb.uuid = 'kb-uuid'
        mock_kb_class = Mock()
        mock_kb_class.objects.filter.return_value.first.return_value = mock_kb

        with patch('core.models.KnowledgeBase', mock_kb_class):
            with pytest.raises(Exception):
                ingest_vc_repository_task(1, 'owner', 'repo', None, 'github_graphql')

    @patch('core.tasks.vc_tasks.send_vc_ingestion_update')
    @patch('core.tasks.vc_tasks.VCRepository')
    @patch('core.tasks.vc_tasks.VCIngestionService')
    @patch('core.tasks.vc_tasks.AppIntegration')
    def test_ingest_vc_repository_task_ingestion_failure_no_kb(self, mock_app_integration_class, mock_vc_service_class, mock_vc_repository_class, mock_send_update):
        mock_app_integration = Mock()
        mock_app_integration.application.name = 'Test App'
        mock_app_integration.application.owner.id = 123
        mock_app_integration_class.objects.select_related.return_value.get.return_value = mock_app_integration

        mock_vc_service = Mock()
        mock_vc_service_class.return_value = mock_vc_service
        mock_vc_service.ingest_repository.side_effect = Exception('Ingestion error')

        mock_repository = Mock()
        mock_repository.full_name = 'owner/repo'
        mock_repository.app_integration.application = mock_app_integration.application
        mock_vc_repository_class.objects.get.return_value = mock_repository

        mock_kb_class = Mock()
        mock_kb_class.objects.filter.return_value.first.return_value = None

        with patch('core.models.KnowledgeBase', mock_kb_class):
            with pytest.raises(Exception):
                ingest_vc_repository_task(1, 'owner', 'repo', None, 'github_graphql')

    @patch('core.tasks.vc_tasks.send_vc_ingestion_update')
    @patch('core.tasks.vc_tasks.VCRepository')
    @patch('core.tasks.vc_tasks.VCIngestionService')
    @patch('core.tasks.vc_tasks.AppIntegration')
    def test_ingest_vc_repository_task_with_since_parameter(self, mock_app_integration_class, mock_vc_service_class, mock_vc_repository_class, mock_send_update):
        mock_app_integration = Mock()
        mock_app_integration.application.name = 'Test App'
        mock_app_integration.application.owner.id = 123
        mock_app_integration_class.objects.select_related.return_value.get.return_value = mock_app_integration

        mock_vc_service = Mock()
        mock_vc_service_class.return_value = mock_vc_service

        mock_repository = Mock()
        mock_repository.id = 1
        mock_repository.full_name = 'owner/repo'
        mock_repository.provider = 'github_graphql'
        mock_vc_repository_class.objects.get.return_value = mock_repository

        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3

        result = ingest_vc_repository_task(1, 'owner', 'repo', '2024-01-01', 'github_graphql')

        assert result['status'] == 'success'
        mock_vc_service.ingest_repository.assert_called_once_with('owner', 'repo', '2024-01-01')
        mock_send_update.assert_called_once_with(mock_repository, 'completed')

    @patch('core.tasks.vc_tasks.send_vc_ingestion_update')
    @patch('core.tasks.vc_tasks.VCRepository')
    @patch('core.tasks.vc_tasks.VCIngestionService')
    @patch('core.tasks.vc_tasks.AppIntegration')
    @patch('core.tasks.vc_tasks.timezone')
    def test_ingest_vc_repository_task_with_custom_provider(self, mock_timezone, mock_app_integration_class, mock_vc_service_class, mock_vc_repository_class, mock_send_update):
        mock_timezone.now.return_value.isoformat.return_value = '2024-01-01T00:00:00Z'

        mock_app_integration = Mock()
        mock_app_integration.application.name = 'Test App'
        mock_app_integration.application.owner.id = 123
        mock_app_integration_class.objects.select_related.return_value.get.return_value = mock_app_integration

        mock_vc_service = Mock()
        mock_vc_service_class.return_value = mock_vc_service

        mock_repository = Mock()
        mock_repository.id = 1
        mock_repository.full_name = 'owner/repo'
        mock_repository.provider = 'gitlab'
        mock_vc_repository_class.objects.get.return_value = mock_repository

        mock_task = Mock()
        mock_task.request.retries = 0
        mock_task.max_retries = 3

        result = ingest_vc_repository_task(1, 'owner', 'repo', None, 'gitlab')

        assert result['status'] == 'success'
        assert result['provider'] == 'gitlab'
        mock_vc_service_class.assert_called_once_with(mock_app_integration, provider_name='gitlab')
        mock_send_update.assert_called_once_with(mock_repository, 'completed')
