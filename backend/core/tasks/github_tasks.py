import logging
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone
from datetime import datetime, timedelta

from core.models import AppIntegration
from core.models.github_data import GitHubRepository
from core.services.github_ingestion import GitHubDataIngestionService
from core.consts import DASHBOARD_USER_ID_PREFIX, LIVE_UPDATES_PREFIX

logger = logging.getLogger(__name__)


def send_github_ingestion_update(repository, ingestion_status):
    try:
        channel_layer = get_channel_layer()
        owner_id = repository.app_integration.application.owner.id
        group_name = f"{LIVE_UPDATES_PREFIX}_{DASHBOARD_USER_ID_PREFIX}_{owner_id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send.kb.updates",
                "data": {
                    "id": str(repository.id),
                    "repository": repository.full_name,
                    "ingestion_status": ingestion_status,
                },
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send WebSocket update for {repository.full_name}: {e}")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_github_repository_task(self, app_integration_id, owner, repo, since=None):
    """Celery task for GitHub repository ingestion"""
    logger.info(f"[Task] ingest_github_repository_task started: {owner}/{repo} (app_integration={app_integration_id}, retry={self.request.retries})")
    try:
        app_integration = AppIntegration.objects.select_related(
            'application__owner', 'integration'
        ).get(id=app_integration_id)
        logger.info(f"[Task] AppIntegration found: id={app_integration_id}, app={app_integration.application.name}")

        ingestion_service = GitHubDataIngestionService(app_integration, use_graphql=True)
        ingestion_service.ingest_repository(owner, repo, since)

        logger.info(f"[Task] ingest_repository completed for {owner}/{repo}")

        try:
            repository = GitHubRepository.objects.get(
                app_integration_id=app_integration_id,
                full_name=f'{owner}/{repo}'
            )
            send_github_ingestion_update(repository, 'completed')
        except GitHubRepository.DoesNotExist:
            logger.warning(f"[Task] GitHubRepository not found after ingestion: {owner}/{repo}")

        return {
            'status': 'success',
            'repository': f'{owner}/{repo}',
            'completed_at': timezone.now().isoformat()
        }

    except AppIntegration.DoesNotExist:
        logger.error(f"[Task] AppIntegration {app_integration_id} not found")
        raise

    except Exception as exc:
        logger.error(f"[Task] ingest_github_repository_task failed for {owner}/{repo}: {exc}", exc_info=True)

        try:
            repository = GitHubRepository.objects.get(
                app_integration_id=app_integration_id,
                full_name=f'{owner}/{repo}'
            )
            repository.ingestion_status = 'failed'
            repository.save()
            send_github_ingestion_update(repository, 'failed')

            from core.models import KnowledgeBase
            from core.tasks.kb import send_kb_update
            kb = KnowledgeBase.objects.filter(
                application=repository.app_integration.application,
                source_type='github',
                path=repository.full_name,
            ).first()
            if kb:
                kb.status = 'failed'
                kb.save(update_fields=['status'])
                send_kb_update(kb, 'failed')
                logger.info(f"[Task] Marked KB {kb.uuid} as failed")
        except Exception as inner_exc:
            logger.warning(f"[Task] Failed to update failure status: {inner_exc}")

        if self.request.retries < self.max_retries:
            logger.info(f"[Task] Retrying (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        else:
            logger.error(f"[Task] Exhausted retries for {owner}/{repo}")
            raise


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def sync_all_github_repositories_task(self, app_integration_id):
    """Sync all repositories for a given integration"""
    try:
        logger.info(f"Starting sync for all GitHub repositories for integration {app_integration_id}")

        app_integration = AppIntegration.objects.get(id=app_integration_id)
        repositories = GitHubRepository.objects.filter(
            app_integration=app_integration,
            ingestion_status='completed'
        )

        results = []
        for repository in repositories:
            try:
                owner, repo = repository.full_name.split('/')

                since = (timezone.now() - timedelta(days=7)).isoformat()

                ingestion_service = GitHubDataIngestionService(app_integration, use_graphql=True)
                ingestion_service.ingest_repository(owner, repo, since)

                results.append({
                    'repository': repository.full_name,
                    'status': 'success'
                })

                logger.info(f"Successfully synced {repository.full_name}")

            except Exception as e:
                logger.error(f"Failed to sync {repository.full_name}: {e}")
                results.append({
                    'repository': repository.full_name,
                    'status': 'failed',
                    'error': str(e)
                })

        logger.info(f"Completed sync for {len(results)} repositories")
        return {
            'status': 'completed',
            'results': results,
            'completed_at': timezone.now().isoformat()
        }

    except AppIntegration.DoesNotExist:
        logger.error(f"AppIntegration {app_integration_id} not found")
        raise

    except Exception as exc:
        logger.error(f"GitHub sync task failed: {exc}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
        else:
            raise


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def cleanup_old_github_data_task(self, days_old=90):
    """Clean up old GitHub data to save storage space"""
    try:
        logger.info(f"Starting cleanup of GitHub data older than {days_old} days")

        cutoff_date = timezone.now() - timedelta(days=days_old)

        old_repositories = GitHubRepository.objects.filter(
            last_ingested_at__lt=cutoff_date,
            ingestion_status='completed'
        )

        deleted_count = 0
        for repository in old_repositories:
            try:
                repository_name = repository.full_name
                repository.delete()
                deleted_count += 1
                logger.info(f"Deleted old repository: {repository_name}")

            except Exception as e:
                logger.error(f"Failed to delete repository {repository.full_name}: {e}")

        logger.info(f"Deleted {deleted_count} old GitHub repositories")
        return {
            'status': 'completed',
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }

    except Exception as exc:
        logger.error(f"GitHub cleanup task failed: {exc}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
        else:
            raise


@shared_task(bind=True, max_retries=1, default_retry_delay=15)
def update_github_repository_status_task(self, repository_id):
    """Update repository status and metadata"""
    try:
        from core.services.github_client import GitHubAPIClient

        repository = GitHubRepository.objects.get(id=repository_id)
        owner, repo = repository.full_name.split('/')

        token = repository.app_integration.integration.config.get('token')
        if not token:
            logger.error("No GitHub token found for repository")
            return

        client = GitHubAPIClient(token)

        repo_info = client.get_repository_info(owner, repo)

        repository.description = repo_info.get('description', '')
        repository.url = repo_info.get('html_url', '')
        repository.is_private = repo_info.get('private', False)
        repository.default_branch = repo_info.get('default_branch', 'main')
        repository.save()

        logger.info(f"Updated metadata for {repository.full_name}")
        return {
            'status': 'success',
            'repository': repository.full_name,
            'updated_at': timezone.now().isoformat()
        }

    except GitHubRepository.DoesNotExist:
        logger.error(f"Repository {repository_id} not found")
        raise

    except Exception as exc:
        logger.error(f"Failed to update repository status: {exc}")

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=15)
        else:
            raise
