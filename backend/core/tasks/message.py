import os

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from core.models.message import Message
from langchain.chat_models import init_chat_model
from core.views.ingestion import get_context_chunks
from core.serializers.message import ViewMessageSerializer

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
AGENT_IDENTIFIER = getattr(settings, "DEFAULT_AGENT_IDENTIFIER", "agent_llm_001")

@shared_task
def generate_bot_response(message_id, app_uuid):
    print('generating response', message_id, app_uuid)
    user_message = Message.objects.get(id=message_id)
    chatroom = user_message.chatroom

    context = get_context_chunks(user_message.message, app_uuid, top_k=5)
    prompt = f"Based on the context:\n{context} provide answer to the user query..."

    model = init_chat_model("gemini-2.0-flash", model_provider="google_genai", api_key=GEMINI_API_KEY)
    llm_response = model.invoke(prompt)

    bot_message = Message.objects.create(
        chatroom=chatroom,
        sender_identifier=AGENT_IDENTIFIER,
        message=llm_response.content,
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chatroom_{chatroom.uuid}",
        {
            "type": "send.message",
            "message": ViewMessageSerializer(bot_message).data,
        }
    )
