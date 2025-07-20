from celery import shared_task

from core.models import KnowledgeBase
from core.services import extract_text_from_file, ingest_kb


def process_kb_item(kb):

    if kb.source_type == 'file':
        content = extract_text_from_file(kb.path)
        kb.metadata = kb.metadata or {}
        kb.metadata['content'] = content
        kb.save()

    if kb.source_type in ['file', 'text']:
        app = kb.application
        ingest_kb(kb, app)


@shared_task
def process_kb(kb_ids):
    kb_items = KnowledgeBase.objects.filter(id__in=kb_ids)

    for kb in kb_items:
        kb.status = 'extracting' if kb.source_type == 'file' else 'processing'
        kb.save()

        try:
            process_kb_item(kb)
            kb.status = 'processed'
        except Exception as e:
            metadata = kb.metadata or {}
            metadata['error'] = str(e)
            kb.metadata = metadata
            kb.status = 'failed'
        finally:
            kb.save()