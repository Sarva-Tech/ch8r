from django.db.models import OuterRef, Subquery, DateTimeField
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Application, ChatRoom, Message
from core.serializers import ApplicationCreateSerializer, ApplicationViewSerializer
from core.serializers.chatroom import ChatRoomPreviewSerializer
from core.services.kb_utils import parse_kb_from_request
from core.services.kb_utils import create_kb_records
from core.tasks import process_kb

class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.none()
    permission_classes = [permissions.IsAuthenticated]
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

        parsed_kb_items = parse_kb_from_request(request)

        if parsed_kb_items:
            created_kbs = create_kb_records(app_instance, parsed_kb_items)

            process_kb.delay([kb.id for kb in created_kbs])

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

        last_message_time_subquery = Message.objects.filter(
            chatroom=OuterRef('pk')
        ).order_by('-created_at').values('created_at')[:1]

        chatrooms = ChatRoom.objects.filter(application=application).annotate(
            last_message_time=Subquery(last_message_time_subquery, output_field=DateTimeField())
        ).order_by('-last_message_time', '-created_at').prefetch_related('messages')

        serializer = ChatRoomPreviewSerializer(chatrooms, many=True)
        return Response({'chatrooms': serializer.data})
