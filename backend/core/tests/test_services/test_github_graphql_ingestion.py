import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from django.utils import timezone

from core.services.github_graphql_ingestion import (
    GitHubGraphQLIngestionService,
    _extract_numeric_id_from_global_id
)


@pytest.mark.unit
class TestExtractNumericIdFromGlobalId:
    def test_extract_numeric_id_from_global_id(self):
        result = _extract_numeric_id_from_global_id('test_global_id_123')

        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFFFFFF

    def test_extract_numeric_id_consistency(self):
        id1 = _extract_numeric_id_from_global_id('same_id')
        id2 = _extract_numeric_id_from_global_id('same_id')

        assert id1 == id2

    def test_extract_numeric_id_different_inputs(self):
        id1 = _extract_numeric_id_from_global_id('id_1')
        id2 = _extract_numeric_id_from_global_id('id_2')

        assert id1 != id2


@pytest.mark.unit
class TestGitHubGraphQLIngestionServiceInit:
    def test_init(self):
        mock_app_integration = Mock()
        service = GitHubGraphQLIngestionService(mock_app_integration)

        assert service.app_integration == mock_app_integration
        assert service.graphql_client is None
        assert service.rest_client is None
        assert service.repository is None
        assert service.quality_filter is not None


@pytest.mark.unit
class TestGetGraphQLClient:
    @patch('core.services.github_graphql_ingestion.GitHubGraphQLClient')
    def test_get_graphql_client_creates_new_client(self, mock_client_class):
        mock_app_integration = Mock()
        mock_integration = Mock()
        mock_integration.credentials = '{"token": "test_token"}'
        mock_app_integration.integration = mock_integration

        service = GitHubGraphQLIngestionService(mock_app_integration)

        client = service._get_graphql_client()

        assert client is not None
        mock_client_class.assert_called_once_with('test_token')

    @patch('core.services.github_graphql_ingestion.GitHubGraphQLClient')
    def test_get_graphql_client_reuses_cached_client(self, mock_client_class):
        mock_app_integration = Mock()
        mock_integration = Mock()
        mock_integration.credentials = '{"token": "test_token"}'
        mock_app_integration.integration = mock_integration

        service = GitHubGraphQLIngestionService(mock_app_integration)

        client1 = service._get_graphql_client()
        client2 = service._get_graphql_client()

        assert client1 is client2
        mock_client_class.assert_called_once()

    def test_get_graphql_client_no_token(self):
        mock_app_integration = Mock()
        mock_integration = Mock()
        mock_integration.credentials = '{}'
        mock_app_integration.integration = mock_integration

        service = GitHubGraphQLIngestionService(mock_app_integration)

        with pytest.raises(ValueError, match="GitHub token not found"):
            service._get_graphql_client()


@pytest.mark.unit
class TestGetRestClient:
    @patch('core.services.github_graphql_ingestion.GitHubAPIClient')
    def test_get_rest_client_creates_new_client(self, mock_client_class):
        mock_app_integration = Mock()
        mock_integration = Mock()
        mock_integration.credentials = '{"token": "test_token"}'
        mock_app_integration.integration = mock_integration

        service = GitHubGraphQLIngestionService(mock_app_integration)

        client = service._get_rest_client()

        assert client is not None
        mock_client_class.assert_called_once_with('test_token')

    @patch('core.services.github_graphql_ingestion.GitHubAPIClient')
    def test_get_rest_client_reuses_cached_client(self, mock_client_class):
        mock_app_integration = Mock()
        mock_integration = Mock()
        mock_integration.credentials = '{"token": "test_token"}'
        mock_app_integration.integration = mock_integration

        service = GitHubGraphQLIngestionService(mock_app_integration)

        client1 = service._get_rest_client()
        client2 = service._get_rest_client()

        assert client1 is client2
        mock_client_class.assert_called_once()


@pytest.mark.unit
class TestParseDatetime:
    def test_parse_datetime_with_z_suffix(self):
        service = GitHubGraphQLIngestionService(Mock())

        result = service._parse_datetime('2024-01-01T12:00:00Z')

        assert result is not None
        assert result.tzinfo is not None

    def test_parse_datetime_without_z_suffix(self):
        service = GitHubGraphQLIngestionService(Mock())

        result = service._parse_datetime('2024-01-01T12:00:00')

        assert result is not None

    def test_parse_datetime_none(self):
        service = GitHubGraphQLIngestionService(Mock())

        result = service._parse_datetime(None)

        assert result is None

    def test_parse_datetime_invalid_string(self):
        service = GitHubGraphQLIngestionService(Mock())

        result = service._parse_datetime('invalid_datetime')

        assert result is not None


@pytest.mark.unit
class TestCreateKnowledgeBaseContent:
    @patch('core.services.github_graphql_ingestion.VCRepository')
    def test_create_knowledge_base_content_no_repository(self, mock_repo_class):
        service = GitHubGraphQLIngestionService(Mock())
        service.repository = None

        result = service._create_knowledge_base_content()

        assert result == ""

    @patch('core.services.github_graphql_ingestion.VCRepository')
    def test_create_knowledge_base_content_with_repository(self, mock_repo_class):
        service = GitHubGraphQLIngestionService(Mock())

        mock_repo = Mock()
        mock_repo.full_name = 'owner/repo'
        mock_repo.description = 'Test repository'
        mock_repo.issues.all.return_value = []
        mock_repo.pull_requests.all.return_value = []
        service.repository = mock_repo

        result = service._create_knowledge_base_content()

        assert 'owner/repo' in result
        assert 'Test repository' in result

    @patch('core.services.github_graphql_ingestion.VCRepository')
    def test_create_knowledge_base_content_with_issues(self, mock_repo_class):
        service = GitHubGraphQLIngestionService(Mock())

        mock_issue = Mock()
        mock_issue.number = 1
        mock_issue.title = 'Test Issue'
        mock_issue.state = 'open'
        mock_issue.author = 'testuser'
        mock_issue.body = 'Issue body'
        mock_issue.labels = ['bug', 'enhancement']
        mock_issue.comments.all.return_value = []

        mock_repo = Mock()
        mock_repo.full_name = 'owner/repo'
        mock_repo.description = ''
        mock_repo.issues.all.return_value = [mock_issue]
        mock_repo.pull_requests.all.return_value = []
        service.repository = mock_repo

        result = service._create_knowledge_base_content()

        assert 'Issue #1' in result
        assert 'Test Issue' in result


@pytest.mark.unit
class TestIngestIssueCommentFromGraphQL:
    @patch('core.services.github_graphql_ingestion.VCIssueComment')
    @patch('core.services.github_graphql_ingestion._extract_numeric_id_from_global_id')
    def test_ingest_issue_comment_success(self, mock_extract_id, mock_comment_class):
        service = GitHubGraphQLIngestionService(Mock())
        service.quality_filter.should_ingest = Mock(return_value=True)
        service.quality_filter.remove_emojis = Mock(return_value='cleaned body')

        mock_issue = Mock()
        comment_data = {
            'id': 'comment_id_123',
            'body': 'Test comment',
            'author': {'login': 'testuser'},
            'authorAssociation': 'OWNER',
            'createdAt': '2024-01-01T12:00:00Z',
            'updatedAt': '2024-01-01T12:00:00Z',
            'url': 'https://github.com/test'
        }
        mock_extract_id.return_value = 123

        service._ingest_issue_comment_from_graphql(mock_issue, comment_data)

        mock_comment_class.objects.update_or_create.assert_called_once()

    @patch('core.services.github_graphql_ingestion.VCIssueComment')
    @patch('core.services.github_graphql_ingestion._extract_numeric_id_from_global_id')
    def test_ingest_issue_comment_filtered(self, mock_extract_id, mock_comment_class):
        service = GitHubGraphQLIngestionService(Mock())
        service.quality_filter.should_ingest = Mock(return_value=False)

        mock_issue = Mock()
        comment_data = {
            'id': 'comment_id_123',
            'body': '👍',
            'author': {'login': 'testuser'},
            'authorAssociation': 'OWNER',
            'createdAt': '2024-01-01T12:00:00Z',
            'updatedAt': '2024-01-01T12:00:00Z',
            'url': 'https://github.com/test'
        }

        service._ingest_issue_comment_from_graphql(mock_issue, comment_data)

        mock_comment_class.objects.update_or_create.assert_not_called()


@pytest.mark.unit
class TestIngestPRCommentFromGraphQL:
    @patch('core.services.github_graphql_ingestion.VCPRComment')
    @patch('core.services.github_graphql_ingestion._extract_numeric_id_from_global_id')
    def test_ingest_pr_comment_success(self, mock_extract_id, mock_comment_class):
        service = GitHubGraphQLIngestionService(Mock())
        service.quality_filter.should_ingest = Mock(return_value=True)
        service.quality_filter.remove_emojis = Mock(return_value='cleaned body')

        mock_pr = Mock()
        comment_data = {
            'id': 'comment_id_123',
            'body': 'Test comment',
            'author': {'login': 'testuser'},
            'authorAssociation': 'OWNER',
            'createdAt': '2024-01-01T12:00:00Z',
            'updatedAt': '2024-01-01T12:00:00Z',
            'url': 'https://github.com/test'
        }
        mock_extract_id.return_value = 123

        service._ingest_pr_comment_from_graphql(mock_pr, comment_data)

        mock_comment_class.objects.update_or_create.assert_called_once()

    @patch('core.services.github_graphql_ingestion.VCPRComment')
    @patch('core.services.github_graphql_ingestion._extract_numeric_id_from_global_id')
    def test_ingest_pr_comment_filtered(self, mock_extract_id, mock_comment_class):
        service = GitHubGraphQLIngestionService(Mock())
        service.quality_filter.should_ingest = Mock(return_value=False)

        mock_pr = Mock()
        comment_data = {
            'id': 'comment_id_123',
            'body': '👍',
            'author': {'login': 'testuser'},
            'authorAssociation': 'OWNER',
            'createdAt': '2024-01-01T12:00:00Z',
            'updatedAt': '2024-01-01T12:00:00Z',
            'url': 'https://github.com/test'
        }

        service._ingest_pr_comment_from_graphql(mock_pr, comment_data)

        mock_comment_class.objects.update_or_create.assert_not_called()


@pytest.mark.unit
class TestIngestSingleIssueFromGraphQL:
    @patch('core.services.github_graphql_ingestion.transaction.atomic')
    @patch('core.services.github_graphql_ingestion.VCIssue')
    def test_ingest_single_issue_success(self, mock_issue_class, mock_atomic):
        service = GitHubGraphQLIngestionService(Mock())
        service.repository = Mock()

        issue_data = {
            'number': 1,
            'title': 'Test Issue',
            'state': 'OPEN',
            'body': 'Issue body',
            'author': {'login': 'testuser'},
            'authorAssociation': 'OWNER',
            'assignees': {'nodes': [{'login': 'assignee1'}]},
            'labels': {'nodes': [{'name': 'bug'}]},
            'milestone': {'title': 'v1.0'},
            'locked': False,
            'createdAt': '2024-01-01T12:00:00Z',
            'updatedAt': '2024-01-01T12:00:00Z',
            'closedAt': None,
            'url': 'https://github.com/test'
        }

        mock_issue = Mock()
        mock_issue_class.objects.update_or_create.return_value = (mock_issue, True)

        service._ingest_single_issue_from_graphql(issue_data)

        mock_issue_class.objects.update_or_create.assert_called_once()

    @patch('core.services.github_graphql_ingestion.transaction.atomic')
    @patch('core.services.github_graphql_ingestion.VCIssue')
    def test_ingest_single_issue_with_comments(self, mock_issue_class, mock_atomic):
        service = GitHubGraphQLIngestionService(Mock())
        service.repository = Mock()
        service._ingest_issue_comment_from_graphql = Mock()

        issue_data = {
            'number': 1,
            'title': 'Test Issue',
            'state': 'OPEN',
            'body': 'Issue body',
            'author': {'login': 'testuser'},
            'authorAssociation': 'OWNER',
            'assignees': {'nodes': []},
            'labels': {'nodes': []},
            'milestone': None,
            'locked': False,
            'createdAt': '2024-01-01T12:00:00Z',
            'updatedAt': '2024-01-01T12:00:00Z',
            'closedAt': None,
            'url': 'https://github.com/test',
            'comments': {
                'edges': [
                    {'node': {'id': 'comment1', 'body': 'Comment 1', 'author': {'login': 'user1'}, 'authorAssociation': 'NONE', 'createdAt': '2024-01-01T12:00:00Z', 'updatedAt': '2024-01-01T12:00:00Z', 'url': 'https://github.com/test'}}
                ]
            }
        }

        mock_issue = Mock()
        mock_issue_class.objects.update_or_create.return_value = (mock_issue, True)

        service._ingest_single_issue_from_graphql(issue_data)

        service._ingest_issue_comment_from_graphql.assert_called_once()


@pytest.mark.unit
class TestIngestSinglePRFromGraphQL:
    @patch('core.services.github_graphql_ingestion.transaction.atomic')
    @patch('core.services.github_graphql_ingestion.VCPullRequest')
    def test_ingest_single_pr_success(self, mock_pr_class, mock_atomic):
        service = GitHubGraphQLIngestionService(Mock())
        service.repository = Mock()

        pr_data = {
            'number': 1,
            'title': 'Test PR',
            'state': 'OPEN',
            'body': 'PR body',
            'author': {'login': 'testuser'},
            'authorAssociation': 'OWNER',
            'assignees': {'nodes': [{'login': 'assignee1'}]},
            'labels': {'nodes': [{'name': 'enhancement'}]},
            'milestone': {'title': 'v1.0'},
            'headRefName': 'feature',
            'baseRefName': 'main',
            'merged': False,
            'mergedAt': None,
            'mergeCommit': {'oid': 'abc123'},
            'additions': 10,
            'deletions': 5,
            'changedFiles': 2,
            'createdAt': '2024-01-01T12:00:00Z',
            'updatedAt': '2024-01-01T12:00:00Z',
            'closedAt': None,
            'url': 'https://github.com/test'
        }

        mock_pr = Mock()
        mock_pr_class.objects.update_or_create.return_value = (mock_pr, True)

        mock_rest_client = Mock()
        mock_rest_client.get_pull_request_files.return_value = []

        service._ingest_single_pull_request_from_graphql(pr_data, 'owner', 'repo', mock_rest_client)

        mock_pr_class.objects.update_or_create.assert_called_once()

    @patch('core.services.github_graphql_ingestion.transaction.atomic')
    @patch('core.services.github_graphql_ingestion.VCPullRequest')
    @patch('core.services.github_graphql_ingestion.VCPRFile')
    def test_ingest_single_pr_with_files(self, mock_file_class, mock_pr_class, mock_atomic):
        service = GitHubGraphQLIngestionService(Mock())
        service.repository = Mock()

        pr_data = {
            'number': 1,
            'title': 'Test PR',
            'state': 'OPEN',
            'body': 'PR body',
            'author': {'login': 'testuser'},
            'authorAssociation': 'OWNER',
            'assignees': {'nodes': []},
            'labels': {'nodes': []},
            'milestone': None,
            'headRefName': 'feature',
            'baseRefName': 'main',
            'merged': False,
            'mergedAt': None,
            'mergeCommit': None,
            'additions': 10,
            'deletions': 5,
            'changedFiles': 2,
            'createdAt': '2024-01-01T12:00:00Z',
            'updatedAt': '2024-01-01T12:00:00Z',
            'closedAt': None,
            'url': 'https://github.com/test',
            'comments': {'edges': []}
        }

        mock_pr = Mock()
        mock_pr_class.objects.update_or_create.return_value = (mock_pr, True)

        mock_rest_client = Mock()
        mock_rest_client.get_pull_request_files.return_value = [
            {'filename': 'file1.py', 'status': 'modified', 'additions': 5, 'deletions': 2, 'changes': 7, 'patch': 'diff', 'blob_url': 'url1', 'raw_url': 'url2', 'contents_url': 'url3'}
        ]

        service._ingest_single_pull_request_from_graphql(pr_data, 'owner', 'repo', mock_rest_client)

        mock_file_class.objects.update_or_create.assert_called_once()
