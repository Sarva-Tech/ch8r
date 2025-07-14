from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from core.models import Application, ChatRoom
from core.serializers import ApplicationCreateSerializer, ApplicationViewSerializer
from core.serializers.chatroom import ChatRoomPreviewSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.none()
    permission_classes = [permissions.IsAuthenticated | HasAPIKey]
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        return ApplicationViewSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        app_instance = create_serializer.save(owner=request.user)

        view_serializer = ApplicationViewSerializer(app_instance, context={'request': request})
        return Response(view_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT", detail="Use PATCH to update application.")

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": f"Application '{instance.name}' deleted successfully."},
            status=status.HTTP_200_OK
        )

    def get_queryset(self):
        return Application.objects.filter(owner=self.request.user)


class ApplicationChatRoomsPreviewView(APIView):
    def get(self, request, application_uuid):
        try:
            application = Application.objects.get(uuid=application_uuid)
        except Application.DoesNotExist:
            return Response({"detail": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

        chatrooms = ChatRoom.objects.filter(application=application).prefetch_related('messages')
        serializer = ChatRoomPreviewSerializer(chatrooms, many=True)
        return Response({'chatrooms': serializer.data})
