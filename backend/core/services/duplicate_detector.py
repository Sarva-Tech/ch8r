import hashlib
import logging
from typing import Optional, List, Tuple
from django.utils import timezone

from core.models.content_hash import ContentHash
from core.models.application import Application
from core.models.knowledge_base import KnowledgeBase
from core.services.ai_client_service import AIClientService
from core.services.content_quality_filter import ContentQualityFilter

logger = logging.getLogger(__name__)


class DuplicateDetector:
    def __init__(self):
        logger.debug("[DuplicateDetector] Initialized for content deduplication")
        self._ai_client_service = AIClientService()
        self._quality_filter = ContentQualityFilter()
        self._replacement_triggered = False

    def get_content_fingerprint(self, content: str) -> str:
        return ContentHash.generate_content_hash(content)

    def _get_embedding(self, content: str, app: Application) -> Optional[List[float]]:
        content_hash = ContentHash.generate_content_hash(content)

        try:
            cached_hash = ContentHash.objects.get(
                app=app,
                content_hash=content_hash
            )
            if cached_hash.embedding:
                logger.info(f"[DuplicateDetector] Using cached embedding for {content_hash[:8]}...")
                return cached_hash.embedding
        except ContentHash.DoesNotExist:
            pass

        embedding = self._generate_new_embedding(content, app)

        if embedding:
            ContentHash.objects.update_or_create(
                app=app,
                content_hash=content_hash,
                defaults={
                    'embedding': embedding,
                    'content_type': 'text'
                }
            )
            logger.info(f"[DuplicateDetector] Cached new embedding for {content_hash[:8]}...")

        return embedding

    def _generate_new_embedding(self, content: str, app: Application) -> Optional[List[float]]:
        try:
            provider, model = self._ai_client_service.get_client_and_model(
                app=app,
                context='response',
                capability='embedding'
            )

            if not provider or not model:
                logger.warning("[DuplicateDetector] No embedding provider available for semantic similarity")
                return None

            embeddings = provider.embed(model, [content])
            return embeddings[0] if embeddings and embeddings[0] else None
        except Exception as e:
            logger.error(f"[DuplicateDetector] Failed to generate embedding: {e}")
            return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        try:
            import numpy as np
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)

            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except ImportError:
            logger.warning("[DuplicateDetector] numpy not available, using manual calculation")
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"[DuplicateDetector] Failed to calculate cosine similarity: {e}")
            return 0.0

    def find_similar_content(self, content: str, app: Application, threshold: float = 0.85, exclude_kb_uuid: str = None) -> List[Tuple[str, float]]:
        if not content or not app:
            return []

        content_embedding = self._get_embedding(content, app)
        if not content_embedding:
            logger.warning("[DuplicateDetector] Could not generate embedding for content")
            return []

        similar_content = []

        kbs = KnowledgeBase.objects.filter(application=app)
        if exclude_kb_uuid:
            kbs = kbs.exclude(uuid=exclude_kb_uuid)

        for kb in kbs:
            kb_content = kb.metadata.get('content', '')
            if not kb_content:
                continue

            kb_embedding = self._get_embedding(kb_content, app)
            if not kb_embedding:
                continue

            similarity = self._cosine_similarity(content_embedding, kb_embedding)

            if similarity >= threshold:
                similar_content.append((str(kb.uuid), similarity))
                logger.debug(f"[DuplicateDetector] Found similar content: kb={kb.uuid}, similarity={similarity:.3f}")

        similar_content.sort(key=lambda x: x[1], reverse=True)
        return similar_content

    def is_semantic_duplicate(self, content: str, app: Application, threshold: float = 0.85) -> bool:
        similar_content = self.find_similar_content(content, app, threshold)
        return len(similar_content) > 0

    def should_replace_content(self, new_content: str, existing_kb_uuid: str, app: Application, content_type: str = 'text') -> bool:
        try:
            existing_kb = KnowledgeBase.objects.get(uuid=existing_kb_uuid, application=app)
            existing_content = existing_kb.metadata.get('content', '')

            if not existing_content:
                logger.warning(f"[DuplicateDetector] No content found in existing KB: {existing_kb_uuid}")
                return True

            new_quality_score = self._quality_filter.calculate_quality_score(new_content, content_type)
            existing_quality_score = self._quality_filter.calculate_quality_score(existing_content, content_type)

            quality_improvement = new_quality_score - existing_quality_score
            should_replace = quality_improvement > 0.1

            logger.debug(f"[DuplicateDetector] Replacement decision: new_quality={new_quality_score:.3f}, "
                        f"existing_quality={existing_quality_score:.3f}, "
                        f"quality_improvement={quality_improvement:.3f}, "
                        f"should_replace={should_replace}")

            return should_replace

        except KnowledgeBase.DoesNotExist:
            logger.warning(f"[DuplicateDetector] Existing KB not found: {existing_kb_uuid}")
            return True
        except Exception as e:
            logger.error(f"[DuplicateDetector] Error in should_replace_content: {e}")
            return False

    def replace_content(self, old_kb_uuid: str, new_content: str, app: Application, content_type: str = 'text') -> bool:
        try:
            old_kb = KnowledgeBase.objects.get(uuid=old_kb_uuid, application=app)

            self._cleanup_old_content(old_kb)

            old_kb.metadata['content'] = new_content
            old_kb.status = 'pending'
            old_kb.save(update_fields=['metadata', 'status'])

            logger.info(f"[DuplicateDetector] Replaced content in KB: {old_kb_uuid}")
            return True

        except KnowledgeBase.DoesNotExist:
            logger.error(f"[DuplicateDetector] KB not found for replacement: {old_kb_uuid}")
            return False
        except Exception as e:
            logger.error(f"[DuplicateDetector] Error in replace_content: {e}")
            return False

    def _cleanup_old_content(self, kb: KnowledgeBase) -> bool:
        try:
            content = kb.metadata.get('content', '')
            if content:
                self.remove_content_hash(content, kb.application)

            from core.services.ingestion import delete_vectors_from_qdrant

            chunk_uuids = [str(chunk.uuid) for chunk in kb.chunks.all()]
            if chunk_uuids:
                delete_vectors_from_qdrant(chunk_uuids)

            kb.chunks.all().delete()

            logger.debug(f"[DuplicateDetector] Cleaned up old content for KB: {kb.uuid}")
            return True

        except Exception as e:
            logger.error(f"[DuplicateDetector] Error in cleanup_old_content: {e}")
            return False

    def handle_semantic_duplicate(self, new_content: str, app: Application, kb_uuid: str, content_type: str = 'text') -> bool:
        self._replacement_triggered = False

        similar_content = self.find_similar_content(new_content, app, threshold=0.85, exclude_kb_uuid=kb_uuid)

        if not similar_content:
            return True

        existing_kb_uuid, similarity = similar_content[0]

        if self.should_replace_content(new_content, existing_kb_uuid, app, content_type):
            success = self.replace_content(existing_kb_uuid, new_content, app, content_type)
            if success:
                logger.info(f"[DuplicateDetector] Replaced lower-quality content: {existing_kb_uuid} with similarity {similarity:.3f}")
                self._replacement_triggered = True
                return False
            else:
                logger.error(f"[DuplicateDetector] Failed to replace content: {existing_kb_uuid}")
                return False
        else:
            logger.info(f"[DuplicateDetector] Keeping existing higher-quality content: {existing_kb_uuid} with similarity {similarity:.3f}")
            return False

    def _was_replacement_triggered(self) -> bool:
        return self._replacement_triggered

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
