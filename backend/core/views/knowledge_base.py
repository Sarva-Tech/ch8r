from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from core.models import KnowledgeBase, Application
from core.serializers import (
    KnowledgeBaseItemListSerializer,
    KnowledgeBaseViewSerializer,
    ApplicationViewSerializer
)
from core.services.kb_utils import create_kb_records
from core.services.kb_utils import parse_kb_from_request
from core.tasks import process_kb


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
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

            return Response({"message": "Knowledge base files added."}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT")

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH")

    def destroy(self, request, *args, **kwargs):
        application_uuid = kwargs.get('application_uuid')
        kb_uuid = kwargs.get('uuid')

        application = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        kb = get_object_or_404(KnowledgeBase, uuid=kb_uuid, application=application)

        kb.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)