from django.db.models import OuterRef, Subquery, DateTimeField
from rest_framework import viewsets, permissions, status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response
from rest_framework.views import APIView

from core.consts import REGISTERED_USER_ID_PREFIX
from core.models import Application, ChatRoom, Message, LLMModel, AppModel
from core.models.chatroom_participant import ChatroomParticipant
from core.permissions import HasAPIKeyPermission
from core.serializers import ApplicationCreateSerializer, ApplicationViewSerializer
from core.serializers.chatroom import ChatRoomPreviewSerializer
from core.services.kb_utils import parse_kb_from_request
from core.services.kb_utils import create_kb_records
from core.tasks import process_kb
from core.widget_auth import WidgetTokenAuthentication, IsAuthenticatedOrWidget


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

        # TODO: may be we need to handle proper log and error messages if default
        # TODO: models are not configured yet.
        AppModel.configure_defaults(app_instance)

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
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]

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

        serializer = ChatRoomPreviewSerializer(chatrooms, many=True, context={'user_identifier': f"{REGISTERED_USER_ID_PREFIX}_{request.user.id}"})
        return Response({'chatrooms': serializer.data})


class UserChatRoomsView(APIView):
    """
    Returns chatrooms for a specific widget user (sender_identifier).
    Supports optional ?type=human|ai filter based on participant roles.
    """
    authentication_classes = [WidgetTokenAuthentication, SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrWidget | HasAPIKeyPermission]

    def get(self, request, application_uuid):
        if request.user and request.user.is_authenticated:
            app = Application.objects.filter(uuid=application_uuid, owner=request.user).first()
        else:
            app = getattr(request, 'application', None)
            if not app or str(app.uuid) != str(application_uuid):
                return Response({'detail': 'Invalid or unauthorized widget token'}, status=403)

        if not app:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        sender_identifier = request.query_params.get('sender_identifier')
        if not sender_identifier:
            return Response({'detail': 'sender_identifier is required.'}, status=status.HTTP_400_BAD_REQUEST)

        chat_type = request.query_params.get('type')  # 'human' or 'ai'

        # Find chatrooms where this sender is a participant
        chatroom_ids = ChatroomParticipant.objects.filter(
            user_identifier=sender_identifier,
            chatroom__application=app,
        ).values_list('chatroom_id', flat=True)

        chatrooms = ChatRoom.objects.filter(id__in=chatroom_ids)

        if chat_type == 'human':
            # Chatrooms that have a human_agent participant
            human_chatroom_ids = ChatroomParticipant.objects.filter(
                chatroom_id__in=chatroom_ids,
                role='human_agent',
            ).values_list('chatroom_id', flat=True)
            chatrooms = chatrooms.filter(id__in=human_chatroom_ids)
        elif chat_type == 'ai':
            # Chatrooms that have an agent (AI) participant but NOT a human_agent
            human_chatroom_ids = ChatroomParticipant.objects.filter(
                chatroom_id__in=chatroom_ids,
                role='human_agent',
            ).values_list('chatroom_id', flat=True)
            chatrooms = chatrooms.exclude(id__in=human_chatroom_ids)

        last_message_time_subquery = Message.objects.filter(
            chatroom=OuterRef('pk')
        ).order_by('-created_at').values('created_at')[:1]

        chatrooms = chatrooms.annotate(
            last_message_time=Subquery(last_message_time_subquery, output_field=DateTimeField())
        ).order_by('-last_message_time', '-created_at').distinct().prefetch_related('messages')

        serializer = ChatRoomPreviewSerializer(chatrooms, many=True, context={'user_identifier': sender_identifier})
        return Response({'chatrooms': serializer.data})
