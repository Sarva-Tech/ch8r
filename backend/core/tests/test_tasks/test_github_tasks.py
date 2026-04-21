import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from core.tasks.github_tasks import send_github_ingestion_update, ingest_github_repository_task


@pytest.mark.unit
class TestSendGithubIngestionUpdate:
    @patch('core.tasks.github_tasks.get_channel_layer')
    @patch('core.tasks.github_tasks.async_to_sync')
    def test_send_github_ingestion_update_success(self, mock_async_to_sync, mock_get_channel_layer):
        mock_repository = Mock()
        mock_repository.id = 1
        mock_repository.full_name = 'owner/repo'
        mock_repository.app_integration.application.owner.id = 123

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        def mock_async_to_sync_func(func):
            return func
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        send_github_ingestion_update(mock_repository, 'completed')

        mock_async_to_sync.assert_called_once()
        mock_channel_layer.group_send.assert_called_once()

    @patch('core.tasks.github_tasks.get_channel_layer')
    @patch('core.tasks.github_tasks.async_to_sync')
    def test_send_github_ingestion_update_failure(self, mock_async_to_sync, mock_get_channel_layer):
        mock_repository = Mock()
        mock_repository.full_name = 'owner/repo'

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        def mock_async_to_sync_func(func):
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                raise Exception('WebSocket error')
            return wrapper
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        send_github_ingestion_update(mock_repository, 'completed')

        mock_channel_layer.group_send.assert_called_once()


@pytest.mark.unit
class TestIngestGithubRepositoryTask:
    @patch('core.tasks.github_tasks.VCRepository')
    @patch('core.tasks.github_tasks.send_github_ingestion_update')
    @patch('core.tasks.github_tasks.GitHubGraphQLIngestionService')
    @patch('core.tasks.github_tasks.AppIntegration')
    def test_ingest_github_repository_task_success(self, mock_app_integration_class, mock_ingestion_service_class, mock_send_update, mock_vc_repository_class):
        mock_app_integration = Mock()
        mock_app_integration.application.name = 'test_app'
        mock_app_integration.application.owner.id = 123
        mock_app_integration_class.objects.select_related.return_value.get.return_value = mock_app_integration

        mock_ingestion_service = Mock()
        mock_ingestion_service_class.return_value = mock_ingestion_service

        mock_repository = Mock()
        mock_repository.id = 1
        mock_repository.full_name = 'owner/repo'
        mock_vc_repository_class.objects.get.return_value = mock_repository

        result = ingest_github_repository_task(1, 'owner', 'repo')

        assert result['status'] == 'success'
        assert result['repository'] == 'owner/repo'
        assert 'completed_at' in result
        mock_ingestion_service.ingest_repository.assert_called_once_with('owner', 'repo', None)
        mock_send_update.assert_called_once_with(mock_repository, 'completed')

    @patch('core.tasks.github_tasks.AppIntegration')
    def test_ingest_github_repository_task_app_integration_not_found(self, mock_app_integration_class):
        mock_app_integration_class.objects.select_related.return_value.get.side_effect = Exception('AppIntegration not found')

        with pytest.raises(Exception):
            ingest_github_repository_task(1, 'owner', 'repo')

    @patch('core.tasks.github_tasks.VCRepository')
    @patch('core.tasks.github_tasks.send_github_ingestion_update')
    @patch('core.tasks.github_tasks.GitHubGraphQLIngestionService')
    @patch('core.tasks.github_tasks.AppIntegration')
    def test_ingest_github_repository_task_with_since_parameter(self, mock_app_integration_class, mock_ingestion_service_class, mock_send_update, mock_vc_repository_class):
        mock_app_integration = Mock()
        mock_app_integration.application.name = 'test_app'
        mock_app_integration.application.owner.id = 123
        mock_app_integration_class.objects.select_related.return_value.get.return_value = mock_app_integration

        mock_ingestion_service = Mock()
        mock_ingestion_service_class.return_value = mock_ingestion_service

        mock_repository = Mock()
        mock_repository.id = 1
        mock_repository.full_name = 'owner/repo'
        mock_vc_repository_class.objects.get.return_value = mock_repository

        result = ingest_github_repository_task(1, 'owner', 'repo', '2024-01-01')

        assert result['status'] == 'success'
        mock_ingestion_service.ingest_repository.assert_called_once_with('owner', 'repo', '2024-01-01')
