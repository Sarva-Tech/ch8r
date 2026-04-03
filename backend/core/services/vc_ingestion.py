import logging
from datetime import datetime
from typing import Dict, Optional, Any
from django.utils import timezone
from django.db import transaction

from core.models.version_control import (
    VCRepository, VCIssue, VCIssueComment, VCPullRequest,
    VCPRComment, VCPRFile
)
from core.models import AppIntegration
from core.services.providers.version_control import VCProviderRegistry
from core.services.content_quality_filter import ContentQualityFilter

logger = logging.getLogger(__name__)


class VCIngestionService:
    def __init__(self, app_integration: AppIntegration, provider_name: Optional[str] = None):
        self.app_integration = app_integration
        self.provider_name = provider_name or self._detect_provider()
        self.provider = self._get_provider()
        self.repository: Optional[VCRepository] = None
        self.quality_filter = ContentQualityFilter()

    def _detect_provider(self) -> str:
        metadata = self.app_integration.metadata or {}
        if 'provider' in metadata:
            return metadata['provider']

        return 'github_graphql'

    def _get_provider(self):
        import json
        credentials = json.loads(self.app_integration.integration.credentials or '{}')
        return VCProviderRegistry.get_provider(self.provider_name, credentials)

    def _get_or_create_repository(self, owner: str, repo: str) -> VCRepository:
        full_name = f"{owner}/{repo}"

        repository, created = VCRepository.objects.get_or_create(
            app_integration=self.app_integration,
            full_name=full_name,
            provider=self.provider_name,
            defaults={
                'name': repo,
                'repo_owner': owner,
                'ingestion_status': 'pending'
            }
        )

        if created:
            try:
                repo_info = self.provider.get_repository_info(owner, repo)

                repository.external_id = repo_info.get('id', '')
                repository.description = repo_info.get('description', '')
                repository.url = repo_info.get('url', '')
                repository.is_private = repo_info.get('is_private', False)
                repository.default_branch = repo_info.get('default_branch', 'main')
                repository.save()

                logger.info(f"Created repository record for {full_name} ({self.provider_name})")
            except Exception as e:
                logger.error(f"Failed to fetch repository info for {full_name}: {e}")
                repository.delete()
                raise

        self.repository = repository
        return repository

    def _ingest_issues(self, owner: str, repo: str, since: Optional[str] = None):
        try:
            issues = self.provider.get_issues(owner, repo, state='all', since=since)
            logger.info(f"Found {len(issues)} issues for {owner}/{repo}")

            for issue_data in issues:
                self._ingest_single_issue(issue_data)

        except Exception as e:
            logger.error(f"Failed to ingest issues for {owner}/{repo}: {e}")
            raise

    def _ingest_single_issue(self, issue_data: Dict[str, Any]):
        with transaction.atomic():
            raw_body = issue_data.get('body', '') or ''
            cleaned_body = self.quality_filter.remove_emojis(raw_body)

            issue, created = VCIssue.objects.update_or_create(
                repository=self.repository,
                external_id=issue_data['id'],
                defaults={
                    'number': issue_data['number'],
                    'title': issue_data['title'],
                    'body': cleaned_body,
                    'state': issue_data['state'],
                    'author': issue_data.get('author', ''),
                    'author_association': issue_data.get('author_association', ''),
                    'assignees': issue_data.get('assignees', []),
                    'labels': issue_data.get('labels', []),
                    'milestone': issue_data.get('milestone'),
                    'locked': issue_data.get('locked', False),
                    'created_at': self.provider._parse_datetime(issue_data['created_at']),
                    'updated_at': self.provider._parse_datetime(issue_data['updated_at']),
                    'closed_at': self.provider._parse_datetime(issue_data.get('closed_at')),
                    'url': issue_data['url']
                }
            )

            try:
                owner = self.repository.repo_owner
                repo = self.repository.name
                comments = self.provider.get_issue_comments(owner, repo, issue_data['number'])
                for comment_data in comments:
                    try:
                        raw_comment_body = comment_data['body']
                        cleaned_comment_body = self.quality_filter.remove_emojis(raw_comment_body)

                        VCIssueComment.objects.update_or_create(
                            issue=issue,
                            external_id=comment_data['id'],
                            defaults={
                                'body': cleaned_comment_body,
                                'author': comment_data.get('author', ''),
                                'author_association': comment_data.get('author_association', ''),
                                'created_at': self.provider._parse_datetime(comment_data['created_at']),
                                'updated_at': self.provider._parse_datetime(comment_data['updated_at']),
                                'url': comment_data['url']
                            }
                        )
                    except Exception as inner_e:
                        logger.warning(f"Failed to ingest comment {comment_data.get('id', 'unknown')}: {inner_e}")
                        continue

                logger.debug(f"Ingested issue #{issue.number} with {len(comments)} comments")

            except Exception as e:
                logger.warning(f"Failed to ingest comments for issue #{issue.number}: {e}")

    def _ingest_pull_requests(self, owner: str, repo: str, since: Optional[str] = None):
        try:
            logger.info(f"[VCIngestion] Starting PR ingestion for {owner}/{repo}")
            prs = self.provider.get_pull_requests(owner, repo, state='all', since=since)
            logger.info(f"Found {len(prs)} pull requests for {owner}/{repo}")

            for i, pr_data in enumerate(prs, 1):
                try:
                    logger.info(f"[VCIngestion] Processing PR {i}/{len(prs)}: #{pr_data.get('number', 'unknown')}")
                    self._ingest_single_pull_request(pr_data)
                except Exception as inner_e:
                    logger.warning(f"Failed to ingest PR #{pr_data.get('number', 'unknown')}: {inner_e}")
                    continue

            logger.info(f"[VCIngestion] Completed PR ingestion for {owner}/{repo}")

        except Exception as e:
            logger.error(f"Failed to ingest pull requests for {owner}/{repo}: {e}")
            raise

    def _ingest_single_pull_request(self, pr_data: Dict[str, Any]):
        pr_number = pr_data.get('number', 'unknown')
        owner = self.repository.repo_owner
        repo = self.repository.name

        try:
            with transaction.atomic():
                # Clean PR body
                raw_body = pr_data.get('body', '') or ''
                cleaned_body = self.quality_filter.remove_emojis(raw_body)

                pr, created = VCPullRequest.objects.update_or_create(
                    repository=self.repository,
                    external_id=pr_data['id'],
                    defaults={
                        'number': pr_data['number'],
                        'title': pr_data['title'],
                        'body': cleaned_body,
                        'state': pr_data['state'],
                        'author': pr_data.get('author', ''),
                        'author_association': pr_data.get('author_association', ''),
                        'assignees': pr_data.get('assignees', []),
                        'reviewers': pr_data.get('reviewers', []),
                        'labels': pr_data.get('labels', []),
                        'milestone': pr_data.get('milestone'),
                        'head_branch': pr_data.get('head_branch', ''),
                        'base_branch': pr_data.get('base_branch', ''),
                        'merged': pr_data.get('merged', False),
                        'merged_at': self.provider._parse_datetime(pr_data.get('merged_at')),
                        'merge_commit_sha': pr_data.get('merge_commit_sha', ''),
                        'additions': pr_data.get('additions', 0),
                        'deletions': pr_data.get('deletions', 0),
                        'changed_files': pr_data.get('changed_files', 0),
                        'created_at': self.provider._parse_datetime(pr_data['created_at']),
                        'updated_at': self.provider._parse_datetime(pr_data['updated_at']),
                        'closed_at': self.provider._parse_datetime(pr_data.get('closed_at')),
                        'url': pr_data['url']
                    }
                )

                logger.debug(f"[VCIngestion] {'Created' if created else 'Updated'} PR #{pr_number}")

                try:
                    comments = self.provider.get_pull_request_comments(owner, repo, pr_data['number'])
                    for comment_data in comments:
                        raw_comment_body = comment_data['body']
                        cleaned_comment_body = self.quality_filter.remove_emojis(raw_comment_body)

                        VCPRComment.objects.update_or_create(
                            pull_request=pr,
                            external_id=comment_data['id'],
                            defaults={
                                'body': cleaned_comment_body,
                                'author': comment_data.get('author', ''),
                                'author_association': comment_data.get('author_association', ''),
                                'created_at': self.provider._parse_datetime(comment_data['created_at']),
                                'updated_at': self.provider._parse_datetime(comment_data['updated_at']),
                                'url': comment_data['url']
                            }
                        )
                except Exception as e:
                    logger.warning(f"Failed to ingest comments for PR #{pr_number}: {e}")

                try:
                    files = self.provider.get_pull_request_files(owner, repo, pr_data['number'])
                    for file_data in files:
                        VCPRFile.objects.update_or_create(
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

                logger.debug(f"[VCIngestion] Completed PR #{pr_number}")

        except Exception as e:
            logger.error(f"Failed to ingest single PR #{pr_number}: {e}")
            raise

    def _create_knowledge_base_content(self) -> str:
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
        from core.services.ingestion import ingest_kb

        app = self.app_integration.application
        full_name = self.repository.full_name
        logger.info(f"[VCIngestion] _ingest_to_knowledge_base: app={app.name}, repo={full_name}")

        kb, created = KnowledgeBase.objects.get_or_create(
            application=app,
            source_type='version_control',
            path=full_name,
            defaults={
                'metadata': {
                    'source': 'version_control',
                    'provider': self.provider_name,
                    'repository': full_name,
                    'content': self._create_knowledge_base_content()
                },
                'status': 'pending'
            }
        )
        logger.info(f"[VCIngestion] KnowledgeBase {'created' if created else 'found'}: uuid={kb.uuid}, status={kb.status}")

        if not created:
            logger.info(f"[VCIngestion] Updating existing KB content for {full_name}")
            kb.metadata['content'] = self._create_knowledge_base_content()
            kb.metadata['provider'] = self.provider_name
            kb.save()

        send_kb_update(kb, 'processing')

        logger.info(f"[VCIngestion] Calling ingest_kb for kb={kb.uuid}")
        ingest_kb(kb, app)
        logger.info(f"[VCIngestion] ingest_kb completed for kb={kb.uuid}, final status={kb.status}")

        send_kb_update(kb, kb.status)

    def ingest_repository(self, owner: str, repo: str, since: Optional[str] = None):
        try:
            logger.info(f"[VCIngestion] Starting ingestion for {owner}/{repo} (provider={self.provider_name}, since={since})")

            repository = self._get_or_create_repository(owner, repo)
            repository.ingestion_status = 'running'
            repository.save()
            logger.info(f"[VCIngestion] Repository record ready: id={repository.id}, full_name={repository.full_name}")

            logger.info(f"[VCIngestion] Ingesting issues...")
            self._ingest_issues(owner, repo, since)

            logger.info(f"[VCIngestion] Ingesting pull requests...")
            self._ingest_pull_requests(owner, repo, since)

            logger.info(f"[VCIngestion] Building knowledge base content...")
            self._ingest_to_knowledge_base()

            repository.ingestion_status = 'completed'
            repository.last_ingested_at = timezone.now()
            repository.save()
            logger.info(f"[VCIngestion] Completed ingestion for {owner}/{repo}")

        except Exception as e:
            logger.error(f"[VCIngestion] Failed ingestion for {owner}/{repo}: {e}", exc_info=True)
            if self.repository:
                self.repository.ingestion_status = 'failed'
                self.repository.save()
            raise

        finally:
            self.provider.close()
