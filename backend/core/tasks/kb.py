from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from core.consts import REGISTERED_USER_ID_PREFIX, LIVE_UPDATES_PREFIX
from core.models import KnowledgeBase
from core.models.knowledge_base import KBStatus
from core.services import extract_text_from_file, ingest_kb


def send_kb_update(kb, status):
    channel_layer = get_channel_layer()
    owner_id = kb.application.owner.id

    group_name = f"{LIVE_UPDATES_PREFIX}_{REGISTERED_USER_ID_PREFIX}_{owner_id}"

    data = {
        "id": str(kb.id),
        "uuid": str(kb.uuid),
        "status": status,
        "content": getattr(kb.metadata, "content", "") or "",
    }

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send.kb.updates",
            "data": data,
        }
    )

def process_kb_item(kb):
    if kb.source_type == 'file':
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


        kb.status = KBStatus.PROCESSED
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
        finally:
            kb.status = KBStatus.COMPLETED
            kb.save()
            send_kb_update(kb, kb.status)