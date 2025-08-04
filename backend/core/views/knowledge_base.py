from django.core.files.storage import default_storage
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from core.models import KnowledgeBase, Application, IngestedChunk
from core.serializers import KnowledgeBaseItemListSerializer, KnowledgeBaseViewSerializer, ApplicationViewSerializer
from core.permissions import HasAPIKeyPermission
from core.services.ingestion import delete_vectors_from_qdrant
from core.services.kb_utils import create_kb_records, parse_kb_from_request, format_text_uri

from core.tasks import process_kb
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.none()
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action == 'create':
            return KnowledgeBaseItemListSerializer
        return KnowledgeBaseViewSerializer

    def get_queryset(self):
        application_uuid = self.kwargs.get('application_uuid')
        return KnowledgeBase.objects.filter(
            application__uuid=application_uuid,
            application__owner=self.request.user
        )

    def list(self, request, *args, **kwargs):
        application_uuid = kwargs.get('application_uuid')
        application = get_object_or_404(
            Application.objects.select_related('owner').prefetch_related('knowledge_bases'),
            uuid=application_uuid, owner=request.user
        )

        app_data = ApplicationViewSerializer(application).data
        kb_data = KnowledgeBaseViewSerializer(application.knowledge_bases.all(), many=True).data
        app_data['knowledge_base'] = kb_data

        return Response({'application': app_data})

    def create(self, request, *args, **kwargs):
        application_uuid = kwargs.get('application_uuid')
        application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)

        parsed_items = parse_kb_from_request(request)

        serializer = self.get_serializer(data={"items": parsed_items}, context={"request": request})
        if serializer.is_valid():
            items = serializer.validated_data['items']

            created_kbs = create_kb_records(application, items)

            process_kb.delay([kb.id for kb in created_kbs])
            serialized_kbs = KnowledgeBaseViewSerializer(created_kbs, many=True)
            return Response({"kbs": serialized_kbs.data}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

        process_kb.delay([kb.id])

        return Response(KnowledgeBaseViewSerializer(kb).data)

    def destroy(self, request, *args, **kwargs):
        application_uuid = kwargs.get('application_uuid')
        kb_uuid = kwargs.get('uuid')

        application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        kb = get_object_or_404(KnowledgeBase, uuid=kb_uuid, application=application)

        chunks = IngestedChunk.objects.filter(knowledge_base=kb)
        qdrant_ids = [str(chunk.uuid) for chunk in chunks]
        chunks.delete()

        delete_vectors_from_qdrant(qdrant_ids)

        if kb.source_type == 'file' and kb.path:
            try:
                default_storage.delete(kb.path)
            except Exception as e:
                logger.warning(f"Failed to delete file for KB {kb.uuid}: {e}")

        kb.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)