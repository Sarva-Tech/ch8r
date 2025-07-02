from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError

from core.models import ApplicationPermission, APIToken
from core.serializers import ApplicationPermissionSerializer

class ApplicationPermissionViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ApplicationPermission.objects.filter(api_token__user=self.request.user)

    def perform_create(self, serializer):
        token_id = self.request.data.get('api_token_id')
        try:
            token = APIToken.objects.get(id=token_id, user=self.request.user)
        except APIToken.DoesNotExist:
            raise ValidationError("Invalid token ID or you don't own this token.")
        serializer.save(api_token=token)
