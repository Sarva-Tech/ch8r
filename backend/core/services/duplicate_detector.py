import hashlib
import logging
from typing import Optional

from core.models.content_hash import ContentHash
from core.models.application import Application

logger = logging.getLogger(__name__)


class DuplicateDetector:
    def __init__(self):
        logger.debug("[DuplicateDetector] Initialized for content deduplication")

    def get_content_fingerprint(self, content: str) -> str:
        return ContentHash.generate_content_hash(content)

    def is_duplicate(self, content: str, app: Application, content_type: str = 'text') -> bool:
        if not content or not app:
            return False

        content_hash = self.get_content_fingerprint(content)

        try:
            ContentHash.objects.get(app=app, content_hash=content_hash)
            logger.debug(f"[DuplicateDetector] Found duplicate content hash: {content_hash[:8]}...")
            return True
        except ContentHash.DoesNotExist:
            return False

    def store_content_hash(self, content: str, app: Application, content_type: str = 'text') -> bool:
        if not content or not app:
            return False

        content_hash = self.get_content_fingerprint(content)

        try:
            ContentHash.objects.create(
                app=app,
                content_hash=content_hash,
                content_type=content_type
            )
            logger.debug(f"[DuplicateDetector] Stored content hash: {content_hash[:8]}...")
            return True
        except Exception as e:
            logger.error(f"[DuplicateDetector] Failed to store content hash: {e}")
            return False

    def remove_content_hash(self, content: str, app: Application) -> bool:
        if not content or not app:
            return False

        content_hash = self.get_content_fingerprint(content)

        try:
            deleted_count, _ = ContentHash.objects.filter(
                app=app,
                content_hash=content_hash
            ).delete()

            if deleted_count > 0:
                logger.debug(f"[DuplicateDetector] Removed content hash: {content_hash[:8]}...")
            return deleted_count > 0
        except Exception as e:
            logger.error(f"[DuplicateDetector] Failed to remove content hash: {e}")
            return False

    def get_duplicate_stats(self, app: Application) -> dict:
        if not app:
            return {}

        try:
            total_hashes = ContentHash.objects.filter(app=app).count()
            content_type_stats = {}

            for content_type in ContentHash.objects.filter(app=app).values_list('content_type', flat=True).distinct():
                count = ContentHash.objects.filter(app=app, content_type=content_type).count()
                content_type_stats[content_type] = count

            return {
                'total_unique_content': total_hashes,
                'content_type_breakdown': content_type_stats
            }
        except Exception as e:
            logger.error(f"[DuplicateDetector] Failed to get stats: {e}")
            return {}
