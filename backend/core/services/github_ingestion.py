import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from core.models.github_data import (
    GitHubRepository, GitHubIssue, GitHubIssueComment, GitHubPullRequest,
    GitHubPRComment, GitHubPRFile
)
from core.models import AppIntegration
from core.services.github_client import GitHubAPIClient
from core.services.ingestion import chunk_text, embed_text, embed_sparse
from core.models import IngestedChunk
from core.qdrant import qdrant, COLLECTION_NAME
from qdrant_client.http.models import PointStruct
from qdrant_client.models import SparseVector
import uuid

logger = logging.getLogger(__name__)


class GitHubDataIngestionService:
    """Production-grade GitHub data ingestion service"""

    def __init__(self, app_integration: AppIntegration):
        self.app_integration = app_integration
        self.github_client = None
        self.repository = None

    def _get_github_client(self) -> GitHubAPIClient:
        """Initialize GitHub client"""
        if not self.github_client:
            token = self.app_integration.integration.config.get('token')
            if not token:
                raise ValueError("GitHub token not found in integration config")
            self.github_client = GitHubAPIClient(token)
        return self.github_client

    def _get_or_create_repository(self, owner: str, repo: str) -> GitHubRepository:
        """Get or create repository record"""
        full_name = f"{owner}/{repo}"

        repository, created = GitHubRepository.objects.get_or_create(
            full_name=full_name,
            defaults={
                'name': repo,
                'repo_owner': owner,
                'app_integration': self.app_integration,
                'ingestion_status': 'pending'
            }
        )

        if created:
            try:
                client = self._get_github_client()
                repo_info = client.get_repository_info(owner, repo)

                repository.description = repo_info.get('description', '')
                repository.url = repo_info.get('html_url', '')
                repository.is_private = repo_info.get('private', False)
                repository.default_branch = repo_info.get('default_branch', 'main')
                repository.save()

                logger.info(f"Created repository record for {full_name}")
            except Exception as e:
                logger.error(f"Failed to fetch repository info for {full_name}: {e}")
                repository.delete()
                raise

        self.repository = repository
        return repository

    def _ingest_issues(self, owner: str, repo: str, since: Optional[str] = None):
        """Ingest issues and comments"""
        client = self._get_github_client()

        try:
            issues = client.get_issues(owner, repo, state='all', since=since)
            logger.info(f"Found {len(issues)} issues for {owner}/{repo}")

            for issue_data in issues:
                self._ingest_single_issue(issue_data, owner, repo)

        except Exception as e:
            logger.error(f"Failed to ingest issues for {owner}/{repo}: {e}")
            raise

    def _ingest_single_issue(self, issue_data: Dict[str, Any], owner: str, repo: str):
        """Ingest a single issue and its comments"""
        client = self._get_github_client()

        with transaction.atomic():
            issue, created = GitHubIssue.objects.update_or_create(
                repository=self.repository,
                github_id=issue_data['id'],
                defaults={
                    'number': issue_data['number'],
                    'title': issue_data['title'],
                    'body': issue_data.get('body', '') or '',
                    'state': issue_data['state'],
                    'author': issue_data['user']['login'] if issue_data.get('user') else '',
                    'author_association': issue_data.get('author_association', ''),
                    'assignees': [user['login'] for user in issue_data.get('assignees', [])],
                    'labels': [label['name'] for label in issue_data.get('labels', [])],
                    'milestone': issue_data.get('milestone'),
                    'locked': issue_data.get('locked', False),
                    'created_at': self._parse_datetime(issue_data['created_at']),
                    'updated_at': self._parse_datetime(issue_data['updated_at']),
                    'closed_at': self._parse_datetime(issue_data.get('closed_at')),
                    'url': issue_data['html_url']
                }
            )

            try:
                comments = client.get_issue_comments(owner, repo, issue_data['number'])
                for comment_data in comments:
                    try:
                        GitHubIssueComment.objects.update_or_create(
                            issue=issue,
                            github_id=comment_data['id'],
                            defaults={
                                'body': comment_data['body'],
                                'author': comment_data['user']['login'] if comment_data.get('user') else '',
                                'author_association': comment_data.get('author_association', ''),
                                'created_at': self._parse_datetime(comment_data['created_at']),
                                'updated_at': self._parse_datetime(comment_data['updated_at']),
                                'url': comment_data['html_url']
                            }
                        )
                    except Exception as inner_e:
                        logger.warning(f"Failed to ingest comment {comment_data.get('id', 'unknown')}: {inner_e}")
                        continue

                logger.debug(f"Ingested issue #{issue.number} with {len(comments)} comments")

            except Exception as e:
                logger.warning(f"Failed to ingest comments for issue #{issue.number}: {e}")
                import traceback
                logger.warning(f"Comment ingestion traceback: {traceback.format_exc()}")

    def _ingest_pull_requests(self, owner: str, repo: str, since: Optional[str] = None):
        """Ingest pull requests, comments, and files"""
        client = self._get_github_client()

        try:
            logger.info(f"[GitHubIngestion] Starting PR ingestion for {owner}/{repo}")
            prs = client.get_pull_requests(owner, repo, state='all', since=since)
            logger.info(f"Found {len(prs)} pull requests for {owner}/{repo}")

            for i, pr_data in enumerate(prs, 1):
                try:
                    logger.info(f"[GitHubIngestion] Processing PR {i}/{len(prs)}: #{pr_data.get('number', 'unknown')}")
                    self._ingest_single_pull_request(pr_data, owner, repo)
                except Exception as inner_e:
                    logger.warning(f"Failed to ingest PR #{pr_data.get('number', 'unknown')}: {inner_e}")
                    continue

            logger.info(f"[GitHubIngestion] Completed PR ingestion for {owner}/{repo}")

        except Exception as e:
            logger.error(f"Failed to ingest pull requests for {owner}/{repo}: {e}")
            import traceback
            logger.warning(f"PR ingestion traceback: {traceback.format_exc()}")
            raise

    def _ingest_single_pull_request(self, pr_data: Dict[str, Any], owner: str, repo: str):
        """Ingest a single pull request and its related data"""
        client = self._get_github_client()
        pr_number = pr_data.get('number', 'unknown')

        try:
            logger.info(f"[GitHubIngestion] Ingesting PR #{pr_number} for {owner}/{repo}")

            with transaction.atomic():
                pr, created = GitHubPullRequest.objects.update_or_create(
                    repository=self.repository,
                    github_id=pr_data['id'],
                    defaults={
                        'number': pr_data['number'],
                        'title': pr_data['title'],
                        'body': pr_data.get('body', '') or '',
                        'state': pr_data['state'],
                        'author': pr_data['user']['login'] if pr_data.get('user') else '',
                        'author_association': pr_data.get('author_association', ''),
                        'assignees': [user['login'] for user in pr_data.get('assignees', [])],
                        'reviewers': [user['login'] for user in pr_data.get('requested_reviewers', [])],
                        'labels': [label['name'] for label in pr_data.get('labels', [])],
                        'milestone': pr_data.get('milestone'),
                        'head_branch': pr_data['head']['ref'] if pr_data.get('head') else '',
                        'base_branch': pr_data['base']['ref'] if pr_data.get('base') else '',
                        'merged': pr_data.get('merged', False),
                        'merged_at': self._parse_datetime(pr_data.get('merged_at')),
                        'merge_commit_sha': pr_data.get('merge_commit_sha', ''),
                        'additions': pr_data.get('additions', 0),
                        'deletions': pr_data.get('deletions', 0),
                        'changed_files': pr_data.get('changed_files', 0),
                        'created_at': self._parse_datetime(pr_data['created_at']),
                        'updated_at': self._parse_datetime(pr_data['updated_at']),
                        'closed_at': self._parse_datetime(pr_data.get('closed_at')),
                        'url': pr_data['html_url']
                    }
                )

                logger.debug(f"[GitHubIngestion] {'Created' if created else 'Updated'} PR #{pr_number}")

                try:
                    logger.debug(f"[GitHubIngestion] Fetching comments for PR #{pr_number}")
                    comments = client.get_pull_request_comments(owner, repo, pr_data['number'])
                    logger.debug(f"[GitHubIngestion] Found {len(comments)} comments for PR #{pr_number}")

                    for comment_data in comments:
                        GitHubPRComment.objects.update_or_create(
                            pull_request=pr,
                            github_id=comment_data['id'],
                            defaults={
                                'body': comment_data['body'],
                                'author': comment_data['user']['login'] if comment_data.get('user') else '',
                                'author_association': comment_data.get('author_association', ''),
                                'created_at': self._parse_datetime(comment_data['created_at']),
                                'updated_at': self._parse_datetime(comment_data['updated_at']),
                                'url': comment_data['html_url']
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to ingest comments for PR #{pr_number}: {e}")

                try:
                    logger.debug(f"[GitHubIngestion] Fetching files for PR #{pr_number}")
                    files = client.get_pull_request_files(owner, repo, pr_data['number'])
                    logger.debug(f"[GitHubIngestion] Found {len(files)} files for PR #{pr_number}")

                    for file_data in files:
                        GitHubPRFile.objects.update_or_create(
                            pull_request=pr,
                            filename=file_data['filename'],
                            defaults={
                                'status': file_data['status'],
                                'additions': file_data.get('additions', 0),
                                'deletions': file_data.get('deletions', 0),
                                'changes': file_data.get('changes', 0),
                                'patch': file_data.get('patch', '') or '',
                                'blob_url': file_data.get('blob_url', ''),
                                'raw_url': file_data.get('raw_url', ''),
                                'contents_url': file_data.get('contents_url', '')
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to ingest files for PR #{pr_number}: {e}")

                logger.debug(f"[GitHubIngestion] Completed PR #{pr_number}")

        except Exception as e:
            logger.error(f"Failed to ingest single PR #{pr_number}: {e}")
            import traceback
            logger.warning(f"Single PR ingestion traceback: {traceback.format_exc()}")
            raise

    def _ingest_code_comments(self, owner: str, repo: str):
        """Ingest code comments from key files"""
        logger.info("Code comment ingestion not yet implemented")
        pass

    def _create_knowledge_base_content(self) -> str:
        """Create knowledge base content from all ingested data"""
        content_parts = []

        if not self.repository:
            return ""

        content_parts.append(f"# Repository: {self.repository.full_name}")
        if self.repository.description:
            content_parts.append(f"Description: {self.repository.description}")
        content_parts.append("")

        issues = self.repository.issues.all()
        if issues:
            content_parts.append("## Issues")
            for issue in issues[:50]:
                content_parts.append(f"### Issue #{issue.number}: {issue.title}")
                content_parts.append(f"State: {issue.state}")
                content_parts.append(f"Author: {issue.author}")
                if issue.body:
                    content_parts.append(f"Description: {issue.body[:500]}...")
                if issue.labels:
                    content_parts.append(f"Labels: {', '.join(issue.labels)}")

                comments = issue.comments.all()[:5]
                for comment in comments:
                    content_parts.append(f"Comment by {comment.author}: {comment.body[:200]}...")
                content_parts.append("")

        prs = self.repository.pull_requests.all()
        if prs:
            content_parts.append("## Pull Requests")
            for pr in prs[:50]:
                content_parts.append(f"### PR #{pr.number}: {pr.title}")
                content_parts.append(f"State: {pr.state}")
                content_parts.append(f"Author: {pr.author}")
                if pr.body:
                    content_parts.append(f"Description: {pr.body[:500]}...")
                if pr.labels:
                    content_parts.append(f"Labels: {', '.join(pr.labels)}")
                content_parts.append("")

        return "\n".join(content_parts)

    def _ingest_to_knowledge_base(self):
        """Ingest all GitHub data into the knowledge base"""
        from core.models import KnowledgeBase
        from core.tasks.kb import send_kb_update

        app = self.app_integration.application
        full_name = self.repository.full_name
        logger.info(f"[GitHubIngestion] _ingest_to_knowledge_base: app={app.name}, repo={full_name}")

        kb, created = KnowledgeBase.objects.get_or_create(
            application=app,
            source_type='github',
            path=full_name,
            defaults={
                'metadata': {
                    'source': 'github',
                    'repository': full_name,
                    'content': self._create_knowledge_base_content()
                },
                'status': 'pending'
            }
        )
        logger.info(f"[GitHubIngestion] KnowledgeBase {'created' if created else 'found'}: uuid={kb.uuid}, status={kb.status}")

        if not created:
            logger.info(f"[GitHubIngestion] Updating existing KB content for {full_name}")
            kb.metadata['content'] = self._create_knowledge_base_content()
            kb.save()

        send_kb_update(kb, 'processing')

        from core.services.ingestion import ingest_kb
        logger.info(f"[GitHubIngestion] Calling ingest_kb for kb={kb.uuid}")
        ingest_kb(kb, app)
        logger.info(f"[GitHubIngestion] ingest_kb completed for kb={kb.uuid}, final status={kb.status}")

        send_kb_update(kb, kb.status)

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from GitHub API"""
        if not dt_str:
            return None

        try:
            if dt_str.endswith('Z'):
                naive_dt = datetime.fromisoformat(dt_str.replace('Z', ''))
                return timezone.make_aware(naive_dt)
            else:
                return datetime.fromisoformat(dt_str)
        except Exception as e:
            logger.warning(f"Failed to parse datetime: {dt_str}, error: {e}")
            return timezone.now()

    def ingest_repository(self, owner: str, repo: str, since: Optional[str] = None):
        """Main method to ingest all GitHub data for a repository"""
        try:
            logger.info(f"[GitHubIngestion] Starting ingestion for {owner}/{repo} (since={since})")

            repository = self._get_or_create_repository(owner, repo)
            repository.ingestion_status = 'running'
            repository.save()
            logger.info(f"[GitHubIngestion] Repository record ready: id={repository.id}, full_name={repository.full_name}")

            logger.info(f"[GitHubIngestion] Ingesting issues...")
            self._ingest_issues(owner, repo, since)

            logger.info(f"[GitHubIngestion] Ingesting pull requests...")
            self._ingest_pull_requests(owner, repo, since)

            logger.info(f"[GitHubIngestion] Building knowledge base content...")
            self._ingest_to_knowledge_base()

            repository.ingestion_status = 'completed'
            repository.last_ingested_at = timezone.now()
            repository.save()
            logger.info(f"[GitHubIngestion] Completed ingestion for {owner}/{repo}")

        except Exception as e:
            logger.error(f"[GitHubIngestion] Failed ingestion for {owner}/{repo}: {e}", exc_info=True)
            if self.repository:
                self.repository.ingestion_status = 'failed'
                self.repository.save()
            raise

        finally:
            if self.github_client:
                self.github_client.close()
