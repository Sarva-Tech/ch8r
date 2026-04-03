import uuid
from django.db import (models)

class KBStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    UPLOADING = 'uploading', 'Uploading'
    EXTRACTING = 'extracting', 'Extracting'
    PROCESSING = 'processing', 'Processing'
    PROCESSED = 'processed', 'Processed'
    REPROCESSING = 'reprocessing', 'Reprocessing'
    FAILED = 'failed', 'Failed'
    COMPLETED = 'completed', 'Completed'
    DUPLICATE = 'duplicate', 'Duplicate'

class KnowledgeBase(models.Model):
    SOURCE_CHOICES = [
        ('url', 'URL'),
        ('file', 'File'),
        ('text', 'Text'),
        ('github', 'GitHub')
    ]

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    application = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='knowledge_bases')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='file')
    path = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=KBStatus.choices,
        default=KBStatus.PENDING,
        help_text="Processing status of the knowledge base item."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)

        try:
            chunk_uuids = [str(chunk.uuid) for chunk in self.chunks.all()]
            if chunk_uuids:
                from core.services.ingestion import delete_vectors_from_qdrant
                delete_vectors_from_qdrant(chunk_uuids)
                logger.info(f"[KnowledgeBase] Deleted {len(chunk_uuids)} Qdrant vectors for KB {self.uuid}")

            content = self.metadata.get('content', '')
            if content:
                from core.services.duplicate_detector import DuplicateDetector

                detector = DuplicateDetector()
                detector.remove_content_hash(content, self.application)
                logger.info(f"[KnowledgeBase] Deleted ContentHash for KB {self.uuid}")

        except Exception as e:
            logger.error(f"[KnowledgeBase] Error during cleanup for KB {self.uuid}: {e}")

        super().delete(*args, **kwargs)

    def __str__(self):
        return f"KnowledgeBase {self.uuid} for Application {self.application_id}"
