from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from core.models import NotificationProfile
from core.serializers import BulkNotificationProfileSerializer, NotificationProfileSerializer


class NotificationProfileViewSet(viewsets.ModelViewSet):
    queryset = NotificationProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'bulk_upload':
            return BulkNotificationProfileSerializer
        return NotificationProfileSerializer

    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request, *args, **kwargs):
        if not isinstance(request.data, list):
            return Response(
                {"error": "Payload must be an array of notification profiles"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                instances = serializer.save()

            response_data = []
            for instance in instances:
                config = instance.config or {}

                if 'webhookUrl' in config:
                    config = {}

                profile_data = {
                    "id": instance.id,
                    "uuid": str(instance.uuid),
                    "type": instance.type,
                    "config": config,
                    "created_at": instance.created_at.isoformat(),
                    "name": instance.name
                }
                response_data.append(profile_data)

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Bulk creation failed",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
