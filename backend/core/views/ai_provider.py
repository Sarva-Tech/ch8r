from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from core.serializers.ai_provider import AIProviderCreateSerializer, AIProviderSerializer, AIProviderUpdateSerializer
from core.models import AIProvider

class AIProviderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'put','patch', 'delete']

    queryset = AIProvider.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return AIProviderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AIProviderUpdateSerializer
        return AIProviderSerializer

    def get_queryset(self):
        user = self.request.user
        return AIProvider.objects.filter(creator=user)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        read_serializer = AIProviderSerializer(serializer.instance, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        read_serializer = AIProviderSerializer(instance, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)
