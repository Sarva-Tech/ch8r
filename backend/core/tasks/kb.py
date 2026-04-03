import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from core.consts import DASHBOARD_USER_ID_PREFIX, LIVE_UPDATES_PREFIX
from core.models import KnowledgeBase
from core.models.knowledge_base import KBStatus
from core.services import extract_text_from_file, ingest_kb
from core.services.url_ingestion import URLIngestionService

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

from abc import ABC, abstractmethod

class KBProcessor(ABC):
    """Abstract base class for knowledge base processors."""
    
    @abstractmethod
    def extract_content(self, kb: KnowledgeBase) -> bool:
        """Extract content from knowledge base item."""
        pass
    
    @abstractmethod
    def should_process(self, kb: KnowledgeBase) -> bool:
        """Check if this processor should handle the given KB item."""
        pass
    
    def finalize_processing(self, kb: KnowledgeBase) -> bool:
        """Finalize processing after content extraction."""
        kb.refresh_from_db()
        if kb.status != KBStatus.DUPLICATE:
            kb.status = KBStatus.PROCESSED
            kb.save()
            send_kb_update(kb, kb.status)
            
            kb.status = KBStatus.COMPLETED
            self.post_processing_hook(kb)
            kb.save()
            send_kb_update(kb, kb.status)
        return True
    
    def post_processing_hook(self, kb: KnowledgeBase):
        """Hook for post-processing actions specific to each processor."""
        pass
    
    def process(self, kb: KnowledgeBase) -> bool:
        """Complete processing workflow."""
        success = self.extract_content(kb)
        if not success:
            return False
        
        # Common processing steps
        app = kb.application
        kb.status = KBStatus.PROCESSING
        kb.save()
        send_kb_update(kb, kb.status)
        
        ingest_kb(kb, app)
        
        return self.finalize_processing(kb)


class FileProcessor(KBProcessor):
    """Processor for file-based knowledge base items."""
    
    def should_process(self, kb: KnowledgeBase) -> bool:
        return kb.source_type == 'file'
    
    def extract_content(self, kb: KnowledgeBase) -> bool:
        is_modified = (kb.metadata or {}).get("is_modified_by_user", False)
        if not is_modified:
            kb.status = KBStatus.EXTRACTING
            kb.save()
            send_kb_update(kb, kb.status)
            
            content = extract_text_from_file(kb.path)
            
            kb.metadata = kb.metadata or {}
            kb.metadata['content'] = content
            kb.save()
        return True


class TextProcessor(KBProcessor):
    """Processor for text-based knowledge base items."""
    
    def should_process(self, kb: KnowledgeBase) -> bool:
        return kb.source_type == 'text'
    
    def extract_content(self, kb: KnowledgeBase) -> bool:
        # Text items already have content in metadata, no extraction needed
        return True


class URLProcessor(KBProcessor):
    """Processor for URL-based knowledge base items."""
    
    def should_process(self, kb: KnowledgeBase) -> bool:
        return kb.source_type == 'url'
    
    def extract_content(self, kb: KnowledgeBase) -> bool:
        url_service = URLIngestionService()
        success = url_service.extract_url_content(kb)
        
        if not success:
            # URL extraction failed, status already set by the service
            return False
        
        return True
    
    def post_processing_hook(self, kb: KnowledgeBase):
        """Update extraction timestamp for URLs when processing completes."""
        if kb.metadata:
            kb.metadata['extraction_timestamp'] = kb.updated_at.isoformat()
            kb.save(update_fields=['metadata'])


def get_processor(kb: KnowledgeBase) -> KBProcessor:
    """Factory function to get appropriate processor for KB item."""
    processors = [FileProcessor(), TextProcessor(), URLProcessor()]
    
    for processor in processors:
        if processor.should_process(kb):
            return processor
    
    raise ValueError(f"No processor found for source_type: {kb.source_type}")


def process_kb_item(kb: KnowledgeBase) -> bool:
    """Process a knowledge base item using appropriate processor."""
    try:
        processor = get_processor(kb)
        return processor.process(kb)
        
    except Exception as e:
        logger.error(f"Error processing KB {kb.uuid}: {str(e)}")
        metadata = kb.metadata or {}
        metadata['error'] = str(e)
        kb.metadata = metadata
        kb.status = KBStatus.FAILED
        kb.save()
        send_kb_update(kb, kb.status)
        return False

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
