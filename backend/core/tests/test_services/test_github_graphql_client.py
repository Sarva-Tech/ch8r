import pytest
from unittest.mock import Mock, patch, MagicMock
from gql.transport.exceptions import TransportQueryError, TransportServerError
import time

from core.services.github_graphql_client import GitHubGraphQLClient


@pytest.mark.unit
class TestGitHubGraphQLClientInit:
    def test_init_sets_token_and_transport(self):
        client = GitHubGraphQLClient('test_token')

        assert client.token == 'test_token'
        assert client.endpoint == 'https://api.github.com/graphql'
        assert client.transport is not None
        assert client.client is not None
        assert client.transport.headers['Authorization'] == 'Bearer test_token'
        assert client.transport.headers['Accept'] == 'application/vnd.github.v4+json'
        assert client.transport.headers['User-Agent'] == 'Ch8r-GitHub-GraphQL/1.0'


@pytest.mark.unit
class TestExecuteQuery:
    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_execute_query_success(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={'data': 'test'})

        result = client._execute_query('query string')

        assert result == {'data': 'test'}
        mock_gql.assert_called_once_with('query string')
        client.client.execute.assert_called_once()

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_execute_query_with_variables(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={'data': 'test'})

        variables = {'owner': 'test', 'repo': 'repo'}
        result = client._execute_query('query string', variables)

        assert result == {'data': 'test'}
        client.client.execute.assert_called_once_with('query_doc', variable_values=variables)

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_execute_query_transport_query_error_raises(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(side_effect=TransportQueryError('Syntax error'))

        with pytest.raises(TransportQueryError):
            client._execute_query('query string')

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_execute_query_rate_limit_retries(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'

        client.client.execute = Mock(side_effect=[
            TransportServerError('API rate limit exceeded'),
            {'data': 'success'}
        ])

        result = client._execute_query('query string')

        assert result == {'data': 'success'}
        assert mock_sleep.called

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_execute_query_authentication_error_raises(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(side_effect=TransportServerError('Bad credentials'))

        with pytest.raises(TransportServerError):
            client._execute_query('query string')

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_execute_query_server_error_retries(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'

        client.client.execute = Mock(side_effect=[
            TransportServerError('Server error'),
            TransportServerError('Server error'),
            {'data': 'success'}
        ])

        result = client._execute_query('query string')

        assert result == {'data': 'success'}
        assert client.client.execute.call_count == 3

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_execute_query_generic_exception_retries(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'

        client.client.execute = Mock(side_effect=[
            Exception('Connection error'),
            Exception('Connection error'),
            {'data': 'success'}
        ])

        result = client._execute_query('query string')

        assert result == {'data': 'success'}
        assert client.client.execute.call_count == 3

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_execute_query_max_retries_exceeded(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(side_effect=Exception('Connection error'))

        with pytest.raises(Exception):
            client._execute_query('query string')

        assert client.client.execute.call_count == 3


@pytest.mark.unit
class TestGetIssuesWithComments:
    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_issues_with_comments_default_states(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={'repository': {'issues': {'edges': []}}})

        result = client.get_issues_with_comments('owner', 'repo')

        assert 'repository' in result
        call_kwargs = client.client.execute.call_args[1]
        assert call_kwargs['variable_values']['states'] == ["OPEN", "CLOSED"]

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_issues_with_comments_custom_states(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={'repository': {'issues': {'edges': []}}})

        result = client.get_issues_with_comments('owner', 'repo', states=['OPEN'])

        assert 'repository' in result
        call_kwargs = client.client.execute.call_args[1]
        assert call_kwargs['variable_values']['states'] == ['OPEN']

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_issues_with_comments_with_cursor(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={'repository': {'issues': {'edges': []}}})

        result = client.get_issues_with_comments('owner', 'repo', after_cursor='cursor123')

        assert 'repository' in result
        call_kwargs = client.client.execute.call_args[1]
        assert call_kwargs['variable_values']['after'] == 'cursor123'

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_issues_with_comments_custom_first(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={'repository': {'issues': {'edges': []}}})

        result = client.get_issues_with_comments('owner', 'repo', first=50)

        assert 'repository' in result
        call_kwargs = client.client.execute.call_args[1]
        assert call_kwargs['variable_values']['first'] == 50


@pytest.mark.unit
class TestGetAllIssuesWithComments:
    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_all_issues_with_comments_single_page(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'

        mock_response = {
            'repository': {
                'issues': {
                    'edges': [
                        {'node': {'id': 1, 'title': 'Issue 1'}},
                        {'node': {'id': 2, 'title': 'Issue 2'}}
                    ],
                    'pageInfo': {
                        'hasNextPage': False,
                        'endCursor': None
                    }
                }
            }
        }
        client.client.execute = Mock(return_value=mock_response)

        result = client.get_all_issues_with_comments('owner', 'repo')

        assert len(result) == 2
        assert result[0]['title'] == 'Issue 1'

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_all_issues_with_comments_pagination(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'

        mock_response1 = {
            'repository': {
                'issues': {
                    'edges': [{'node': {'id': i}} for i in range(100)],
                    'pageInfo': {
                        'hasNextPage': True,
                        'endCursor': 'cursor1'
                    }
                }
            }
        }

        mock_response2 = {
            'repository': {
                'issues': {
                    'edges': [{'node': {'id': i}} for i in range(100, 150)],
                    'pageInfo': {
                        'hasNextPage': False,
                        'endCursor': None
                    }
                }
            }
        }

        client.client.execute = Mock(side_effect=[mock_response1, mock_response2])

        result = client.get_all_issues_with_comments('owner', 'repo')

        assert len(result) == 150

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_all_issues_with_comments_no_repository(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={})

        result = client.get_all_issues_with_comments('owner', 'repo')

        assert result == []

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_all_issues_with_comments_custom_states(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'

        mock_response = {
            'repository': {
                'issues': {
                    'edges': [],
                    'pageInfo': {'hasNextPage': False}
                }
            }
        }
        client.client.execute = Mock(return_value=mock_response)

        result = client.get_all_issues_with_comments('owner', 'repo', states=['OPEN'])

        assert result == []


@pytest.mark.unit
class TestGetPullRequestsWithComments:
    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_pull_requests_with_comments_default_states(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={'repository': {'pullRequests': {'edges': []}}})

        result = client.get_pull_requests_with_comments('owner', 'repo')

        assert 'repository' in result
        call_kwargs = client.client.execute.call_args[1]
        assert call_kwargs['variable_values']['states'] == ["OPEN", "CLOSED", "MERGED"]

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_pull_requests_with_comments_custom_states(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={'repository': {'pullRequests': {'edges': []}}})

        result = client.get_pull_requests_with_comments('owner', 'repo', states=['OPEN'])

        assert 'repository' in result
        call_kwargs = client.client.execute.call_args[1]
        assert call_kwargs['variable_values']['states'] == ['OPEN']

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_pull_requests_with_comments_with_cursor(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={'repository': {'pullRequests': {'edges': []}}})

        result = client.get_pull_requests_with_comments('owner', 'repo', after_cursor='cursor123')

        assert 'repository' in result
        call_kwargs = client.client.execute.call_args[1]
        assert call_kwargs['variable_values']['after'] == 'cursor123'


@pytest.mark.unit
class TestGetAllPullRequestsWithComments:
    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_all_pull_requests_with_comments_single_page(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'

        mock_response = {
            'repository': {
                'pullRequests': {
                    'edges': [
                        {'node': {'id': 1, 'title': 'PR 1'}},
                        {'node': {'id': 2, 'title': 'PR 2'}}
                    ],
                    'pageInfo': {
                        'hasNextPage': False,
                        'endCursor': None
                    }
                }
            }
        }
        client.client.execute = Mock(return_value=mock_response)

        result = client.get_all_pull_requests_with_comments('owner', 'repo')

        assert len(result) == 2
        assert result[0]['title'] == 'PR 1'

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_all_pull_requests_with_comments_pagination(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'

        mock_response1 = {
            'repository': {
                'pullRequests': {
                    'edges': [{'node': {'id': i}} for i in range(100)],
                    'pageInfo': {
                        'hasNextPage': True,
                        'endCursor': 'cursor1'
                    }
                }
            }
        }

        mock_response2 = {
            'repository': {
                'pullRequests': {
                    'edges': [{'node': {'id': i}} for i in range(100, 150)],
                    'pageInfo': {
                        'hasNextPage': False,
                        'endCursor': None
                    }
                }
            }
        }

        client.client.execute = Mock(side_effect=[mock_response1, mock_response2])

        result = client.get_all_pull_requests_with_comments('owner', 'repo')

        assert len(result) == 150

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_all_pull_requests_with_comments_no_repository(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={})

        result = client.get_all_pull_requests_with_comments('owner', 'repo')

        assert result == []


@pytest.mark.unit
class TestGetRepositoryInfo:
    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_repository_info_success(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'

        mock_response = {
            'repository': {
                'name': 'test-repo',
                'nameWithOwner': 'owner/test-repo',
                'description': 'Test repository',
                'url': 'https://github.com/owner/test-repo',
                'stargazerCount': 100
            }
        }
        client.client.execute = Mock(return_value=mock_response)

        result = client.get_repository_info('owner', 'repo')

        assert result['name'] == 'test-repo'
        assert result['stargazerCount'] == 100

    @patch('core.services.github_graphql_client.time.sleep')
    @patch('core.services.github_graphql_client.gql')
    def test_get_repository_info_no_repository_key(self, mock_gql, mock_sleep):
        client = GitHubGraphQLClient('test_token')
        mock_gql.return_value = 'query_doc'
        client.client.execute = Mock(return_value={})

        result = client.get_repository_info('owner', 'repo')

        assert result == {}


@pytest.mark.unit
class TestClose:
    def test_close_session(self):
        client = GitHubGraphQLClient('test_token')
        client.client.close_session = Mock()

        client.close()

        client.client.close_session.assert_called_once()

    def test_close_no_close_session_method(self):
        client = GitHubGraphQLClient('test_token')
        client.client = Mock(spec=[])

        client.close()
