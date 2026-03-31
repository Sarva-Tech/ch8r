import logging
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone
from datetime import datetime, timedelta

from core.models import AppIntegration
from core.models.version_control import VCRepository
from core.services.vc_ingestion import VCIngestionService
from core.consts import DASHBOARD_USER_ID_PREFIX, LIVE_UPDATES_PREFIX

logger = logging.getLogger(__name__)


def send_vc_ingestion_update(repository, ingestion_status):
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
                    "provider": repository.provider,
                    "ingestion_status": ingestion_status,
                },
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send WebSocket update for {repository.full_name}: {e}")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_vc_repository_task(self, app_integration_id, owner, repo, since=None, provider='github_graphql'):
    logger.info(f"[Task] ingest_vc_repository_task started: {owner}/{repo} "
                f"(app_integration={app_integration_id}, provider={provider}, retry={self.request.retries})")

    try:
        app_integration = AppIntegration.objects.select_related(
            'application__owner', 'integration'
        ).get(id=app_integration_id)
        logger.info(f"[Task] AppIntegration found: id={app_integration_id}, app={app_integration.application.name}")

        ingestion_service = VCIngestionService(app_integration, provider_name=provider)
        ingestion_service.ingest_repository(owner, repo, since)

        logger.info(f"[Task] ingest_repository completed for {owner}/{repo}")

        try:
            repository = VCRepository.objects.get(
                app_integration_id=app_integration_id,
                full_name=f'{owner}/{repo}'
            )
            send_vc_ingestion_update(repository, 'completed')
        except VCRepository.DoesNotExist:
            logger.warning(f"[Task] VCRepository not found after ingestion: {owner}/{repo}")

        return {
            'status': 'success',
            'repository': f'{owner}/{repo}',
            'provider': provider,
            'completed_at': timezone.now().isoformat()
        }

    except AppIntegration.DoesNotExist:
        logger.error(f"[Task] AppIntegration {app_integration_id} not found")
        raise

    except Exception as exc:
        logger.error(f"[Task] ingest_vc_repository_task failed for {owner}/{repo}: {exc}", exc_info=True)

        try:
            repository = VCRepository.objects.get(
                app_integration_id=app_integration_id,
                full_name=f'{owner}/{repo}'
            )
            repository.ingestion_status = 'failed'
            repository.save()
            send_vc_ingestion_update(repository, 'failed')

            from core.models import KnowledgeBase
            from core.tasks.kb import send_kb_update
            kb = KnowledgeBase.objects.filter(
                application=repository.app_integration.application,
                source_type='version_control',
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
