from rest_framework import viewsets
from core.models import NotificationProfile
from core.serializers import NotificationProfileSerializer
from rest_framework.permissions import IsAuthenticated

class NotificationProfileViewSet(viewsets.ModelViewSet):
    queryset = NotificationProfile.objects.all()
    serializer_class = NotificationProfileSerializer
    permission_classes = [IsAuthenticated]
