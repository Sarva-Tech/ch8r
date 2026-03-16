from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import NotificationProfile
from core.serializers.notification_profiles import NotificationProfileSerializer
from core.consts import SUPPORTED_NOTIFICATION_PROVIDERS


class NotificationProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationProfileSerializer
    lookup_field = 'uuid'
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return NotificationProfile.objects.filter(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['supported_providers'] = SUPPORTED_NOTIFICATION_PROVIDERS
        return response

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response({'detail': 'deleted'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle_enabled(self, request, uuid=None):
        profile = self.get_object()
        profile.is_enabled = not profile.is_enabled
        profile.save(update_fields=['is_enabled'])
        return Response(NotificationProfileSerializer(profile).data)
