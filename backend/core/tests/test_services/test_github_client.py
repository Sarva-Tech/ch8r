import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import time

from core.services.github_client import GitHubAPIClient


@pytest.mark.unit
class TestGitHubAPIClientInit:
    def test_init_sets_token_and_headers(self):
        client = GitHubAPIClient('test_token')

        assert client.token == 'test_token'
        assert client.session is not None
        assert client.session.headers['Authorization'] == 'Bearer test_token'
        assert client.session.headers['Accept'] == 'application/vnd.github+json'
        assert client.session.headers['X-GitHub-Api-Version'] == '2022-11-28'
        assert client.session.headers['User-Agent'] == 'Ch8r-GitHub-Ingestion/1.0'


@pytest.mark.unit
class TestMakeRequest:
    @patch('core.services.github_client.time.sleep')
    def test_make_request_success(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        client.session.request = Mock(return_value=mock_response)

        result = client._make_request('GET', '/test')

        assert result == {'data': 'test'}
        client.session.request.assert_called_once()

    @patch('core.services.github_client.time.sleep')
    def test_make_request_rate_limit_hit(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.headers = {
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(int(time.time()) + 2)
        }
        mock_response.json.return_value = {'message': 'Rate limit exceeded'}

        client.session.request = Mock(side_effect=[
            mock_response,
            Mock(status_code=200, json=Mock(return_value={'data': 'success'}))
        ])

        result = client._make_request('GET', '/test')

        assert result == {'data': 'success'}
        assert mock_sleep.called

    @patch('core.services.github_client.time.sleep')
    def test_make_request_401_error_raises(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.content = b'{"message": "Unauthorized"}'
        mock_response.json.return_value = {'message': 'Unauthorized'}
        client.session.request = Mock(return_value=mock_response)

        with pytest.raises(requests.exceptions.HTTPError, match="GitHub API error: Unauthorized"):
            client._make_request('GET', '/test')

    @patch('core.services.github_client.time.sleep')
    def test_make_request_404_error_raises(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.content = b'{"message": "Not found"}'
        mock_response.json.return_value = {'message': 'Not found'}
        client.session.request = Mock(return_value=mock_response)

        with pytest.raises(requests.exceptions.HTTPError, match="GitHub API error: Not found"):
            client._make_request('GET', '/test')

    @patch('core.services.github_client.time.sleep')
    def test_make_request_500_error_retries(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b'{"message": "Server error"}'
        mock_response.json.return_value = {'message': 'Server error'}

        client.session.request = Mock(side_effect=[
            mock_response,
            mock_response,
            Mock(status_code=200, json=Mock(return_value={'data': 'success'}))
        ])

        result = client._make_request('GET', '/test')

        assert result == {'data': 'success'}
        assert client.session.request.call_count == 3

    @patch('core.services.github_client.time.sleep')
    def test_make_request_timeout_retries(self, mock_sleep):
        client = GitHubAPIClient('test_token')

        client.session.request = Mock(side_effect=[
            requests.exceptions.Timeout('Timeout'),
            requests.exceptions.Timeout('Timeout'),
            Mock(status_code=200, json=Mock(return_value={'data': 'success'}))
        ])

        result = client._make_request('GET', '/test')

        assert result == {'data': 'success'}
        assert client.session.request.call_count == 3

    @patch('core.services.github_client.time.sleep')
    def test_make_request_timeout_max_retries_exceeded(self, mock_sleep):
        client = GitHubAPIClient('test_token')

        client.session.request = Mock(side_effect=requests.exceptions.Timeout('Timeout'))

        with pytest.raises(requests.exceptions.Timeout):
            client._make_request('GET', '/test')

        assert client.session.request.call_count == 3


@pytest.mark.unit
class TestGetRepositoryInfo:
    @patch('core.services.github_client.time.sleep')
    def test_get_repository_info(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'name': 'test-repo', 'owner': 'test-owner'}
        client.session.request = Mock(return_value=mock_response)

        result = client.get_repository_info('owner', 'repo')

        assert result == {'name': 'test-repo', 'owner': 'test-owner'}
        client.session.request.assert_called_once_with('GET', 'https://api.github.com/repos/owner/repo', timeout=30)


@pytest.mark.unit
class TestGetIssues:
    @patch('core.services.github_client.time.sleep')
    def test_get_issues_single_page(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'title': 'Issue 1'},
            {'id': 2, 'title': 'Issue 2'}
        ]
        client.session.request = Mock(return_value=mock_response)

        result = client.get_issues('owner', 'repo')

        assert len(result) == 2
        assert result[0]['title'] == 'Issue 1'

    @patch('core.services.github_client.time.sleep')
    def test_get_issues_filters_pull_requests(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'title': 'Issue 1'},
            {'id': 2, 'title': 'PR 1', 'pull_request': {}},
            {'id': 3, 'title': 'Issue 2'}
        ]
        client.session.request = Mock(return_value=mock_response)

        result = client.get_issues('owner', 'repo')

        assert len(result) == 2
        assert all('pull_request' not in issue for issue in result)

    @patch('core.services.github_client.time.sleep')
    def test_get_issues_with_since_parameter(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        client.session.request = Mock(return_value=mock_response)

        client.get_issues('owner', 'repo', since='2024-01-01')

        call_kwargs = client.session.request.call_args[1]
        assert 'since' in call_kwargs['params']
        assert call_kwargs['params']['since'] == '2024-01-01'

    @patch('core.services.github_client.time.sleep')
    def test_get_issues_pagination(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = [{'id': i} for i in range(100)]

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = [{'id': i} for i in range(100, 150)]

        client.session.request = Mock(side_effect=[mock_response1, mock_response2])

        result = client.get_issues('owner', 'repo', per_page=100)

        assert len(result) == 150


@pytest.mark.unit
class TestGetIssueComments:
    @patch('core.services.github_client.time.sleep')
    def test_get_issue_comments(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'body': 'Comment 1'},
            {'id': 2, 'body': 'Comment 2'}
        ]
        client.session.request = Mock(return_value=mock_response)

        result = client.get_issue_comments('owner', 'repo', 1)

        assert len(result) == 2
        assert result[0]['body'] == 'Comment 1'

    @patch('core.services.github_client.time.sleep')
    def test_get_issue_comments_pagination(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = [{'id': i} for i in range(100)]

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = [{'id': i} for i in range(100, 150)]

        client.session.request = Mock(side_effect=[mock_response1, mock_response2])

        result = client.get_issue_comments('owner', 'repo', 1)

        assert len(result) == 150


@pytest.mark.unit
class TestGetPullRequests:
    @patch('core.services.github_client.time.sleep')
    def test_get_pull_requests(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'title': 'PR 1'},
            {'id': 2, 'title': 'PR 2'}
        ]
        client.session.request = Mock(return_value=mock_response)

        result = client.get_pull_requests('owner', 'repo')

        assert len(result) == 2
        assert result[0]['title'] == 'PR 1'

    @patch('core.services.github_client.time.sleep')
    def test_get_pull_requests_with_since(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        client.session.request = Mock(return_value=mock_response)

        client.get_pull_requests('owner', 'repo', since='2024-01-01')

        call_kwargs = client.session.request.call_args[1]
        assert 'since' in call_kwargs['params']
        assert call_kwargs['params']['since'] == '2024-01-01'


@pytest.mark.unit
class TestGetPullRequestComments:
    @patch('core.services.github_client.time.sleep')
    def test_get_pull_request_comments(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'id': 1, 'body': 'Comment 1'},
            {'id': 2, 'body': 'Comment 2'}
        ]
        client.session.request = Mock(return_value=mock_response)

        result = client.get_pull_request_comments('owner', 'repo', 1)

        assert len(result) == 2

    @patch('core.services.github_client.time.sleep')
    def test_get_pull_request_comments_error_handling(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        client.session.request = Mock(side_effect=Exception('API error'))

        result = client.get_pull_request_comments('owner', 'repo', 1)

        assert result == []


@pytest.mark.unit
class TestGetPullRequestFiles:
    @patch('core.services.github_client.time.sleep')
    def test_get_pull_request_files(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'filename': 'file1.py'},
            {'filename': 'file2.py'}
        ]
        client.session.request = Mock(return_value=mock_response)

        result = client.get_pull_request_files('owner', 'repo', 1)

        assert len(result) == 2
        assert result[0]['filename'] == 'file1.py'

    @patch('core.services.github_client.time.sleep')
    def test_get_pull_request_files_error_handling(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        client.session.request = Mock(side_effect=Exception('API error'))

        result = client.get_pull_request_files('owner', 'repo', 1)

        assert result == []


@pytest.mark.unit
class TestGetDiscussions:
    @patch('core.services.github_client.time.sleep')
    def test_get_discussions(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'items': [
                {'id': 1, 'title': 'Discussion 1'},
                {'id': 2, 'title': 'Discussion 2'}
            ]
        }
        client.session.request = Mock(return_value=mock_response)

        result = client.get_discussions('owner', 'repo')

        assert len(result) == 2
        assert result[0]['title'] == 'Discussion 1'

    @patch('core.services.github_client.time.sleep')
    def test_get_discussions_with_since(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'items': []}
        client.session.request = Mock(return_value=mock_response)

        client.get_discussions('owner', 'repo', since='2024-01-01')

        call_kwargs = client.session.request.call_args[1]
        assert 'q' in call_kwargs['params']
        assert 'created:>2024-01-01' in call_kwargs['params']['q']


@pytest.mark.unit
class TestGetDiscussionComments:
    def test_get_discussion_comments_not_implemented(self):
        client = GitHubAPIClient('test_token')

        result = client.get_discussion_comments('owner', 'repo', 1)

        assert result == []


@pytest.mark.unit
class TestGetWikiPages:
    def test_get_wiki_pages_not_available(self):
        client = GitHubAPIClient('test_token')

        result = client.get_wiki_pages('owner', 'repo')

        assert result == []


@pytest.mark.unit
class TestGetRepositoryFile:
    @patch('core.services.github_client.time.sleep')
    def test_get_repository_file_success(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'content': 'file content'}
        client.session.request = Mock(return_value=mock_response)

        result = client.get_repository_file('owner', 'repo', 'path/to/file.txt')

        assert result == {'content': 'file content'}

    @patch('core.services.github_client.time.sleep')
    def test_get_repository_file_with_ref(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'content': 'file content'}
        client.session.request = Mock(return_value=mock_response)

        client.get_repository_file('owner', 'repo', 'path/to/file.txt', ref='main')

        call_kwargs = client.session.request.call_args[1]
        assert 'ref' in call_kwargs['params']
        assert call_kwargs['params']['ref'] == 'main'

    @patch('core.services.github_client.time.sleep')
    def test_get_repository_file_not_found(self, mock_sleep):
        client = GitHubAPIClient('test_token')

        with patch.object(client, '_make_request', side_effect=requests.exceptions.HTTPError('404 Not found')):
            result = client.get_repository_file('owner', 'repo', 'path/to/file.txt')

        assert result is None


@pytest.mark.unit
class TestGetCodeComments:
    @patch('core.services.github_client.time.sleep')
    def test_get_code_comments_success(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'sha': 'abc123', 'commit': {'message': 'Fix bug'}}
        ]
        client.session.request = Mock(return_value=mock_response)

        result = client.get_code_comments('owner', 'repo', 'path/to/file.py')

        assert len(result) == 1

    @patch('core.services.github_client.time.sleep')
    def test_get_code_comments_error_handling(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        client.session.request = Mock(side_effect=Exception('API error'))

        result = client.get_code_comments('owner', 'repo', 'path/to/file.py')

        assert result == []


@pytest.mark.unit
class TestGetRateLimitStatus:
    @patch('core.services.github_client.time.sleep')
    def test_get_rate_limit_status(self, mock_sleep):
        client = GitHubAPIClient('test_token')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'resources': {
                'core': {'remaining': 4999, 'limit': 5000}
            }
        }
        client.session.request = Mock(return_value=mock_response)

        result = client.get_rate_limit_status()

        assert result['resources']['core']['remaining'] == 4999


@pytest.mark.unit
class TestClose:
    def test_close_session(self):
        client = GitHubAPIClient('test_token')
        client.session.close = Mock()

        client.close()

        client.session.close.assert_called_once()
