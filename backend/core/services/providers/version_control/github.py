import logging
from typing import Dict, List, Optional, Any, Tuple

from core.services.providers.version_control import VCProvider, register_provider
from core.services.github_client import GitHubAPIClient

logger = logging.getLogger(__name__)


@register_provider('github')
class GitHubProvider(VCProvider):

    provider_name = 'github'

    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self._client: Optional[GitHubAPIClient] = None

    def _get_client(self) -> GitHubAPIClient:
        if not self._client:
            token = self.credentials.get('token')
            if not token:
                raise ValueError("GitHub token not found in credentials")
            self._client = GitHubAPIClient(token)
        return self._client

    def validate_credentials(self) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            client = self._get_client()
            user_info = client._make_request('GET', '/user')
            metadata = {
                'login': user_info.get('login'),
                'name': user_info.get('name'),
                'avatar_url': user_info.get('avatar_url'),
                'html_url': user_info.get('html_url'),
            }
            return True, '', metadata
        except Exception as e:
            return False, str(e), {}

    def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        client = self._get_client()
        data = client.get_repository_info(owner, repo)
        return {
            'id': str(data.get('id')),
            'name': data.get('name'),
            'owner': data.get('owner', {}).get('login'),
            'full_name': data.get('full_name'),
            'description': data.get('description', ''),
            'url': data.get('html_url'),
            'is_private': data.get('private', False),
            'default_branch': data.get('default_branch', 'main'),
            'fork': data.get('fork', False),
            'stars': data.get('stargazers_count', 0),
            'watchers': data.get('watchers_count', 0),
            'forks': data.get('forks_count', 0),
            'open_issues': data.get('open_issues_count', 0),
        }

    def get_issues(self, owner: str, repo: str, state: str = 'all',
                   since: Optional[str] = None) -> List[Dict[str, Any]]:
        client = self._get_client()
        issues = client.get_issues(owner, repo, state=state, since=since)
        return [
            {
                'id': str(issue['id']),
                'number': issue['number'],
                'title': issue['title'],
                'body': issue.get('body', '') or '',
                'state': issue['state'],
                'author': issue.get('user', {}).get('login', ''),
                'author_association': issue.get('author_association', ''),
                'assignees': [user['login'] for user in issue.get('assignees', [])],
                'labels': [label['name'] for label in issue.get('labels', [])],
                'milestone': issue.get('milestone'),
                'locked': issue.get('locked', False),
                'created_at': issue['created_at'],
                'updated_at': issue['updated_at'],
                'closed_at': issue.get('closed_at'),
                'url': issue['html_url'],
            }
            for issue in issues
        ]

    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        client = self._get_client()
        comments = client.get_issue_comments(owner, repo, issue_number)
        return [
            {
                'id': str(comment['id']),
                'body': comment['body'],
                'author': comment.get('user', {}).get('login', ''),
                'author_association': comment.get('author_association', ''),
                'created_at': comment['created_at'],
                'updated_at': comment['updated_at'],
                'url': comment['html_url'],
            }
            for comment in comments
        ]

    def get_pull_requests(self, owner: str, repo: str, state: str = 'all',
                          since: Optional[str] = None) -> List[Dict[str, Any]]:
        client = self._get_client()
        prs = client.get_pull_requests(owner, repo, state=state, since=since)
        return [
            {
                'id': str(pr['id']),
                'number': pr['number'],
                'title': pr['title'],
                'body': pr.get('body', '') or '',
                'state': pr['state'],
                'author': pr.get('user', {}).get('login', ''),
                'author_association': pr.get('author_association', ''),
                'assignees': [user['login'] for user in pr.get('assignees', [])],
                'reviewers': [user['login'] for user in pr.get('requested_reviewers', [])],
                'labels': [label['name'] for label in pr.get('labels', [])],
                'milestone': pr.get('milestone'),
                'head_branch': pr.get('head', {}).get('ref', ''),
                'base_branch': pr.get('base', {}).get('ref', ''),
                'merged': pr.get('merged', False),
                'merged_at': pr.get('merged_at'),
                'merge_commit_sha': pr.get('merge_commit_sha', ''),
                'additions': pr.get('additions', 0),
                'deletions': pr.get('deletions', 0),
                'changed_files': pr.get('changed_files', 0),
                'created_at': pr['created_at'],
                'updated_at': pr['updated_at'],
                'closed_at': pr.get('closed_at'),
                'url': pr['html_url'],
            }
            for pr in prs
        ]

    def get_pull_request_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        client = self._get_client()
        comments = client.get_pull_request_comments(owner, repo, pr_number)
        return [
            {
                'id': str(comment['id']),
                'body': comment['body'],
                'author': comment.get('user', {}).get('login', ''),
                'author_association': comment.get('author_association', ''),
                'created_at': comment['created_at'],
                'updated_at': comment['updated_at'],
                'url': comment['html_url'],
            }
            for comment in comments
        ]

    def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        client = self._get_client()
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
        if self._client:
            self._client.close()
            self._client = None
