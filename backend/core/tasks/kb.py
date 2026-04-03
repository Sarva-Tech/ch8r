import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from core.consts import DASHBOARD_USER_ID_PREFIX, LIVE_UPDATES_PREFIX
from core.models import KnowledgeBase
from core.models.knowledge_base import KBStatus
from core.services import extract_text_from_file, ingest_kb

logger = logging.getLogger(__name__)


def send_kb_update(kb, status):
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning(f"[send_kb_update] Channel layer is None, skipping WS update for kb {kb.uuid}")
            return

        owner_id = kb.application.owner.id
        group_name = f"{LIVE_UPDATES_PREFIX}_{DASHBOARD_USER_ID_PREFIX}_{owner_id}"

        data = {
            "id": str(kb.id),
            "uuid": str(kb.uuid),
            "status": status,
        }

        logger.info(f"[send_kb_update] Sending status={status} for kb={kb.uuid} to group={group_name}")

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send.kb.updates",
                "data": data,
            }
        )
        logger.info(f"[send_kb_update] Successfully sent update for kb={kb.uuid}")
    except Exception as e:
        logger.error(f"[send_kb_update] Failed to send WS update for kb={kb.uuid}: {e}", exc_info=True)

def process_kb_item(kb):
    if kb.source_type == 'file':
        is_modified = (kb.metadata or {}).get("is_modified_by_user", False)

        if not is_modified:
            kb.status = KBStatus.EXTRACTING
            kb.save()
            send_kb_update(kb, kb.status)

            content = extract_text_from_file(kb.path)

            kb.metadata = kb.metadata or {}
            kb.metadata['content'] = content
            kb.save()

    if kb.source_type in ['file', 'text']:
        app = kb.application

        kb.status = KBStatus.PROCESSING
        kb.save()
        send_kb_update(kb, kb.status)

        ingest_kb(kb, app)

        kb.refresh_from_db()
        if kb.status != KBStatus.DUPLICATE:
            kb.status = KBStatus.PROCESSED
            kb.save()
            send_kb_update(kb, kb.status)

            kb.status = KBStatus.COMPLETED
            kb.save()
            send_kb_update(kb, kb.status)

@shared_task
def process_kb(kb_ids):
    kb_items = KnowledgeBase.objects.filter(id__in=kb_ids).select_related('application__owner')

    for kb in kb_items:
        try:
            process_kb_item(kb)
        except Exception as e:
            metadata = kb.metadata or {}
            metadata['error'] = str(e)
            kb.metadata = metadata
            kb.status = KBStatus.FAILED
            kb.save()
            send_kb_update(kb, kb.status)
