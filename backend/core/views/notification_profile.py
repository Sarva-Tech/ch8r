from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from core.models import NotificationProfile
from core.serializers import NotificationProfileSerializer

class NotificationProfileViewSet(viewsets.ModelViewSet):
    queryset = NotificationProfile.objects.all()
    serializer_class = NotificationProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"message": "Notification created successfully"},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {"message": "Notification updated successfully"},
            status=status.HTTP_200_OK
        )
