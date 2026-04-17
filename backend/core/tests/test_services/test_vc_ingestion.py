import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime

from core.services.vc_ingestion import VCIngestionService


@pytest.mark.unit
class TestVCIngestionServiceInit:
    @patch('core.services.vc_ingestion.VCProviderRegistry')
    def test_init_with_provider_name(self, mock_registry):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        mock_provider = Mock()
        mock_registry.get_provider.return_value = mock_provider
        
        service = VCIngestionService(mock_app_integration, provider_name='github')
        
        assert service.app_integration == mock_app_integration
        assert service.provider_name == 'github'

    @patch('core.services.vc_ingestion.VCProviderRegistry')
    def test_init_without_provider_name(self, mock_registry):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {'provider': 'gitlab'}
        mock_app_integration.integration.credentials = '{}'
        
        mock_provider = Mock()
        mock_registry.get_provider.return_value = mock_provider
        
        service = VCIngestionService(mock_app_integration)
        
        assert service.provider_name == 'gitlab'


@pytest.mark.unit
class TestDetectProvider:
    def test_detect_provider_from_metadata(self):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {'provider': 'bitbucket'}
        
        service = VCIngestionService.__new__(VCIngestionService)
        service.app_integration = mock_app_integration
        
        result = service._detect_provider()
        
        assert result == 'bitbucket'

    def test_detect_provider_default(self):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        
        service = VCIngestionService.__new__(VCIngestionService)
        service.app_integration = mock_app_integration
        
        result = service._detect_provider()
        
        assert result == 'github_graphql'


@pytest.mark.unit
class TestGetOrCreateRepository:
    @patch('core.services.vc_ingestion.VCRepository')
    def test_get_or_create_repository_new(self, mock_vc_repo_class):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        mock_provider = Mock()
        mock_provider.get_repository_info.return_value = {
            'id': '123',
            'description': 'Test repo',
            'url': 'https://github.com/test/repo',
            'is_private': False,
            'default_branch': 'main'
        }
        
        mock_repo = Mock()
        mock_repo.id = 1
        mock_repo.full_name = 'test/repo'
        mock_vc_repo_class.objects.get_or_create.return_value = (mock_repo, True)
        
        service = VCIngestionService(mock_app_integration)
        service.provider = mock_provider
        
        result = service._get_or_create_repository('test', 'repo')
        
        assert result == mock_repo
        mock_vc_repo_class.objects.get_or_create.assert_called_once()

    @patch('core.services.vc_ingestion.VCRepository')
    def test_get_or_create_repository_existing(self, mock_vc_repo_class):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        mock_provider = Mock()
        
        mock_repo = Mock()
        mock_repo.id = 1
        mock_repo.full_name = 'test/repo'
        mock_vc_repo_class.objects.get_or_create.return_value = (mock_repo, False)
        
        service = VCIngestionService(mock_app_integration)
        service.provider = mock_provider
        
        result = service._get_or_create_repository('test', 'repo')
        
        assert result == mock_repo
        mock_provider.get_repository_info.assert_not_called()


@pytest.mark.unit
class TestIngestSingleIssue:
    @patch('core.services.vc_ingestion.transaction')
    @patch('core.services.vc_ingestion.VCIssue')
    def test_ingest_single_issue_success(self, mock_issue_class, mock_transaction):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        mock_provider = Mock()
        mock_provider._parse_datetime.return_value = datetime.now()
        
        mock_repository = Mock()
        mock_repository.repo_owner = 'test'
        mock_repository.name = 'repo'
        
        mock_issue = Mock()
        mock_issue.number = 1
        mock_issue.comments = Mock()
        mock_issue.comments.all.return_value = []
        mock_issue_class.objects.update_or_create.return_value = (mock_issue, True)
        
        mock_quality_filter = Mock()
        mock_quality_filter.remove_emojis.return_value = 'cleaned body'
        
        service = VCIngestionService(mock_app_integration)
        service.provider = mock_provider
        service.repository = mock_repository
        service.quality_filter = mock_quality_filter
        
        issue_data = {
            'id': '123',
            'number': 1,
            'title': 'Test issue',
            'body': 'Test body',
            'state': 'open',
            'author': 'testuser',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'url': 'https://github.com/test/repo/issues/1'
        }
        
        service._ingest_single_issue(issue_data)
        
        mock_issue_class.objects.update_or_create.assert_called_once()


@pytest.mark.unit
class TestIngestSinglePullRequest:
    @patch('core.services.vc_ingestion.transaction')
    @patch('core.services.vc_ingestion.VCPullRequest')
    def test_ingest_single_pull_request_success(self, mock_pr_class, mock_transaction):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        mock_provider = Mock()
        mock_provider._parse_datetime.return_value = datetime.now()
        mock_provider.get_pull_request_comments.return_value = []
        mock_provider.get_pull_request_files.return_value = []
        
        mock_repository = Mock()
        mock_repository.repo_owner = 'test'
        mock_repository.name = 'repo'
        
        mock_pr = Mock()
        mock_pr.number = 1
        mock_pr_class.objects.update_or_create.return_value = (mock_pr, True)
        
        mock_quality_filter = Mock()
        mock_quality_filter.remove_emojis.return_value = 'cleaned body'
        
        service = VCIngestionService(mock_app_integration)
        service.provider = mock_provider
        service.repository = mock_repository
        service.quality_filter = mock_quality_filter
        
        pr_data = {
            'id': '123',
            'number': 1,
            'title': 'Test PR',
            'body': 'Test body',
            'state': 'open',
            'author': 'testuser',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'url': 'https://github.com/test/repo/pull/1'
        }
        
        service._ingest_single_pull_request(pr_data)
        
        mock_pr_class.objects.update_or_create.assert_called_once()


@pytest.mark.unit
class TestCreateKnowledgeBaseContent:
    def test_create_knowledge_base_content_no_repository(self):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        service = VCIngestionService(mock_app_integration)
        service.repository = None
        
        result = service._create_knowledge_base_content()
        
        assert result == ""

    def test_create_knowledge_base_content_with_repository(self):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        mock_repository = Mock()
        mock_repository.full_name = 'test/repo'
        mock_repository.description = 'Test description'
        mock_repository.issues = Mock()
        mock_repository.issues.all.return_value = []
        mock_repository.pull_requests = Mock()
        mock_repository.pull_requests.all.return_value = []
        
        service = VCIngestionService(mock_app_integration)
        service.repository = mock_repository
        
        result = service._create_knowledge_base_content()
        
        assert 'Repository: test/repo' in result
        assert 'Description: Test description' in result

    def test_create_knowledge_base_content_with_issues(self):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        mock_issue = Mock()
        mock_issue.number = 1
        mock_issue.title = 'Test issue'
        mock_issue.state = 'open'
        mock_issue.author = 'testuser'
        mock_issue.body = 'Test body'
        mock_issue.labels = ['bug']
        mock_issue.comments = Mock()
        mock_issue.comments.all.return_value = []
        
        mock_repository = Mock()
        mock_repository.full_name = 'test/repo'
        mock_repository.description = 'Test description'
        mock_repository.issues = Mock()
        mock_repository.issues.all.return_value = [mock_issue]
        mock_repository.pull_requests = Mock()
        mock_repository.pull_requests.all.return_value = []
        
        service = VCIngestionService(mock_app_integration)
        service.repository = mock_repository
        
        result = service._create_knowledge_base_content()
        
        assert '## Issues' in result
        assert 'Issue #1: Test issue' in result


@pytest.mark.unit
class TestIngestRepository:
    @patch('core.services.vc_ingestion.VCIngestionService._ingest_to_knowledge_base')
    @patch('core.services.vc_ingestion.VCIngestionService._ingest_pull_requests')
    @patch('core.services.vc_ingestion.VCIngestionService._ingest_issues')
    @patch('core.services.vc_ingestion.VCIngestionService._get_or_create_repository')
    def test_ingest_repository_success(self, mock_get_repo, mock_ingest_issues, mock_ingest_prs, mock_ingest_kb):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        mock_provider = Mock()
        mock_provider.close = Mock()
        
        mock_repository = Mock()
        mock_repository.id = 1
        mock_repository.full_name = 'test/repo'
        mock_repository.ingestion_status = 'completed'
        
        mock_get_repo.return_value = mock_repository
        
        service = VCIngestionService(mock_app_integration)
        service.provider = mock_provider
        service.provider_name = 'github'
        
        service.ingest_repository('test', 'repo')
        
        mock_get_repo.assert_called_once_with('test', 'repo')
        mock_ingest_issues.assert_called_once()
        mock_ingest_prs.assert_called_once()
        mock_ingest_kb.assert_called_once()
        assert mock_repository.ingestion_status == 'completed'

    @patch('core.services.vc_ingestion.VCIngestionService._get_or_create_repository')
    def test_ingest_repository_exception(self, mock_get_repo):
        mock_app_integration = Mock()
        mock_app_integration.metadata = {}
        mock_app_integration.integration.credentials = '{}'
        
        mock_provider = Mock()
        mock_provider.close = Mock()
        
        mock_repository = Mock()
        mock_repository.ingestion_status = 'running'
        mock_get_repo.return_value = mock_repository
        mock_get_repo.side_effect = Exception('Test error')
        
        service = VCIngestionService(mock_app_integration)
        service.provider = mock_provider
        service.provider_name = 'github'
        service.repository = mock_repository
        
        with pytest.raises(Exception):
            service.ingest_repository('test', 'repo')
        
        assert mock_repository.ingestion_status == 'failed'
        mock_provider.close.assert_called_once()
