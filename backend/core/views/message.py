import os

from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings

from core.models.application import Application
from core.models.chatroom import ChatRoom
from core.models.chatroom_participant import ChatroomParticipant
from core.models.message import Message

from core.serializers.message import CreateMessageSerializer, ViewMessageSerializer

from langchain.chat_models import init_chat_model

from core.views.ingestion import get_context_chunks
from core.widget_auth import WidgetTokenAuthentication

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
AGENT_IDENTIFIER = getattr(settings, "DEFAULT_AGENT_IDENTIFIER", "agent_llm_001")

def generate_chatroom_name(a, b):
    return f"chat:{':'.join(sorted([a, b]))}"

class SendMessageView(APIView):
    authentication_classes = [WidgetTokenAuthentication, SessionAuthentication, TokenAuthentication]

    def post(self, request, application_uuid):
        # Refactor
        if request.user and request.user.is_authenticated:
            app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        else:
            app = getattr(request, 'application', None)
            if not app or str(app.uuid) != str(application_uuid):
                return Response({'detail': 'Invalid or unauthorized widget token'}, status=403)

        serializer = CreateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        chatroom_uuid = data.get('chatroom_identifier')
        sender_id = data.get('sender_identifier')
        message_text = data['message']
        metadata = data.get('metadata', {})

        if not chatroom_uuid and not sender_id:
            return Response(
                {"detail": "sender_identifier is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if chatroom_uuid:
            chatroom = get_object_or_404(ChatRoom, uuid=chatroom_uuid, application=app)

            if sender_id and not ChatroomParticipant.objects.filter(chatroom=chatroom,
                                                                    user_identifier=sender_id).exists():
                ChatroomParticipant.objects.create(
                    chatroom=chatroom,
                    user_identifier=sender_id,
                    role='user'
                )

        else:
            chatroom_name = generate_chatroom_name(sender_id, AGENT_IDENTIFIER)

            with transaction.atomic():
                chatroom = ChatRoom.objects.create(
                    application=app,
                    name=chatroom_name
                )

                ChatroomParticipant.objects.bulk_create([
                    ChatroomParticipant(chatroom=chatroom, user_identifier=sender_id, role='user'),
                    ChatroomParticipant(chatroom=chatroom, user_identifier=AGENT_IDENTIFIER, role='agent'),
                ])

        message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=sender_id,
            message=message_text,
            metadata=metadata
        )

        context = get_context_chunks(message.message, app.uuid, top_k=5)
        prompt = f"Based on the context:\n{context} provide answer to the user query. If you do not have a context simply avoid answering the question.\n\nUser: {message.message}"

        model = init_chat_model("gemini-2.0-flash", model_provider="google_genai", api_key=GEMINI_API_KEY)
        llm_response = model.invoke(prompt)

        bot_message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=AGENT_IDENTIFIER,
            message=llm_response.content,
        )

        response_data = ViewMessageSerializer(bot_message).data
        response_data['message_identifier'] = message.uuid
        response_data['chatroom_identifier'] = chatroom.uuid
        return Response(response_data, status=status.HTTP_201_CREATED)
