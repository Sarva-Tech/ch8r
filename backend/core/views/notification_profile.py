from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from core.models import NotificationProfile
from core.serializers import BulkNotificationProfileSerializer


class NotificationProfileViewSet(viewsets.ModelViewSet):
    queryset = NotificationProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'bulk_upload':
            return BulkNotificationProfileSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request, *args, **kwargs):
        # Ensure we're working with a list
        if not isinstance(request.data, list):
            return Response(
                {"error": "Payload must be an array of notification profiles"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BulkNotificationProfileSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                # Let the serializer handle creation
                instances = serializer.save()

            return Response({
                "status": "success",
                "message": f"Created {len(instances)} notifications",
                "count": len(instances)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "Bulk creation failed",
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)