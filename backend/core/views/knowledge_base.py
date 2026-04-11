from django.core.files.storage import default_storage
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from core.models import KnowledgeBase, Application, IngestedChunk, ContentHash
from core.serializers.knowledge_base import (
    KnowledgeBaseViewSerializer, KnowledgeBaseItemSerializer, KnowledgeBaseCreateSerializer,
    CrawlingEnableSerializer, CrawlingDataSerializer, CrawlingStatsSerializer
)
from core.serializers import ApplicationViewSerializer
from core.permissions import HasAPIKeyPermission
from core.services.ingestion import delete_vectors_from_qdrant
from core.services.kb_utils import create_kb_records, parse_kb_from_request, format_text_uri
from core.services.ai_client_service import AIClientService
from core.services.url_ingestion import URLIngestionService
from core.tasks.kb import process_kb_item, process_kb
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.none()
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action == 'create':
            return KnowledgeBaseCreateSerializer
        return KnowledgeBaseViewSerializer

    def get_queryset(self):
        application_uuid = self.kwargs.get('application_uuid')
        return KnowledgeBase.objects.filter(
            application__uuid=application_uuid,
            application__owner=self.request.user
        ).exclude(source_type='crawled_url')

    def list(self, request, *args, **kwargs):
        application_uuid = kwargs.get('application_uuid')
        application = get_object_or_404(
            Application.objects.select_related('owner').prefetch_related('knowledge_bases'),
            uuid=application_uuid, owner=request.user
        )

        app_data = ApplicationViewSerializer(application).data
        kb_queryset = application.knowledge_bases.exclude(source_type='crawled_url')
        kb_data = KnowledgeBaseViewSerializer(kb_queryset, many=True).data
        app_data['knowledge_base'] = kb_data

        return Response({'application': app_data})

    def create(self, request, *args, **kwargs):
        application_uuid = kwargs.get('application_uuid')
        application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)

        parsed_items = parse_kb_from_request(request)
        logger.info(f"Parsed items for KB creation: {parsed_items}")

        serializer = self.get_serializer_class()(data={"items": parsed_items}, context={"request": request})

        if not serializer.is_valid():
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items = serializer.validated_data['items']
        logger.info(f"Validated items: {items}")

        created_kbs = create_kb_records(application, items)

        ai_client_service = AIClientService()
        _, embedding_model = ai_client_service.get_client_and_model(
            app=application, context='response', capability='embedding'
        )

        errors = {}
        if not embedding_model:
            errors["embedding_model"] = f"Embedding model not found for application {application.name}. Please configure an EMBEDDING model."

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        process_kb.delay([kb.id for kb in created_kbs])

        serialized_kbs = KnowledgeBaseViewSerializer(created_kbs, many=True)
        return Response({"kbs": serialized_kbs.data}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT")

    def partial_update(self, request, *args, **kwargs):
        kb = self.get_object()
        content = request.data.get("content")

        if content is None:
            raise ValidationError({"content": "This field is required."})

        fields_to_update = ["metadata"]
        kb.metadata = kb.metadata or {}
        kb.metadata["content"] = content
        kb.metadata["is_modified_by_user"] = True

        if kb.source_type == 'text':
            kb.path = format_text_uri(content)
            fields_to_update.append("path")

        kb.save(update_fields=fields_to_update)

        # TODO: We need to check whether text & embedding models are configured here as well
        process_kb.delay([kb.id])

        return Response(KnowledgeBaseViewSerializer(kb).data)

    def destroy(self, request, *args, **kwargs):
        application_uuid = kwargs.get('application_uuid')
        kb_uuid = kwargs.get('uuid')

        application = get_object_or_404(Application, uuid=application_uuid)
        kb = get_object_or_404(KnowledgeBase, uuid=kb_uuid, application=application)

        self._delete_crawled_knowledge_bases(application, kb_uuid)
        self._delete_knowledge_base_data(kb, application)
        self._delete_content_hash(kb, application)
        self._cleanup_application_if_last_kb(application, kb_uuid)
        self._delete_file_if_applicable(kb)
        kb.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _delete_crawled_knowledge_bases(self, application: Application, kb_uuid: str) -> None:
        crawled_kbs = KnowledgeBase.objects.filter(
            application=application,
            source_type='crawled_url',
            metadata__original_kb_uuid=str(kb_uuid)
        )

        crawled_kbs_count = crawled_kbs.count()
        if crawled_kbs_count > 0:
            logger.info(f"Deleting {crawled_kbs_count} related crawled KB items for original KB {kb_uuid}")

            for crawled_kb in crawled_kbs:
                self._delete_crawled_kb_data(crawled_kb, application)

            crawled_kbs.delete()
            logger.info(f"Deleted {crawled_kbs_count} crawled KB items for original KB {kb_uuid}")

    def _delete_crawled_kb_data(self, crawled_kb: KnowledgeBase, application: Application) -> None:
        try:
            crawled_chunks = IngestedChunk.objects.filter(knowledge_base=crawled_kb)
            crawled_qdrant_ids = [str(chunk.uuid) for chunk in crawled_chunks]

            if crawled_qdrant_ids:
                crawled_chunks.delete()
                delete_vectors_from_qdrant(crawled_qdrant_ids)
                logger.info(f"Deleted {len(crawled_qdrant_ids)} vectors for crawled KB {crawled_kb.uuid}")

            self._delete_crawled_kb_content_hash(crawled_kb, application)

        except Exception as e:
            logger.error(f"Failed to clean up crawled KB {crawled_kb.uuid}: {e}")

    def _delete_crawled_kb_content_hash(self, crawled_kb: KnowledgeBase, application: Application) -> None:
        try:
            from core.services.duplicate_detector import DuplicateDetector
            detector = DuplicateDetector()

            crawled_content = crawled_kb.metadata.get('content', '') if crawled_kb.metadata else ''
            if crawled_content and crawled_content.strip():
                detector.remove_content_hash(crawled_content, application)
                logger.info(f"Deleted content hash for crawled KB {crawled_kb.uuid}")
        except Exception as e:
            logger.error(f"Failed to delete content hash for crawled KB {crawled_kb.uuid}: {e}")

    def _delete_knowledge_base_data(self, kb: KnowledgeBase, application: Application) -> None:
        chunks = IngestedChunk.objects.filter(knowledge_base=kb)
        qdrant_ids = [str(chunk.uuid) for chunk in chunks]
        chunks.delete()
        delete_vectors_from_qdrant(qdrant_ids)

    def _delete_content_hash(self, kb: KnowledgeBase, application: Application) -> None:
        try:
            from core.services.duplicate_detector import DuplicateDetector
            detector = DuplicateDetector()

            content = self._extract_content_for_hash_deletion(kb)
            content_length = len(content) if content else 0

            logger.info(f"[KB Delete] Processing content hash deletion for KB {kb.uuid} (source_type: {kb.source_type}, content_length: {content_length})")

            if content and content.strip():
                self._remove_content_hash_with_logging(content, application, kb)
            else:
                logger.debug(f"[KB Delete] No content found for KB {kb.uuid} (source_type: {kb.source_type}, content_length: {content_length}) to delete content hash")

        except Exception as e:
            logger.error(f"[KB Delete] Failed to delete content hash for KB {kb.uuid}: {e}")
            import traceback
            logger.error(f"[KB Delete] Traceback: {traceback.format_exc()}")

    def _extract_content_for_hash_deletion(self, kb: KnowledgeBase) -> str:
        if not kb.metadata:
            return ''

        return kb.metadata.get('content', '')

    def _remove_content_hash_with_logging(self, content: str, application: Application, kb: KnowledgeBase) -> None:
        content_hash = ContentHash.generate_content_hash(content)
        logger.info(f"[KB Delete] Generated content hash: {content_hash[:8]}... for KB {kb.uuid}")

        existing_hashes = ContentHash.objects.filter(app=application, content_hash=content_hash)
        hash_count = existing_hashes.count()
        logger.info(f"[KB Delete] Found {hash_count} existing content hashes for KB {kb.uuid}")

        if hash_count > 0:
            for hash_obj in existing_hashes:
                logger.info(f"[KB Delete] Deleting hash: {hash_obj.content_hash[:8]}... (id: {hash_obj.id}, content_type: {hash_obj.content_type})")

        from core.services.duplicate_detector import DuplicateDetector
        detector = DuplicateDetector()
        success = detector.remove_content_hash(content, application)

        if success:
            logger.info(f"[KB Delete] Successfully deleted ContentHash for KB {kb.uuid} (source_type: {kb.source_type})")
        else:
            logger.warning(f"[KB Delete] ContentHash not found for KB {kb.uuid} (source_type: {kb.source_type})")

    def _cleanup_application_if_last_kb(self, application: Application, kb_uuid: str) -> None:
        other_kbs_count = KnowledgeBase.objects.filter(application=application).exclude(uuid=kb_uuid).exclude(source_type='crawled_url').count()

        if other_kbs_count == 0:
            remaining_hashes = ContentHash.objects.filter(app=application).count()
            if remaining_hashes > 0:
                ContentHash.objects.filter(app=application).delete()
                logger.info(f"Cleaned up all remaining content hashes for application {application.uuid}")
        else:
            logger.info(f"Keeping other content hashes for application {application.uuid} (other KBs exist)")

    def _delete_file_if_applicable(self, kb: KnowledgeBase) -> None:
        if kb.source_type == 'file' and kb.path:
            try:
                default_storage.delete(kb.path)
            except Exception as e:
                logger.warning(f"Failed to delete file for KB {kb.uuid}: {e}")

    @action(detail=False, methods=['post'])
    def validate_url(self, request, application_uuid=None):
        url = request.data.get('url')
        if not url:
            return Response(
                {'error': 'URL is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        simple_validation = request.data.get('simple_validation', False)

        application = get_object_or_404(
            Application,
            uuid=application_uuid,
            owner=request.user
        )

        url_service = URLIngestionService()
        validation_result = url_service.validate_url_before_ingestion(url, simple_validation)

        if validation_result['valid']:
            return Response(validation_result, status=status.HTTP_200_OK)
        else:
            return Response(
                validation_result,
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def extraction_details(self, request, application_uuid=None, uuid=None):
        kb = self.get_object()

        metadata = kb.metadata or {}

        extraction_info = {
            'source_type': kb.source_type,
            'path': kb.path,
            'title': metadata.get('title'),
            'description': metadata.get('description'),
            'content_length': len(metadata.get('content', '')),
            'content_type': metadata.get('content_type'),
            'extraction_status': metadata.get('extraction_status'),
            'extraction_timestamp': metadata.get('extraction_timestamp'),
            'extraction_error': metadata.get('extraction_error')
        }

        if kb.source_type == 'url':
            extraction_info.update({
                'url': kb.path,
                'links_count': len(metadata.get('links', [])),
                'crawling_enabled': metadata.get('crawling_enabled', False),
                'crawling_status': metadata.get('crawling_status'),
                'crawled_pages': metadata.get('crawled_data', {}).get('total_pages', 0)
            })

        return Response(extraction_info, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def enable_crawling(self, request, application_uuid=None, uuid=None):
        kb = self.get_object()

        if kb.source_type != 'url':
            return Response(
                {'error': 'Crawling is only available for URL knowledge base items'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CrawlingEnableSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url_service = URLIngestionService()
        max_depth = serializer.validated_data['max_depth']
        max_pages = serializer.validated_data['max_pages']

        try:
            url_service.enable_crawling_for_kb(kb, max_depth, max_pages)

            process_kb_item(kb)

            return Response({
                'message': 'Crawling enabled successfully',
                'crawling_config': {
                    'max_depth': max_depth,
                    'max_pages': max_pages
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Failed to enable crawling: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def disable_crawling(self, request, application_uuid=None, uuid=None):
        kb = self.get_object()

        if kb.source_type != 'url':
            return Response(
                {'error': 'Crawling is only available for URL knowledge base items'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            url_service = URLIngestionService()
            url_service.disable_crawling_for_kb(kb)

            return Response({
                'message': 'Crawling disabled successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Failed to disable crawling: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def crawling_data(self, request, application_uuid=None, uuid=None):
        kb = self.get_object()

        if kb.source_type != 'url':
            return Response(
                {'error': 'Crawling data is only available for URL knowledge base items'},
                status=status.HTTP_400_BAD_REQUEST
            )

        metadata = kb.metadata or {}
        crawled_data = metadata.get('crawled_data', {})

        if not crawled_data:
            return Response({
                'message': 'No crawling data available',
                'crawling_enabled': metadata.get('crawling_enabled', False),
                'crawling_status': metadata.get('crawling_status', 'not_started')
            }, status=status.HTTP_200_OK)

        serializer = CrawlingDataSerializer(crawled_data)

        return Response({
            'crawling_enabled': metadata.get('crawling_enabled', False),
            'crawling_status': metadata.get('crawling_status'),
            'crawling_timestamp': metadata.get('crawling_timestamp'),
            'crawling_config': metadata.get('crawling_config', {}),
            'crawled_pages': metadata.get('crawled_data', {}).get('total_pages', 0),
            'total_pages': metadata.get('crawl_stats', {}).get('total_pages', 0),
            'crawl_stats': metadata.get('crawl_stats', {}),
            'crawled_data': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def crawling_stats(self, request, application_uuid=None, uuid=None):
        kb = self.get_object()

        if kb.source_type != 'url':
            return Response(
                {'error': 'Crawling stats are only available for URL knowledge base items'},
                status=status.HTTP_400_BAD_REQUEST
            )

        metadata = kb.metadata or {}
        crawled_data = metadata.get('crawled_data', {})
        crawl_stats = crawled_data.get('crawl_stats', {})

        if not crawl_stats:
            return Response({
                'message': 'No crawling statistics available',
                'crawling_enabled': metadata.get('crawling_enabled', False),
                'crawling_status': metadata.get('crawling_status', 'not_started')
            }, status=status.HTTP_200_OK)

        serializer = CrawlingStatsSerializer(crawl_stats)

        return Response({
            'crawling_enabled': metadata.get('crawling_enabled', False),
            'crawling_status': metadata.get('crawling_status'),
            'crawling_timestamp': metadata.get('crawling_timestamp'),
            'crawl_stats': serializer.data
        }, status=status.HTTP_200_OK)
