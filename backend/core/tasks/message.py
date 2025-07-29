import json
import os
import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Q

from core.consts import LIVE_UPDATES_PREFIX
from core.models import IngestedChunk, Application
from core.models.message import Message
from langchain.chat_models import init_chat_model

from core.serializers.message import ViewMessageSerializer
from core.services import get_chunks
from core.services.template_loader import TemplateLoader
from core.utils import parse_llm_response

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
AGENT_IDENTIFIER = getattr(settings, "DEFAULT_AGENT_IDENTIFIER", "agent_llm_001")

@shared_task
def generate_bot_response(message_id, app_uuid):
    app = Application.objects.get(uuid=app_uuid)
    user_message = Message.objects.get(id=message_id)
    chatroom = user_message.chatroom
    question = user_message.message

    has_chunks = IngestedChunk.objects.filter(
        knowledge_base__application__uuid=app_uuid
    ).exists()

    messages = chatroom.messages.order_by("created_at")
    chat_history_entries = []
    for msg in messages:
        if msg.sender_identifier.startswith("agent_llm"):
            sender = "AI Agent"
        elif msg.sender_identifier.startswith("reg_"):
            sender = "Human Agent"
        elif msg.sender_identifier.startswith("anon_"):
            sender = "User"
        else:
            sender = "Unknown"

        chat_history_entries.append(f"{sender}: {msg.message}")

    chat_history = "\n".join(chat_history_entries)

    if has_chunks:
        context = get_chunks(question, app_uuid, top_k=5)
    else:
        context = "NO_CONTEXT"

    prompt_context = {
        "product_name": app.name,
        "product_type": 'Software as a Service (SaaS)',
        "tone": "friendly and professional",
        "context": context,
        "chat_history": chat_history,
        "user_query": question,
    }

    prompt = TemplateLoader.render_template('customer_support.j2', prompt_context)
    print(':::DEBUG Prompt:::', prompt)
    model = init_chat_model("gemini-2.5-pro", model_provider="google_genai", api_key=GEMINI_API_KEY)
    llm_response = model.invoke(prompt)

    try:
        llm_response_data = parse_llm_response(llm_response.content)

        answer = llm_response_data.get("answer", "").strip()
        status = llm_response_data.get("status", "ERROR").strip()
        escalation = llm_response_data.get("escalation", False)
        reason = llm_response_data.get("reason_for_escalation", "").strip()

        metadata = {
            "status": status,
            "escalation": escalation,
            "reason_for_escalation": reason,
        }

    except json.JSONDecodeError:
        answer = llm_response.content.strip()
        metadata = {
            "status": "ERROR",
            "escalation": True,
            "reason_for_escalation": "Malformed LLM response",
        }

    bot_message = Message.objects.create(
        chatroom=chatroom,
        sender_identifier=AGENT_IDENTIFIER,
        message=answer,
        metadata=metadata,
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
