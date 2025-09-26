from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.integrations.registry import SUPPORTED_INTEGRATIONS, INTEGRATION_TOOLS, \
    SUPPORTED_PROVIDERS
from core.models import Integration
from core.serializers import IntegrationCreateSerializer, IntegrationViewSerializer

class IntegrationViewSet(viewsets.ModelViewSet):
    queryset = Integration.objects.none()
    permission_classes = [IsAuthenticated]
    lookup_field = 'uuid'
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return Integration.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return IntegrationCreateSerializer
        return IntegrationViewSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "PUT method not allowed. Use PATCH instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Deleted"},
            status=status.HTTP_200_OK
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supported_integrations(request):
    data = {
        "supported_integrations": SUPPORTED_INTEGRATIONS,
        "supported_providers": SUPPORTED_PROVIDERS,
        "integration_tools": INTEGRATION_TOOLS,
    }
    return Response(data)


