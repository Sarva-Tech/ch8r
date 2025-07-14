from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from core.models import KnowledgeBase, Application
from core.serializers import KnowledgeBaseCreateSerializer, KnowledgeBaseViewSerializer, ApplicationViewSerializer
from django.core.files.storage import default_storage


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.none()
    permission_classes = [permissions.IsAuthenticated | HasAPIKey]
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action == 'create':
            return KnowledgeBaseCreateSerializer
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

        serializer = KnowledgeBaseCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            data = serializer.validated_data
            path = ""
            metadata = {}

            if data['source_type'] in ['youtube', 'url']:
                path = data['url']
            elif data['source_type'] == 'text':
                path = f"text://{data['text'][:50]}"
                metadata = {'content': data['text']}
            elif data['source_type'] == 'file':
                uploaded_file = data['file']
                filename = default_storage.save(f"uploads/{uploaded_file.name}", uploaded_file)
                path = default_storage.url(filename)

            kb = KnowledgeBase.objects.create(application=application, path=path, metadata=metadata, source_type=data['source_type'])
            return Response(KnowledgeBaseViewSerializer(kb).data, status=status.HTTP_201_CREATED)

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

    def get_queryset(self):
        application_uuid = self.kwargs.get('application_uuid')
        return KnowledgeBase.objects.filter(application__uuid=application_uuid, application__owner=self.request.user)
