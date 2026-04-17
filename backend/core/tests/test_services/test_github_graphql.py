import pytest
from unittest.mock import Mock, patch

from core.services.providers.version_control.github_graphql import GitHubGraphQLProvider


@pytest.mark.unit
class TestGitHubGraphQLProvider:
    def test_init(self):
        credentials = {'token': 'test_token'}
        provider = GitHubGraphQLProvider(credentials)

        assert provider.credentials == credentials
        assert provider._graphql_client is None
        assert provider._rest_client is None

    def test_provider_name(self):
        assert GitHubGraphQLProvider.provider_name == 'github_graphql'

    def test_get_graphql_client_with_token(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            client = provider._get_graphql_client()

            mock_client_class.assert_called_once_with('test_token')
            assert client == mock_client
            assert provider._graphql_client == mock_client

    def test_get_graphql_client_without_token(self):
        credentials = {}
        provider = GitHubGraphQLProvider(credentials)

        with pytest.raises(ValueError) as exc_info:
            provider._get_graphql_client()

        assert "GitHub token not found in credentials" in str(exc_info.value)

    def test_get_graphql_client_caches_client(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            client1 = provider._get_graphql_client()
            client2 = provider._get_graphql_client()

            mock_client_class.assert_called_once()
            assert client1 == client2

    def test_get_rest_client_with_token(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            client = provider._get_rest_client()

            mock_client_class.assert_called_once_with('test_token')
            assert client == mock_client
            assert provider._rest_client == mock_client

    def test_get_rest_client_without_token(self):
        credentials = {}
        provider = GitHubGraphQLProvider(credentials)

        with pytest.raises(ValueError) as exc_info:
            provider._get_rest_client()

        assert "GitHub token not found in credentials" in str(exc_info.value)

    def test_validate_credentials_success(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.execute_query.return_value = {
                'data': {
                    'viewer': {
                        'login': 'testuser',
                        'name': 'Test User',
                        'avatarUrl': 'https://example.com/avatar.png',
                        'url': 'https://github.com/testuser'
                    }
                }
            }

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            is_valid, error, metadata = provider.validate_credentials()

            assert is_valid is True
            assert error == ''
            assert metadata['login'] == 'testuser'
            assert metadata['name'] == 'Test User'
            assert metadata['avatar_url'] == 'https://example.com/avatar.png'
            assert metadata['html_url'] == 'https://github.com/testuser'

    def test_validate_credentials_failure(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.execute_query.side_effect = Exception("Invalid token")

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            is_valid, error, metadata = provider.validate_credentials()

            assert is_valid is False
            assert "Invalid token" in error
            assert metadata == {}

    def test_get_repository_info(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_repository_info.return_value = {
                'id': '123',
                'name': 'test-repo',
                'description': 'Test repository',
                'url': 'https://github.com/owner/test-repo',
                'isPrivate': False,
                'defaultBranchRef': {'name': 'main'},
                'isFork': False,
                'stargazerCount': 10,
                'forkCount': 5,
                'issues': {'totalCount': 3}
            }

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            repo_info = provider.get_repository_info('owner', 'test-repo')

            mock_client.get_repository_info.assert_called_once_with('owner', 'test-repo')
            assert repo_info['id'] == '123'
            assert repo_info['name'] == 'test-repo'
            assert repo_info['owner'] == 'owner'
            assert repo_info['full_name'] == 'owner/test-repo'
            assert repo_info['description'] == 'Test repository'
            assert repo_info['default_branch'] == 'main'
            assert repo_info['stars'] == 10
            assert repo_info['forks'] == 5
            assert repo_info['open_issues'] == 3

    def test_get_issues_all(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_all_issues_with_comments.return_value = [
                {
                    'number': 1,
                    'title': 'Test Issue',
                    'body': 'Issue body',
                    'state': 'OPEN',
                    'author': {'login': 'testuser'},
                    'authorAssociation': 'OWNER',
                    'assignees': {'nodes': [{'login': 'assignee1'}]},
                    'labels': {'nodes': [{'name': 'bug'}]},
                    'milestone': {'title': 'v1.0'},
                    'locked': False,
                    'createdAt': '2024-01-01T00:00:00Z',
                    'updatedAt': '2024-01-02T00:00:00Z',
                    'closedAt': None,
                    'url': 'https://github.com/owner/repo/issues/1'
                }
            ]

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            issues = provider.get_issues('owner', 'repo', state='all')

            mock_client.get_all_issues_with_comments.assert_called_once_with(
                'owner', 'repo', states=['OPEN', 'CLOSED'], since=None
            )
            assert len(issues) == 1
            assert issues[0]['id'] == '1'
            assert issues[0]['title'] == 'Test Issue'
            assert issues[0]['state'] == 'open'
            assert issues[0]['author'] == 'testuser'

    def test_get_issues_open(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_all_issues_with_comments.return_value = []

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            issues = provider.get_issues('owner', 'repo', state='open')

            mock_client.get_all_issues_with_comments.assert_called_once_with(
                'owner', 'repo', states=['OPEN'], since=None
            )

    def test_get_issues_closed(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_all_issues_with_comments.return_value = []

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            issues = provider.get_issues('owner', 'repo', state='closed')

            mock_client.get_all_issues_with_comments.assert_called_once_with(
                'owner', 'repo', states=['CLOSED'], since=None
            )

    def test_get_issues_with_since(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_all_issues_with_comments.return_value = []

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            issues = provider.get_issues('owner', 'repo', state='all', since='2024-01-01')

            mock_client.get_all_issues_with_comments.assert_called_once_with(
                'owner', 'repo', states=['OPEN', 'CLOSED'], since='2024-01-01'
            )

    def test_get_issue_comments(self):
        credentials = {'token': 'test_token'}
        provider = GitHubGraphQLProvider(credentials)

        comments = provider.get_issue_comments('owner', 'repo', 1)

        assert comments == []

    def test_get_pull_requests_all(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_all_pull_requests_with_comments.return_value = [
                {
                    'number': 1,
                    'title': 'Test PR',
                    'body': 'PR body',
                    'state': 'OPEN',
                    'author': {'login': 'testuser'},
                    'authorAssociation': 'OWNER',
                    'assignees': {'nodes': [{'login': 'assignee1'}]},
                    'labels': {'nodes': [{'name': 'enhancement'}]},
                    'milestone': {'title': 'v1.0'},
                    'headRefName': 'feature',
                    'baseRefName': 'main',
                    'merged': False,
                    'mergedAt': None,
                    'mergeCommit': None,
                    'additions': 10,
                    'deletions': 5,
                    'changedFiles': 2,
                    'createdAt': '2024-01-01T00:00:00Z',
                    'updatedAt': '2024-01-02T00:00:00Z',
                    'closedAt': None,
                    'url': 'https://github.com/owner/repo/pull/1'
                }
            ]

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            prs = provider.get_pull_requests('owner', 'repo', state='all')

            mock_client.get_all_pull_requests_with_comments.assert_called_once_with(
                'owner', 'repo', states=['OPEN', 'CLOSED', 'MERGED'], since=None
            )
            assert len(prs) == 1
            assert prs[0]['id'] == '1'
            assert prs[0]['title'] == 'Test PR'
            assert prs[0]['state'] == 'open'
            assert prs[0]['head_branch'] == 'feature'
            assert prs[0]['base_branch'] == 'main'

    def test_get_pull_requests_open(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_all_pull_requests_with_comments.return_value = []

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            prs = provider.get_pull_requests('owner', 'repo', state='open')

            mock_client.get_all_pull_requests_with_comments.assert_called_once_with(
                'owner', 'repo', states=['OPEN'], since=None
            )

    def test_get_pull_requests_closed(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_all_pull_requests_with_comments.return_value = []

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            prs = provider.get_pull_requests('owner', 'repo', state='closed')

            mock_client.get_all_pull_requests_with_comments.assert_called_once_with(
                'owner', 'repo', states=['CLOSED', 'MERGED'], since=None
            )

    def test_get_pull_requests_merged(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_all_pull_requests_with_comments.return_value = []

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            prs = provider.get_pull_requests('owner', 'repo', state='merged')

            mock_client.get_all_pull_requests_with_comments.assert_called_once_with(
                'owner', 'repo', states=['MERGED'], since=None
            )

    def test_get_pull_requests_with_since(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_all_pull_requests_with_comments.return_value = []

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            prs = provider.get_pull_requests('owner', 'repo', state='all', since='2024-01-01')

            mock_client.get_all_pull_requests_with_comments.assert_called_once_with(
                'owner', 'repo', states=['OPEN', 'CLOSED', 'MERGED'], since='2024-01-01'
            )

    def test_get_pull_request_comments(self):
        credentials = {'token': 'test_token'}
        provider = GitHubGraphQLProvider(credentials)

        comments = provider.get_pull_request_comments('owner', 'repo', 1)

        assert comments == []

    def test_get_pull_request_files(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            mock_client.get_pull_request_files.return_value = [
                {
                    'filename': 'test.py',
                    'status': 'modified',
                    'additions': 10,
                    'deletions': 5,
                    'changes': 15,
                    'patch': 'diff content',
                    'blob_url': 'https://github.com/blob',
                    'raw_url': 'https://github.com/raw'
                }
            ]

            credentials = {'token': 'test_token'}
            provider = GitHubGraphQLProvider(credentials)

            files = provider.get_pull_request_files('owner', 'repo', 1)

            mock_client.get_pull_request_files.assert_called_once_with('owner', 'repo', 1)
            assert len(files) == 1
            assert files[0]['filename'] == 'test.py'
            assert files[0]['status'] == 'modified'
            assert files[0]['additions'] == 10
            assert files[0]['deletions'] == 5

    def test_close(self):
        with patch('core.services.providers.version_control.github_graphql.GitHubGraphQLClient') as mock_graphql_class:
            with patch('core.services.providers.version_control.github_graphql.GitHubAPIClient') as mock_rest_class:
                mock_graphql_client = Mock()
                mock_graphql_class.return_value = mock_graphql_client

                mock_rest_client = Mock()
                mock_rest_class.return_value = mock_rest_client

                credentials = {'token': 'test_token'}
                provider = GitHubGraphQLProvider(credentials)

                # Initialize both clients
                provider._get_graphql_client()
                provider._get_rest_client()

                provider.close()

                mock_graphql_client.close.assert_called_once()
                mock_rest_client.close.assert_called_once()
                assert provider._graphql_client is None
                assert provider._rest_client is None

    def test_close_with_no_clients(self):
        credentials = {'token': 'test_token'}
        provider = GitHubGraphQLProvider(credentials)

        # Should not raise any errors
        provider.close()

        assert provider._graphql_client is None
        assert provider._rest_client is None
