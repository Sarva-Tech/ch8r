from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response

from core.models import LLMModel
from core.permissions import DefaultLLMModelPermission
from core.serializers import LLMModelCreateSerializer, LLMModelViewSerializer


class LLMModelViewSet(viewsets.ModelViewSet):
    queryset = LLMModel.objects.none()
    permission_classes = [permissions.IsAuthenticated, DefaultLLMModelPermission]
    lookup_field = 'uuid'
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return LLMModelCreateSerializer
        return LLMModelViewSerializer

    def get_queryset(self):
        return (
            LLMModel.objects.filter(owner=self.request.user) |
            LLMModel.objects.filter(is_default=True)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        instance = create_serializer.save(owner=request.user)

        view_serializer = LLMModelViewSerializer(instance, context={'request': request})
        return Response(view_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Deleted"},
            status=status.HTTP_200_OK
        )