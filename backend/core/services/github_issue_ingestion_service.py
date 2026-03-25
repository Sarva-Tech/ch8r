import logging
from typing import Dict, List, Any
from django.db import transaction

from core.models.github_data import GitHubIssue, GitHubIssueComment
from core.services.github_client import GitHubAPIClient
from core.services.github_data_processors import IssueDataProcessor

logger = logging.getLogger(__name__)


class GitHubIssueIngestionService:
    def __init__(self, github_client: GitHubAPIClient, repository):
        self.github_client = github_client
        self.repository = repository
        self.processor = IssueDataProcessor()
    
    def ingest_issues(self, owner: str, repo: str, since: str = None):
        try:
            issues = self.github_client.get_issues(owner, repo, state='all', since=since)
            logger.info(f"Found {len(issues)} issues for {owner}/{repo}")
            
            for issue_data in issues:
                self._ingest_single_issue(issue_data, owner, repo)
                
        except Exception as e:
            logger.error(f"Failed to ingest issues for {owner}/{repo}: {e}")
            raise
    
    def _ingest_single_issue(self, issue_data: Dict[str, Any], owner: str, repo: str):
        try:
            with transaction.atomic():
                issue = self._create_or_update_issue(issue_data)
                self._ingest_issue_comments(issue, owner, repo, issue_data['number'])
                
        except Exception as e:
            logger.error(f"Failed to ingest issue #{issue_data.get('number', 'unknown')}: {e}")
            raise
    
    def _create_or_update_issue(self, issue_data: Dict[str, Any]) -> GitHubIssue:
        processed_data = self.processor.process_data(issue_data)
        
        issue, created = GitHubIssue.objects.update_or_create(
            repository=self.repository,
            github_id=issue_data['id'],
            defaults=processed_data
        )
        
        action = "Created" if created else "Updated"
        logger.debug(f"{action} issue #{issue.number}: {issue.title}")
        
        return issue
    
    def _ingest_issue_comments(self, issue: GitHubIssue, owner: str, repo: str, issue_number: int):
        try:
            comments = self.github_client.get_issue_comments(owner, repo, issue_number)
            logger.debug(f"Found {len(comments)} comments for issue #{issue_number}")
            
            for comment_data in comments:
                self._create_or_update_comment(issue, comment_data)
                
        except Exception as e:
            logger.warning(f"Failed to ingest comments for issue #{issue_number}: {e}")
    
    def _create_or_update_comment(self, issue: GitHubIssue, comment_data: Dict[str, Any]):
        try:
            processed_data = self.processor.process_comment_data(comment_data)
            
            comment, created = GitHubIssueComment.objects.update_or_create(
                issue=issue,
                github_id=comment_data['id'],
                defaults=processed_data
            )
            
            if created:
                logger.debug(f"Created comment {comment.github_id}")
                
        except Exception as e:
            logger.warning(f"Failed to ingest comment {comment_data.get('id', 'unknown')}: {e}")
