import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from django.utils import timezone

from core.models.github_data import (
    GitHubRepository, GitHubIssue, GitHubIssueComment, 
    GitHubPullRequest, GitHubPRComment, GitHubPRFile
)
from core.services.abstractions import DataProcessor

logger = logging.getLogger(__name__)


class BaseDataProcessor(DataProcessor):
    def validate_data(self, data: Dict[str, Any]) -> bool:
        return isinstance(data, dict) and bool(data)
    
    @staticmethod
    def parse_iso_datetime(date_string: Optional[str]) -> Optional[datetime]:
        if not date_string:
            return None
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse datetime '{date_string}': {e}")
            return None
    
    @staticmethod
    def extract_user_login(user_data: Dict[str, Any]) -> str:
        return user_data.get('login', '') if user_data else ''
    
    @staticmethod
    def extract_label_names(labels_data: List[Dict[str, Any]]) -> List[str]:
        return [label.get('name', '') for label in labels_data if label.get('name')]


class RepositoryDataProcessor(BaseDataProcessor):
    def process_data(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_data(repo_data):
            raise ValueError("Invalid repository data")
            
        return {
            'name': repo_data.get('name', ''),
            'description': repo_data.get('description', ''),
            'url': repo_data.get('html_url', ''),
            'is_private': repo_data.get('private', False),
            'default_branch': repo_data.get('default_branch', 'main')
        }


class IssueDataProcessor(BaseDataProcessor):
    def process_data(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'number': issue_data['number'],
            'title': issue_data['title'],
            'body': issue_data.get('body', '') or '',
            'state': issue_data['state'],
            'author': self.extract_user_login(issue_data.get('user')),
            'author_association': issue_data.get('author_association', ''),
            'assignees': [user['login'] for user in issue_data.get('assignees', [])],
            'labels': self.extract_label_names(issue_data.get('labels', [])),
            'milestone': issue_data.get('milestone'),
            'locked': issue_data.get('locked', False),
            'created_at': self.parse_iso_datetime(issue_data['created_at']),
            'updated_at': self.parse_iso_datetime(issue_data['updated_at']),
            'closed_at': self.parse_iso_datetime(issue_data.get('closed_at')),
            'url': issue_data['html_url']
        }
    
    def process_comment_data(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'body': comment_data['body'],
            'author': self.extract_user_login(comment_data.get('user')),
            'author_association': comment_data.get('author_association', ''),
            'created_at': self.parse_iso_datetime(comment_data['created_at']),
            'updated_at': self.parse_iso_datetime(comment_data['updated_at']),
            'url': comment_data['html_url']
        }


class PullRequestDataProcessor(BaseDataProcessor):
    def process_data(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'number': pr_data['number'],
            'title': pr_data['title'],
            'body': pr_data.get('body', '') or '',
            'state': pr_data['state'],
            'author': self.extract_user_login(pr_data.get('user')),
            'author_association': pr_data.get('author_association', ''),
            'assignees': [user['login'] for user in pr_data.get('assignees', [])],
            'labels': self.extract_label_names(pr_data.get('labels', [])),
            'milestone': pr_data.get('milestone'),
            'head_branch': pr_data['head']['ref'] if pr_data.get('head') else '',
            'base_branch': pr_data['base']['ref'] if pr_data.get('base') else '',
            'merged': pr_data.get('merged', False),
            'merged_at': self.parse_iso_datetime(pr_data.get('merged_at')),
            'merge_commit_sha': pr_data.get('merge_commit_sha', ''),
            'additions': pr_data.get('additions', 0),
            'deletions': pr_data.get('deletions', 0),
            'changed_files': pr_data.get('changed_files', 0),
            'created_at': self.parse_iso_datetime(pr_data['created_at']),
            'updated_at': self.parse_iso_datetime(pr_data['updated_at']),
            'closed_at': self.parse_iso_datetime(pr_data.get('closed_at')),
            'url': pr_data['html_url']
        }
    
    def process_comment_data(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'body': comment_data['body'],
            'author': self.extract_user_login(comment_data.get('user')),
            'author_association': comment_data.get('author_association', ''),
            'created_at': self.parse_iso_datetime(comment_data['created_at']),
            'updated_at': self.parse_iso_datetime(comment_data['updated_at']),
            'url': comment_data['html_url']
        }
    
    def process_file_data(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'status': file_data['status'],
            'additions': file_data.get('additions', 0),
            'deletions': file_data.get('deletions', 0),
            'changes': file_data.get('changes', 0),
            'patch': file_data.get('patch', '') or '',
            'blob_url': file_data.get('blob_url', ''),
            'raw_url': file_data.get('raw_url', ''),
            'contents_url': file_data.get('contents_url', '')
        }
