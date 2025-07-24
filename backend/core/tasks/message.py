import os
import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Q

from core.consts import LIVE_UPDATES_PREFIX
from core.models import IngestedChunk
from core.models.message import Message
from langchain.chat_models import init_chat_model
from core.serializers.message import ViewMessageSerializer
from core.services import get_chunks

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
AGENT_IDENTIFIER = getattr(settings, "DEFAULT_AGENT_IDENTIFIER", "agent_llm_001")

@shared_task
def generate_bot_response(message_id, app_uuid):
    user_message = Message.objects.get(id=message_id)
    chatroom = user_message.chatroom
    question = user_message.message

    has_chunks = IngestedChunk.objects.filter(
        knowledge_base__application__uuid=app_uuid
    ).exists()

    if has_chunks:
        context = get_chunks(question, app_uuid, top_k=5)
        prompt = f"Based on the context:\n{context}\n\nAnswer the user query:\n{question}"
    else:
        print("No ingested chunks found for this application.")
        prompt = f"Answer the user query:\n{question}"

    model = init_chat_model("gemini-2.0-flash", model_provider="google_genai", api_key=GEMINI_API_KEY)
    llm_response = model.invoke(prompt)

    bot_message = Message.objects.create(
        chatroom=chatroom,
        sender_identifier=AGENT_IDENTIFIER,
        message=llm_response.content,
    )

    channel_layer = get_channel_layer()
    participants = list(
        user_message.chatroom.participants.exclude(
            Q(role='agent')
        ).values_list('user_identifier', flat=True)
    )

    for participant_id in participants:
        group_name = f"{LIVE_UPDATES_PREFIX}_{participant_id}"
        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send.message",
                    "message": ViewMessageSerializer(bot_message).data,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to send message to {group_name}: {str(e)}")
