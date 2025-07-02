from rest_framework import viewsets, permissions

from core.serializers.api_token import APITokenSerializer


class APITokenViewSet(viewsets.ModelViewSet):
    serializer_class = APITokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.api_tokens.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
