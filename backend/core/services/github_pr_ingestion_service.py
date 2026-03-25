import logging
from typing import Dict, List, Any
from django.db import transaction

from core.models.github_data import GitHubPullRequest, GitHubPRComment, GitHubPRFile
from core.services.github_client import GitHubAPIClient
from core.services.github_data_processors import PullRequestDataProcessor

logger = logging.getLogger(__name__)


class GitHubPRIngestionService:
    def __init__(self, github_client: GitHubAPIClient, repository):
        self.github_client = github_client
        self.repository = repository
        self.processor = PullRequestDataProcessor()
    
    def ingest_pull_requests(self, owner: str, repo: str, since: str = None):
        try:
            prs = self.github_client.get_pull_requests(owner, repo, state='all', since=since)
            logger.info(f"Found {len(prs)} pull requests for {owner}/{repo}")
            
            for pr_data in prs:
                self._ingest_single_pr(pr_data, owner, repo)
                
        except Exception as e:
            logger.error(f"Failed to ingest pull requests for {owner}/{repo}: {e}")
            raise
    
    def _ingest_single_pr(self, pr_data: Dict[str, Any], owner: str, repo: str):
        try:
            with transaction.atomic():
                pr = self._create_or_update_pr(pr_data)
                self._ingest_pr_comments(pr, owner, repo, pr_data['number'])
                self._ingest_pr_files(pr, owner, repo, pr_data['number'])
                
        except Exception as e:
            logger.error(f"Failed to ingest PR #{pr_data.get('number', 'unknown')}: {e}")
            raise
    
    def _create_or_update_pr(self, pr_data: Dict[str, Any]) -> GitHubPullRequest:
        processed_data = self.processor.process_data(pr_data)
        
        pr, created = GitHubPullRequest.objects.update_or_create(
            repository=self.repository,
            github_id=pr_data['id'],
            defaults=processed_data
        )
        
        action = "Created" if created else "Updated"
        logger.debug(f"{action} PR #{pr.number}: {pr.title}")
        
        return pr
    
    def _ingest_pr_comments(self, pr: GitHubPullRequest, owner: str, repo: str, pr_number: int):
        try:
            comments = self.github_client.get_pull_request_comments(owner, repo, pr_number)
            logger.debug(f"Found {len(comments)} comments for PR #{pr_number}")
            
            for comment_data in comments:
                self._create_or_update_pr_comment(pr, comment_data)
                
        except Exception as e:
            logger.warning(f"Failed to ingest comments for PR #{pr_number}: {e}")
    
    def _create_or_update_pr_comment(self, pr: GitHubPullRequest, comment_data: Dict[str, Any]):
        try:
            processed_data = self.processor.process_comment_data(comment_data)
            
            comment, created = GitHubPRComment.objects.update_or_create(
                pull_request=pr,
                github_id=comment_data['id'],
                defaults=processed_data
            )
            
            if created:
                logger.debug(f"Created PR comment {comment.github_id}")
                
        except Exception as e:
            logger.warning(f"Failed to ingest PR comment {comment_data.get('id', 'unknown')}: {e}")
    
    def _ingest_pr_files(self, pr: GitHubPullRequest, owner: str, repo: str, pr_number: int):
        try:
            files = self.github_client.get_pull_request_files(owner, repo, pr_number)
            logger.debug(f"Found {len(files)} files for PR #{pr_number}")
            
            for file_data in files:
                self._create_or_update_pr_file(pr, file_data)
                
        except Exception as e:
            logger.warning(f"Failed to ingest files for PR #{pr_number}: {e}")
    
    def _create_or_update_pr_file(self, pr: GitHubPullRequest, file_data: Dict[str, Any]):
        try:
            processed_data = self.processor.process_file_data(file_data)
            
            file_record, created = GitHubPRFile.objects.update_or_create(
                pull_request=pr,
                filename=file_data['filename'],
                defaults=processed_data
            )
            
            if created:
                logger.debug(f"Created PR file {file_record.filename}")
                
        except Exception as e:
            logger.warning(f"Failed to ingest PR file {file_data.get('filename', 'unknown')}: {e}")
