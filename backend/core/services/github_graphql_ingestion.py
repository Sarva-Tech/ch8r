import logging
from datetime import datetime
import hashlib
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction

from core.models.github_data import (
    GitHubRepository, GitHubIssue, GitHubIssueComment, GitHubPullRequest,
    GitHubPRComment, GitHubPRFile
)
from core.models import AppIntegration
from core.services.github_graphql_client import GitHubGraphQLClient
from core.services.github_client import GitHubAPIClient
from core.services.ingestion import chunk_text, embed_text, embed_sparse
from core.models import IngestedChunk
from core.qdrant import qdrant, COLLECTION_NAME
from qdrant_client.http.models import PointStruct
from qdrant_client.models import SparseVector
import uuid

logger = logging.getLogger(__name__)


def _extract_numeric_id_from_global_id(global_id: str) -> int:
    hash_object = hashlib.md5(global_id.encode())
    hex_digest = hash_object.hexdigest()
    return int(hex_digest[:8], 16)


class GitHubGraphQLIngestionService:
    def __init__(self, app_integration: AppIntegration):
        self.app_integration = app_integration
        self.graphql_client = None
        self.rest_client = None  # Still needed for some operations like PR files
        self.repository = None

    def _get_graphql_client(self) -> GitHubGraphQLClient:
        if not self.graphql_client:
            token = self.app_integration.integration.config.get('token')
            if not token:
                raise ValueError("GitHub token not found in integration config")
            self.graphql_client = GitHubGraphQLClient(token)
        return self.graphql_client

    def _get_rest_client(self) -> GitHubAPIClient:
        if not self.rest_client:
            token = self.app_integration.integration.config.get('token')
            if not token:
                raise ValueError("GitHub token not found in integration config")
            self.rest_client = GitHubAPIClient(token)
        return self.rest_client

    def _get_or_create_repository(self, owner: str, repo: str) -> GitHubRepository:
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
                client = self._get_graphql_client()
                repo_info = client.get_repository_info(owner, repo)

                repository.description = repo_info.get('description', '')
                repository.url = repo_info.get('url', '')
                repository.is_private = repo_info.get('isPrivate', False)
                repository.default_branch = repo_info.get('defaultBranchRef', {}).get('name', 'main')
                repository.save()

                logger.info(f"Created repository record for {full_name}")
            except Exception as e:
                logger.error(f"Failed to fetch repository info for {full_name}: {e}")
                repository.delete()
                raise

        self.repository = repository
        return repository

    def _ingest_issues(self, owner: str, repo: str, since: Optional[str] = None):
        try:
            client = self._get_graphql_client()

            logger.info(f"[GraphQLIngestion] Starting bulk issue ingestion for {owner}/{repo}")
            issues_data = client.get_all_issues_with_comments(
                owner=owner,
                repo=repo,
                states=['OPEN', 'CLOSED'],
                since=since
            )

            logger.info(f"[GraphQLIngestion] Processing {len(issues_data)} issues from GraphQL")

            for i, issue_data in enumerate(issues_data, 1):
                try:
                    logger.info(f"[GraphQLIngestion] Processing issue {i}/{len(issues_data)}: #{issue_data.get('number', 'unknown')}")
                    self._ingest_single_issue_from_graphql(issue_data)
                except Exception as inner_e:
                    issue_number = issue_data.get('number', 'unknown')
                    logger.warning(f"Failed to ingest issue #{issue_number}: {inner_e}")
                    logger.debug(f"Issue data that failed: {issue_data}")
                    continue

            logger.info(f"[GraphQLIngestion] Processed {len(issues_data)} issues for {owner}/{repo}")

            logger.info(f"[GraphQLIngestion] Completed issue ingestion for {owner}/{repo}")

        except Exception as e:
            logger.error(f"Failed to ingest issues for {owner}/{repo}: {e}")
            raise

    def _ingest_single_issue_from_graphql(self, issue_data: Dict[str, Any]):
        with transaction.atomic():
            author = issue_data.get('author', {}).get('login', '') if issue_data.get('author') else ''

            assignees = [
                user['login'] for user in
                issue_data.get('assignees', {}).get('nodes', [])
            ]

            labels = [
                label['name'] for label in
                issue_data.get('labels', {}).get('nodes', [])
            ]

            milestone = issue_data.get('milestone', {}).get('title') if issue_data.get('milestone') else None

            issue, created = GitHubIssue.objects.update_or_create(
                repository=self.repository,
                github_id=issue_data['number'],
                defaults={
                    'number': issue_data['number'],
                    'title': issue_data['title'],
                    'body': issue_data.get('body', '') or '',
                    'state': issue_data['state'].lower(),
                    'author': author,
                    'author_association': issue_data.get('authorAssociation', ''),
                    'assignees': assignees,
                    'labels': labels,
                    'milestone': milestone,
                    'locked': issue_data.get('locked', False),
                    'created_at': self._parse_datetime(issue_data['createdAt']),
                    'updated_at': self._parse_datetime(issue_data['updatedAt']),
                    'closed_at': self._parse_datetime(issue_data.get('closedAt')),
                    'url': issue_data['url']
                }
            )

            comments_data = issue_data.get('comments', {}).get('edges', [])
            for comment_edge in comments_data:
                comment_data = comment_edge.get('node', {})
                if comment_data:
                    try:
                        self._ingest_issue_comment_from_graphql(issue, comment_data)
                    except Exception as inner_e:
                        logger.warning(f"Failed to ingest comment {comment_data.get('id', 'unknown')}: {inner_e}")
                        continue

            logger.debug(f"[GraphQLIngestion] {'Created' if created else 'Updated'} issue #{issue.number} with {len(comments_data)} comments")

    def _ingest_issue_comment_from_graphql(self, issue: GitHubIssue, comment_data: Dict[str, Any]):
        author = comment_data.get('author', {}).get('login', '') if comment_data.get('author') else ''

        GitHubIssueComment.objects.update_or_create(
            issue=issue,
            github_id=_extract_numeric_id_from_global_id(comment_data['id']),
            defaults={
                'body': comment_data['body'],
                'author': author,
                'author_association': comment_data.get('authorAssociation', ''),
                'created_at': self._parse_datetime(comment_data['createdAt']),
                'updated_at': self._parse_datetime(comment_data['updatedAt']),
                'url': comment_data['url']
            }
        )

    def _ingest_pull_requests(self, owner: str, repo: str, since: Optional[str] = None):
        try:
            graphql_client = self._get_graphql_client()
            rest_client = self._get_rest_client()

            logger.info(f"[GraphQLIngestion] Starting bulk PR ingestion for {owner}/{repo}")

            prs_data = graphql_client.get_all_pull_requests_with_comments(
                owner=owner,
                repo=repo,
                states=['OPEN', 'CLOSED', 'MERGED'],
                since=since
            )

            logger.info(f"[GraphQLIngestion] Processing {len(prs_data)} pull requests from GraphQL")

            for i, pr_data in enumerate(prs_data, 1):
                try:
                    logger.info(f"[GraphQLIngestion] Processing PR {i}/{len(prs_data)}: #{pr_data.get('number', 'unknown')}")
                    self._ingest_single_pull_request_from_graphql(pr_data, owner, repo, rest_client)
                except Exception as inner_e:
                    pr_number = pr_data.get('number', 'unknown')
                    logger.warning(f"Failed to ingest PR #{pr_number}: {inner_e}")
                    logger.debug(f"PR data that failed: {pr_data}")
                    continue

            logger.info(f"[GraphQLIngestion] Processed {len(prs_data)} pull requests for {owner}/{repo}")

            logger.info(f"[GraphQLIngestion] Completed PR ingestion for {owner}/{repo}")

        except Exception as e:
            logger.error(f"Failed to ingest pull requests for {owner}/{repo}: {e}")
            raise

    def _ingest_single_pull_request_from_graphql(self, pr_data: Dict[str, Any], owner: str, repo: str, rest_client: GitHubAPIClient):
        pr_number = pr_data.get('number', 'unknown')

        try:
            with transaction.atomic():
                author = pr_data.get('author', {}).get('login', '') if pr_data.get('author') else ''

                assignees = [
                    user['login'] for user in
                    pr_data.get('assignees', {}).get('nodes', [])
                ]

                reviewers = []

                labels = [
                    label['name'] for label in
                    pr_data.get('labels', {}).get('nodes', [])
                ]

                milestone = pr_data.get('milestone', {}).get('title') if pr_data.get('milestone') else None

                merge_commit_sha = pr_data.get('mergeCommit', {}).get('oid', '') if pr_data.get('mergeCommit') else ''

                pr, created = GitHubPullRequest.objects.update_or_create(
                    repository=self.repository,
                    github_id=pr_data['number'],
                    defaults={
                        'number': pr_data['number'],
                        'title': pr_data['title'],
                        'body': pr_data.get('body', '') or '',
                        'state': pr_data['state'].lower(),
                        'author': author,
                        'author_association': pr_data.get('authorAssociation', ''),
                        'assignees': assignees,
                        'reviewers': reviewers,
                        'labels': labels,
                        'milestone': milestone,
                        'head_branch': pr_data.get('headRefName', ''),
                        'base_branch': pr_data.get('baseRefName', ''),
                        'merged': pr_data.get('merged', False),
                        'merged_at': self._parse_datetime(pr_data.get('mergedAt')),
                        'merge_commit_sha': merge_commit_sha,
                        'additions': pr_data.get('additions', 0),
                        'deletions': pr_data.get('deletions', 0),
                        'changed_files': pr_data.get('changedFiles', 0),
                        'created_at': self._parse_datetime(pr_data['createdAt']),
                        'updated_at': self._parse_datetime(pr_data['updatedAt']),
                        'closed_at': self._parse_datetime(pr_data.get('closedAt')),
                        'url': pr_data['url']
                    }
                )

                logger.debug(f"[GraphQLIngestion] {'Created' if created else 'Updated'} PR #{pr_number}")

                comments_data = pr_data.get('comments', {}).get('edges', [])
                for comment_edge in comments_data:
                    comment_data = comment_edge.get('node', {})
                    if comment_data:
                        try:
                            self._ingest_pr_comment_from_graphql(pr, comment_data)
                        except Exception as inner_e:
                            logger.warning(f"Failed to ingest PR comment {comment_data.get('id', 'unknown')}: {inner_e}")
                            continue

                try:
                    logger.debug(f"[GraphQLIngestion] Fetching files for PR #{pr_number} via REST")
                    files = rest_client.get_pull_request_files(owner, repo, pr_data['number'])
                    logger.debug(f"[GraphQLIngestion] Found {len(files)} files for PR #{pr_number}")

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

                logger.debug(f"[GraphQLIngestion] Completed PR #{pr_number}")

        except Exception as e:
            logger.error(f"Failed to ingest single PR #{pr_number}: {e}")
            raise

    def _ingest_pr_comment_from_graphql(self, pull_request: GitHubPullRequest, comment_data: Dict[str, Any]):
        author = comment_data.get('author', {}).get('login', '') if comment_data.get('author') else ''

        GitHubPRComment.objects.update_or_create(
            pull_request=pull_request,
            github_id=_extract_numeric_id_from_global_id(comment_data['id']),
            defaults={
                'body': comment_data['body'],
                'author': author,
                'author_association': comment_data.get('authorAssociation', ''),
                'created_at': self._parse_datetime(comment_data['createdAt']),
                'updated_at': self._parse_datetime(comment_data['updatedAt']),
                'url': comment_data['url']
            }
        )

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
        from core.models import KnowledgeBase
        from core.tasks.kb import send_kb_update

        app = self.app_integration.application
        full_name = self.repository.full_name
        logger.info(f"[GraphQLIngestion] _ingest_to_knowledge_base: app={app.name}, repo={full_name}")

        kb, created = KnowledgeBase.objects.get_or_create(
            application=app,
            source_type='github',
            path=full_name,
            defaults={
                'metadata': {
                    'source': 'github',
                    'repository': full_name,
                    'content': self._create_knowledge_base_content(),
                    'ingestion_method': 'graphql'
                },
                'status': 'pending'
            }
        )
        logger.info(f"[GraphQLIngestion] KnowledgeBase {'created' if created else 'found'}: uuid={kb.uuid}, status={kb.status}")

        if not created:
            logger.info(f"[GraphQLIngestion] Updating existing KB content for {full_name}")
            kb.metadata['content'] = self._create_knowledge_base_content()
            kb.metadata['ingestion_method'] = 'graphql'
            kb.save()

        send_kb_update(kb, 'processing')

        from core.services.ingestion import ingest_kb
        logger.info(f"[GraphQLIngestion] Calling ingest_kb for kb={kb.uuid}")
        ingest_kb(kb, app)
        logger.info(f"[GraphQLIngestion] ingest_kb completed for kb={kb.uuid}, final status={kb.status}")

        send_kb_update(kb, kb.status)

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
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
        try:
            logger.info(f"[GraphQLIngestion] Starting GraphQL ingestion for {owner}/{repo} (since={since})")

            repository = self._get_or_create_repository(owner, repo)
            repository.ingestion_status = 'running'
            repository.save()
            logger.info(f"[GraphQLIngestion] Repository record ready: id={repository.id}, full_name={repository.full_name}")

            logger.info(f"[GraphQLIngestion] Ingesting issues using GraphQL...")
            self._ingest_issues(owner, repo, since)

            logger.info(f"[GraphQLIngestion] Ingesting pull requests using GraphQL...")
            self._ingest_pull_requests(owner, repo, since)

            logger.info(f"[GraphQLIngestion] Building knowledge base content...")
            self._ingest_to_knowledge_base()

            repository.ingestion_status = 'completed'
            repository.last_ingested_at = timezone.now()
            repository.save()
            logger.info(f"[GraphQLIngestion] Completed GraphQL ingestion for {owner}/{repo}")

        except Exception as e:
            logger.error(f"[GraphQLIngestion] Failed GraphQL ingestion for {owner}/{repo}: {e}", exc_info=True)
            if self.repository:
                self.repository.ingestion_status = 'failed'
                self.repository.save()
            raise

        finally:
            if self.graphql_client:
                self.graphql_client.close()
            if self.rest_client:
                self.rest_client.close()
