import logging
from typing import Dict, List, Optional, Any

from core.services.providers.version_control import VCProvider, register_provider
from core.services.github_graphql_client import GitHubGraphQLClient
from core.services.github_client import GitHubAPIClient

logger = logging.getLogger(__name__)


@register_provider('github_graphql')
class GitHubGraphQLProvider(VCProvider):
    provider_name = 'github_graphql'

    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self._graphql_client: Optional[GitHubGraphQLClient] = None
        self._rest_client: Optional[GitHubAPIClient] = None

    def _get_graphql_client(self) -> GitHubGraphQLClient:
        if not self._graphql_client:
            token = self.credentials.get('token')
            if not token:
                raise ValueError("GitHub token not found in credentials")
            self._graphql_client = GitHubGraphQLClient(token)
        return self._graphql_client

    def _get_rest_client(self) -> GitHubAPIClient:
        if not self._rest_client:
            token = self.credentials.get('token')
            if not token:
                raise ValueError("GitHub token not found in credentials")
            self._rest_client = GitHubAPIClient(token)
        return self._rest_client

    def validate_credentials(self) -> tuple[bool, str, Dict[str, Any]]:
        try:
            client = self._get_graphql_client()
            query = """
            query {
                viewer {
                    login
                    name
                    avatarUrl
                    url
                }
            }
            """
            result = client.execute_query(query)
            viewer = result.get('data', {}).get('viewer', {})
            metadata = {
                'login': viewer.get('login'),
                'name': viewer.get('name'),
                'avatar_url': viewer.get('avatarUrl'),
                'html_url': viewer.get('url'),
            }
            return True, '', metadata
        except Exception as e:
            return False, str(e), {}

    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        client = self._get_graphql_client()
        data = client.get_repository_info(owner, repo)
        return {
            'id': data.get('id'),
            'name': data.get('name'),
            'owner': owner,
            'full_name': f"{owner}/{repo}",
            'description': data.get('description', ''),
            'url': data.get('url'),
            'is_private': data.get('isPrivate', False),
            'default_branch': data.get('defaultBranchRef', {}).get('name', 'main'),
            'fork': data.get('isFork', False),
            'stars': data.get('stargazerCount', 0),
            'watchers': 0,
            'forks': data.get('forkCount', 0),
            'open_issues': data.get('issues', {}).get('totalCount', 0),
        }

    def get_issues(self, owner: str, repo: str, state: str = 'all',
                   since: Optional[str] = None) -> List[Dict[str, Any]]:
        client = self._get_graphql_client()

        states = []
        if state == 'all':
            states = ['OPEN', 'CLOSED']
        elif state == 'open':
            states = ['OPEN']
        elif state == 'closed':
            states = ['CLOSED']

        issues_data = client.get_all_issues_with_comments(owner, repo, states=states, since=since)

        return [
            {
                'id': str(issue['number']),
                'number': issue['number'],
                'title': issue['title'],
                'body': issue.get('body', '') or '',
                'state': issue['state'].lower(),
                'author': issue.get('author', {}).get('login', ''),
                'author_association': issue.get('authorAssociation', ''),
                'assignees': [user['login'] for user in issue.get('assignees', {}).get('nodes', [])],
                'labels': [label['name'] for label in issue.get('labels', {}).get('nodes', [])],
                'milestone': issue.get('milestone', {}).get('title') if issue.get('milestone') else None,
                'locked': issue.get('locked', False),
                'created_at': issue['createdAt'],
                'updated_at': issue['updatedAt'],
                'closed_at': issue.get('closedAt'),
                'url': issue['url'],
            }
            for issue in issues_data
        ]

    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        logger.debug("GitHubGraphQLProvider: get_issue_comments - comments usually pre-fetched")
        return []

    def get_pull_requests(self, owner: str, repo: str, state: str = 'all',
                          since: Optional[str] = None) -> List[Dict[str, Any]]:
        client = self._get_graphql_client()

        states = []
        if state == 'all':
            states = ['OPEN', 'CLOSED', 'MERGED']
        elif state == 'open':
            states = ['OPEN']
        elif state == 'closed':
            states = ['CLOSED', 'MERGED']
        elif state == 'merged':
            states = ['MERGED']

        prs_data = client.get_all_pull_requests_with_comments(owner, repo, states=states, since=since)

        return [
            {
                'id': str(pr['number']),
                'number': pr['number'],
                'title': pr['title'],
                'body': pr.get('body', '') or '',
                'state': pr['state'].lower(),
                'author': pr.get('author', {}).get('login', ''),
                'author_association': pr.get('authorAssociation', ''),
                'assignees': [user['login'] for user in pr.get('assignees', {}).get('nodes', [])],
                'reviewers': [],  # GraphQL has different field for reviewers
                'labels': [label['name'] for label in pr.get('labels', {}).get('nodes', [])],
                'milestone': pr.get('milestone', {}).get('title') if pr.get('milestone') else None,
                'head_branch': pr.get('headRefName', ''),
                'base_branch': pr.get('baseRefName', ''),
                'merged': pr.get('merged', False),
                'merged_at': pr.get('mergedAt'),
                'merge_commit_sha': pr.get('mergeCommit', {}).get('oid', '') if pr.get('mergeCommit') else '',
                'additions': pr.get('additions', 0),
                'deletions': pr.get('deletions', 0),
                'changed_files': pr.get('changedFiles', 0),
                'created_at': pr['createdAt'],
                'updated_at': pr['updatedAt'],
                'closed_at': pr.get('closedAt'),
                'url': pr['url'],
            }
            for pr in prs_data
        ]

    def get_pull_request_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        logger.debug("GitHubGraphQLProvider: get_pull_request_comments - comments usually pre-fetched")
        return []

    def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        client = self._get_rest_client()
        files = client.get_pull_request_files(owner, repo, pr_number)
        return [
            {
                'filename': file['filename'],
                'status': file['status'],
                'additions': file.get('additions', 0),
                'deletions': file.get('deletions', 0),
                'changes': file.get('changes', 0),
                'patch': file.get('patch', ''),
                'blob_url': file.get('blob_url', ''),
                'raw_url': file.get('raw_url', ''),
            }
            for file in files
        ]

    def close(self):
        if self._graphql_client:
            self._graphql_client.close()
            self._graphql_client = None
        if self._rest_client:
            self._rest_client.close()
            self._rest_client = None
