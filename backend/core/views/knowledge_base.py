from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from core.models import KnowledgeBase, Application, IngestedChunk
from core.serializers import KnowledgeBaseItemListSerializer, KnowledgeBaseViewSerializer, ApplicationViewSerializer
from django.core.files.storage import default_storage
from core.permissions import HasAPIKeyPermission
from core.services.ingestion import delete_vectors_from_qdrant

from core.tasks import process_kb
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.none()
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action == 'create':
            return KnowledgeBaseItemListSerializer
        return KnowledgeBaseViewSerializer

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

        parsed_items = []
        i = 0

        while True:
            type_key = f"items[{i}].type"
            value_key = f"items[{i}].value"
            file_key = f"items[{i}].file"

            if type_key not in request.data:
                break

            item = {
                "type": request.data.get(type_key),
                "value": request.data.get(value_key),
                "file": request.FILES.get(file_key),
            }
            parsed_items.append(item)
            i += 1


        serializer = self.get_serializer(data={"items": parsed_items}, context={"request": request})
        if serializer.is_valid():
            items = serializer.validated_data['items']

            records = []
            for item in items:
                item_type = item['type']
                if item_type == 'file':
                    uploaded_file = item['file']
                    filename = default_storage.save(uploaded_file.name, uploaded_file)

                    records.append(KnowledgeBase(
                        application=application,
                        source_type="file",
                        path=filename,
                        status="pending",
                        metadata={
                            'filename': filename,
                            'content': ""
                        }
                    ))
                elif item_type == 'text':
                    text_value = item['value']
                    path = f"text://{text_value[:50]}"

                    records.append(KnowledgeBase(
                        application=application,
                        source_type="text",
                        path=path,
                        status="pending",
                        metadata={
                            'filename': path,
                            'content': text_value
                        }
                    ))

                elif item_type == 'url':
                    url_value = item['value']
                    path = f"{url_value}"

                    records.append(KnowledgeBase(
                        application=application,
                        source_type="url",
                        path=path,
                        status="pending",
                        metadata={
                            'filename': path,
                            'content': ''
                        }
                    ))

            KnowledgeBase.objects.bulk_create(records)

            created_kbs = KnowledgeBase.objects.filter(
                application=application
            ).order_by('-id')[:len(records)][::-1]
            kb_ids = [kb.id for kb in created_kbs]
            process_kb.delay(kb_ids)

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

        kb.metadata = kb.metadata or {}
        kb.metadata["content"] = content
        kb.metadata["is_modified_by_user"] = True
        kb.save(update_fields=["metadata"])

        process_kb.delay([kb.id])

        return Response({"detail": "Content updated successfully."})

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
                kb.path.delete(save=False)
            except Exception as e:
                logger.warning(f"Failed to delete file for KB {kb.uuid}: {e}")

        kb.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        application_uuid = self.kwargs.get('application_uuid')
        return KnowledgeBase.objects.filter(application__uuid=application_uuid, application__owner=self.request.user)
