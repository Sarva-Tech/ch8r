import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from core.models import AppIntegration, Application
from core.models.github_data import GitHubRepository, GitHubIssue
from core.services.github_client import GitHubAPIClient
from core.services.github_ingestion import GitHubDataIngestionService
from core.views.github_ingestion import GitHubIngestionViewSet


class GitHubAPIClientTestCase(TestCase):
    """Test cases for GitHub API client"""
    
    def setUp(self):
        self.client = GitHubAPIClient("test_token")
    
    def test_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.client.token, "test_token")
        self.assertIn("Authorization", self.client.session.headers)
        self.assertEqual(self.client.session.headers["Authorization"], "Bearer test_token")
    
    @patch('core.services.github_client.requests.Session.request')
    def test_make_request_success(self, mock_request):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": 123, "title": "Test Issue"}
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        result = self.client._make_request('GET', '/test')
        
        self.assertEqual(result["id"], 123)
        self.assertEqual(result["title"], "Test Issue")
        mock_request.assert_called_once()
    
    @patch('core.services.github_client.requests.Session.request')
    def test_make_request_rate_limit(self, mock_request):
        """Test rate limit handling"""
        # First call hits rate limit
        mock_rate_limit_response = Mock()
        mock_rate_limit_response.status_code = 403
        mock_rate_limit_response.headers = {
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(int(timezone.now().timestamp()) + 60)
        }
        mock_rate_limit_response.json.return_value = {"message": "Rate limit exceeded"}
        
        # Second call succeeds
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"id": 123}
        mock_success_response.raise_for_status.return_value = None
        
        mock_request.side_effect = [mock_rate_limit_response, mock_success_response]
        
        with patch('time.sleep'):  # Skip actual sleep
            result = self.client._make_request('GET', '/test')
        
        self.assertEqual(result["id"], 123)
        self.assertEqual(mock_request.call_count, 2)
    
    @patch('core.services.github_client.requests.Session.request')
    def test_get_repository_info(self, mock_request):
        """Test getting repository information"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "description": "Test repository",
            "private": False,
            "default_branch": "main"
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        result = self.client.get_repository_info("owner", "test-repo")
        
        self.assertEqual(result["full_name"], "owner/test-repo")
        self.assertEqual(result["description"], "Test repository")
        self.assertFalse(result["private"])


class GitHubDataIngestionServiceTestCase(TestCase):
    """Test cases for GitHub data ingestion service"""
    
    def setUp(self):
        self.user = Mock()
        self.application = Mock()
        self.application.owner = self.user
        
        self.integration = Mock()
        self.integration.config = {"token": "test_token"}
        
        self.app_integration = Mock()
        self.app_integration.integration = self.integration
        self.app_integration.app = self.application
        self.app_integration.id = 1
    
    @patch('core.services.github_ingestion.GitHubAPIClient')
    def test_get_or_create_repository_new(self, mock_client_class):
        """Test creating a new repository record"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_repo_info = {
            "description": "Test repository",
            "html_url": "https://github.com/owner/test-repo",
            "private": False,
            "default_branch": "main"
        }
        mock_client.get_repository_info.return_value = mock_repo_info
        
        service = GitHubDataIngestionService(self.app_integration)
        repository = service._get_or_create_repository("owner", "test-repo")
        
        self.assertEqual(repository.full_name, "owner/test-repo")
        self.assertEqual(repository.name, "test-repo")
        self.assertEqual(repository.owner, "owner")
        self.assertEqual(repository.description, "Test repository")
        self.assertFalse(repository.is_private)
        self.assertEqual(repository.default_branch, "main")
    
    @patch('core.services.github_ingestion.GitHubAPIClient')
    def test_ingest_single_issue(self, mock_client_class):
        """Test ingesting a single issue"""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock repository
        repository = GitHubRepository(
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            app_integration=self.app_integration
        )
        repository.save()
        
        service = GitHubDataIngestionService(self.app_integration)
        service.repository = repository
        
        issue_data = {
            "id": 123,
            "number": 1,
            "title": "Test Issue",
            "body": "This is a test issue",
            "state": "open",
            "user": {"login": "testuser"},
            "author_association": "NONE",
            "assignees": [],
            "labels": [{"name": "bug"}],
            "milestone": None,
            "locked": False,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "closed_at": None,
            "html_url": "https://github.com/owner/test-repo/issues/1"
        }
        
        mock_client.get_issue_comments.return_value = []
        
        service._ingest_single_issue(issue_data, "owner", "test-repo")
        
        # Verify issue was created
        issue = GitHubIssue.objects.get(repository=repository, github_id=123)
        self.assertEqual(issue.title, "Test Issue")
        self.assertEqual(issue.state, "open")
        self.assertEqual(issue.author, "testuser")
        self.assertEqual(issue.labels, ["bug"])


class GitHubIngestionViewSetTestCase(TestCase):
    """Test cases for GitHub ingestion API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = Mock()
        self.user.id = 1
        
        # Mock authentication
        self.client.force_authenticate(user=self.user)
        
        self.application = Application.objects.create(
            name="Test App",
            owner=self.user,
            description="Test application"
        )
        
        # This would need to be adapted based on your actual Integration model
        # self.integration = Integration.objects.create(
        #     name="GitHub Integration",
        #     type="pms",
        #     provider="github",
        #     owner=self.user,
        #     config={"token": "test_token"}
        # )
        
        # self.app_integration = AppIntegration.objects.create(
        #     app=self.application,
        #     integration=self.integration
        # )
    
    @patch('core.views.github_ingestion.GitHubDataIngestionService')
    def test_ingest_repository_success(self, mock_service_class):
        """Test successful repository ingestion"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        viewset = GitHubIngestionViewSet()
        viewset.request = Mock()
        viewset.request.query_params = {
            'owner': 'test-owner',
            'repo': 'test-repo'
        }
        viewset.request.data = {
            'app_integration_id': 1
        }
        viewset.request.user = self.user
        
        # Mock the AppIntegration lookup
        with patch('core.views.github_ingestion.get_object_or_404') as mock_get:
            mock_app_integration = Mock()
            mock_app_integration.app.owner = self.user
            mock_get.return_value = mock_app_integration
            
            response = viewset.ingest_repository(viewset.request)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'success')
            self.assertEqual(response.data['repository'], 'test-owner/test-repo')
    
    def test_ingest_repository_missing_params(self):
        """Test ingestion with missing parameters"""
        viewset = GitHubIngestionViewSet()
        viewset.request = Mock()
        viewset.request.query_params = {}  # Missing owner and repo
        viewset.request.data = {}
        
        response = viewset.ingest_repository(viewset.request)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('core.views.github_ingestion.GitHubDataIngestionService')
    def test_ingest_repository_failure(self, mock_service_class):
        """Test ingestion failure handling"""
        mock_service = Mock()
        mock_service.ingest_repository.side_effect = Exception("Test error")
        mock_service_class.return_value = mock_service
        
        viewset = GitHubIngestionViewSet()
        viewset.request = Mock()
        viewset.request.query_params = {
            'owner': 'test-owner',
            'repo': 'test-repo'
        }
        viewset.request.data = {
            'app_integration_id': 1
        }
        viewset.request.user = self.user
        
        with patch('core.views.github_ingestion.get_object_or_404') as mock_get:
            mock_app_integration = Mock()
            mock_app_integration.app.owner = self.user
            mock_get.return_value = mock_app_integration
            
            response = viewset.ingest_repository(viewset.request)
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('error', response.data)


class GitHubDataIntegrityTestCase(TestCase):
    """Test data integrity and relationships"""
    
    def setUp(self):
        self.user = Mock()
        self.application = Mock()
        self.application.owner = self.user
        
        self.app_integration = Mock()
        self.app_integration.app = self.application
        self.app_integration.id = 1
        
        # Create test repository
        self.repository = GitHubRepository.objects.create(
            full_name="owner/test-repo",
            name="test-repo",
            owner="owner",
            app_integration=self.app_integration,
            url="https://github.com/owner/test-repo"
        )
    
    def test_issue_creation(self):
        """Test issue creation and relationships"""
        issue = GitHubIssue.objects.create(
            repository=self.repository,
            github_id=123,
            number=1,
            title="Test Issue",
            body="Test body",
            state="open",
            author="testuser",
            created_at=timezone.now(),
            updated_at=timezone.now(),
            url="https://github.com/owner/test-repo/issues/1"
        )
        
        self.assertEqual(issue.repository, self.repository)
        self.assertEqual(str(issue), "owner/test-repo#1: Test Issue")
    
    def test_pull_request_creation(self):
        """Test pull request creation and relationships"""
        from core.models.github_data import GitHubPullRequest
        
        pr = GitHubPullRequest.objects.create(
            repository=self.repository,
            github_id=456,
            number=1,
            title="Test PR",
            body="Test PR body",
            state="open",
            author="testuser",
            head_branch="feature-branch",
            base_branch="main",
            merged=False,
            created_at=timezone.now(),
            updated_at=timezone.now(),
            url="https://github.com/owner/test-repo/pull/1"
        )
        
        self.assertEqual(pr.repository, self.repository)
        self.assertEqual(str(pr), "PR owner/test-repo#1: Test PR")
    
    def test_cascade_delete(self):
        """Test cascade deletion behavior"""
        # Create issue
        issue = GitHubIssue.objects.create(
            repository=self.repository,
            github_id=123,
            number=1,
            title="Test Issue",
            state="open",
            author="testuser",
            created_at=timezone.now(),
            updated_at=timezone.now(),
            url="https://github.com/owner/test-repo/issues/1"
        )
        
        # Verify issue exists
        self.assertTrue(GitHubIssue.objects.filter(id=issue.id).exists())
        
        # Delete repository
        self.repository.delete()
        
        # Verify issue is also deleted
        self.assertFalse(GitHubIssue.objects.filter(id=issue.id).exists())


if __name__ == '__main__':
    pytest.main([__file__])
