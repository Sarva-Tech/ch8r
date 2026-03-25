from rest_framework import viewsets, status, permissions
from rest_framework.response import Response

from core.models import NotificationProfile
from core.serializers import NotificationProfileSerializer


class NotificationProfileViewSet(viewsets.ModelViewSet):
    queryset = NotificationProfile.objects.none()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationProfile.objects.filter(owner=self.request.user)

    def get_serializer_class(self):
        return NotificationProfileSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "PUT method not allowed. Use PATCH instead."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )