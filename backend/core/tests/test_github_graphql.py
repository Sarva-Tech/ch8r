"""
Tests for GitHub GraphQL client and ingestion service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from datetime import datetime

from core.services.github_graphql_client import GitHubGraphQLClient
from core.services.github_graphql_ingestion import GitHubGraphQLIngestionService
from core.models import AppIntegration, Integration, GitHubRepository
from core.tests.factories import AppIntegrationFactory, IntegrationFactory


class TestGitHubGraphQLClient(TestCase):
    """Test GitHub GraphQL client functionality"""

    def setUp(self):
        self.token = "test_token"
        self.client = GitHubGraphQLClient(self.token)

    def tearDown(self):
        if hasattr(self.client, 'close'):
            self.client.close()

    @patch('core.services.github_graphql_client.Client.execute')
    def test_get_repository_info(self, mock_execute):
        """Test repository info retrieval"""
        mock_response = {
            'repository': {
                'id': 'R_123',
                'name': 'test-repo',
                'nameWithOwner': 'owner/test-repo',
                'description': 'Test repository',
                'url': 'https://github.com/owner/test-repo',
                'isPrivate': False,
                'defaultBranchRef': {
                    'name': 'main'
                },
                'createdAt': '2023-01-01T00:00:00Z',
                'updatedAt': '2023-01-02T00:00:00Z'
            }
        }
        mock_execute.return_value = mock_response

        result = self.client.get_repository_info('owner', 'test-repo')

        self.assertEqual(result['name'], 'test-repo')
        self.assertEqual(result['nameWithOwner'], 'owner/test-repo')
        self.assertFalse(result['isPrivate'])
        self.assertEqual(result['defaultBranchRef']['name'], 'main')

    @patch('core.services.github_graphql_client.Client.execute')
    def test_get_issues_with_comments(self, mock_execute):
        """Test issues with comments retrieval"""
        mock_response = {
            'repository': {
                'issues': {
                    'pageInfo': {
                        'hasNextPage': False,
                        'endCursor': 'cursor123'
                    },
                    'edges': [
                        {
                            'node': {
                                'id': 'I_123',
                                'number': 1,
                                'title': 'Test Issue',
                                'body': 'Issue body',
                                'state': 'OPEN',
                                'author': {
                                    'login': 'testuser'
                                },
                                'comments': {
                                    'edges': [
                                        {
                                            'node': {
                                                'id': 'IC_456',
                                                'body': 'Comment body',
                                                'author': {
                                                    'login': 'commenter'
                                                },
                                                'createdAt': '2023-01-01T00:00:00Z'
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        }
        mock_execute.return_value = mock_response

        result = self.client.get_issues_with_comments('owner', 'repo')

        self.assertEqual(len(result['repository']['issues']['edges']), 1)
        issue = result['repository']['issues']['edges'][0]['node']
        self.assertEqual(issue['number'], 1)
        self.assertEqual(issue['title'], 'Test Issue')
        self.assertEqual(len(issue['comments']['edges']), 1)

    @patch('core.services.github_graphql_client.Client.execute')
    def test_rate_limit_handling(self, mock_execute):
        """Test rate limit handling"""
        from gql.exceptions import GraphQLExecutionError

        # Mock rate limit error
        mock_execute.side_effect = GraphQLExecutionError("API rate limit exceeded")

        with self.assertRaises(GraphQLExecutionError):
            self.client.get_repository_info('owner', 'repo')

        # Verify retry attempts (should be called 3 times)
        self.assertEqual(mock_execute.call_count, 3)


class TestGitHubGraphQLIngestionService(TestCase):
    """Test GitHub GraphQL ingestion service"""

    def setUp(self):
        self.integration = IntegrationFactory(
            integration_type='github',
            config={'token': 'test_token'}
        )
        self.app_integration = AppIntegrationFactory(
            integration=self.integration
        )

        self.service = GitHubGraphQLIngestionService(self.app_integration)

    def tearDown(self):
        if hasattr(self.service, 'graphql_client') and self.service.graphql_client:
            self.service.graphql_client.close()
        if hasattr(self.service, 'rest_client') and self.service.rest_client:
            self.service.rest_client.close()

    @patch('core.services.github_graphql_ingestion.GitHubGraphQLClient')
    def test_get_or_create_repository(self, mock_graphql_client_class):
        mock_client = Mock()
        mock_graphql_client_class.return_value = mock_client

        mock_client.get_repository_info.return_value = {
            'id': 'R_123',
            'name': 'test-repo',
            'description': 'Test repository',
            'url': 'https://github.com/owner/test-repo',
            'isPrivate': False,
            'defaultBranchRef': {'name': 'main'}
        }

        service = GitHubGraphQLIngestionService(self.app_integration)
        repository = service._get_or_create_repository('owner', 'test-repo')

        self.assertIsInstance(repository, GitHubRepository)
        self.assertEqual(repository.name, 'test-repo')
        self.assertEqual(repository.repo_owner, 'owner')
        self.assertEqual(repository.full_name, 'owner/test-repo')
        self.assertFalse(repository.is_private)
        self.assertEqual(repository.default_branch, 'main')

    @patch('core.services.github_graphql_ingestion.GitHubGraphQLClient')
    def test_ingest_single_issue_from_graphql(self, mock_graphql_client_class):
        """Test single issue ingestion from GraphQL data"""
        repository = GitHubRepository.objects.create(
            name='test-repo',
            repo_owner='owner',
            full_name='owner/test-repo',
            app_integration=self.app_integration
        )
        self.service.repository = repository

        issue_data = {
            'id': 'I_123',
            'number': 1,
            'title': 'Test Issue',
            'body': 'Issue body',
            'state': 'OPEN',
            'author': {'login': 'testuser'},
            'authorAssociation': 'CONTRIBUTOR',
            'assignees': {'nodes': [{'login': 'assignee1'}]},
            'labels': {'nodes': [{'name': 'bug'}]},
            'milestone': None,
            'locked': False,
            'createdAt': '2023-01-01T00:00:00Z',
            'updatedAt': '2023-01-02T00:00:00Z',
            'closedAt': None,
            'url': 'https://github.com/owner/test-repo/issues/1',
            'comments': {
                'edges': [
                    {
                        'node': {
                            'id': 'IC_456',
                            'body': 'Comment body',
                            'author': {'login': 'commenter'},
                            'authorAssociation': 'CONTRIBUTOR',
                            'createdAt': '2023-01-01T01:00:00Z',
                            'updatedAt': '2023-01-01T01:00:00Z',
                            'url': 'https://github.com/owner/test-repo/issues/1#issuecomment-456'
                        }
                    }
                ]
            }
        }

        self.service._ingest_single_issue_from_graphql(issue_data)

        from core.models.github_data import GitHubIssue, GitHubIssueComment
        issue = GitHubIssue.objects.get(repository=repository, number=1)
        self.assertEqual(issue.title, 'Test Issue')
        self.assertEqual(issue.state, 'open')
        self.assertEqual(issue.author, 'testuser')
        self.assertEqual(issue.assignees, ['assignee1'])
        self.assertEqual(issue.labels, ['bug'])

        comment = GitHubIssueComment.objects.get(issue=issue)
        self.assertEqual(comment.body, 'Comment body')
        self.assertEqual(comment.author, 'commenter')

    def test_parse_datetime(self):
        dt = self.service._parse_datetime('2023-01-01T00:00:00Z')
        self.assertIsInstance(dt, datetime)
        self.assertTrue(timezone.is_aware(dt))

        dt = self.service._parse_datetime(None)
        self.assertIsNone(dt)


class TestGitHubMigrationHelper(TestCase):

    def setUp(self):
        self.integration = IntegrationFactory(
            integration_type='github',
            config={'token': 'test_token'}
        )
        self.app_integration = AppIntegrationFactory(
            integration=self.integration
        )

    def test_migration_helper_initialization(self):
        from core.utils.github_migration_helper import GitHubMigrationHelper

        helper = GitHubMigrationHelper(self.app_integration)
        self.assertEqual(helper.app_integration, self.app_integration)
        self.assertIsNone(helper.rest_client)
        self.assertIsNone(helper.graphql_client)

    @patch('core.utils.github_migration_helper.GitHubAPIClient')
    @patch('core.utils.github_migration_helper.GitHubGraphQLClient')
    def test_performance_comparison(self, mock_graphql_client_class, mock_rest_client_class):
        from core.utils.github_migration_helper import GitHubMigrationHelper

        mock_rest_client = Mock()
        mock_graphql_client = Mock()
        mock_rest_client_class.return_value = mock_rest_client
        mock_graphql_client_class.return_value = mock_graphql_client

        mock_rest_client.get_issues.return_value = [
            {'id': 1, 'number': 1, 'title': 'Issue 1'},
            {'id': 2, 'number': 2, 'title': 'Issue 2'}
        ]
        mock_rest_client.get_issue_comments.return_value = [{'id': 101, 'body': 'Comment 1'}]

        mock_graphql_client.get_all_issues_with_comments.return_value = [
            {
                'id': 'I_1',
                'number': 1,
                'title': 'Issue 1',
                'comments': {'edges': [{'node': {'id': 'IC_101', 'body': 'Comment 1'}}]}
            },
            {
                'id': 'I_2',
                'number': 2,
                'title': 'Issue 2',
                'comments': {'edges': []}
            }
        ]

        helper = GitHubMigrationHelper(self.app_integration)
        results = helper.compare_issue_ingestion_performance('owner', 'repo', limit=2)

        self.assertIn('repository', results)
        self.assertIn('rest_api', results)
        self.assertIn('graphql', results)
        self.assertIn('improvement', results)

        self.assertEqual(results['rest_api']['api_calls'], 3)  # 1 for issues + 2 for comments
        self.assertEqual(results['rest_api']['issues_processed'], 2)

        self.assertEqual(results['graphql']['api_calls'], 1)  # Single GraphQL query
        self.assertEqual(results['graphql']['issues_processed'], 2)


if __name__ == '__main__':
    pytest.main([__file__])
