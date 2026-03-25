import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Q

from core.consts import LIVE_UPDATES_PREFIX
from core.llm_client_utils import messages_to_llm_conversation, add_kb_to_convo, \
    add_instructions_to_convo
from core.models import IngestedChunk, Application, AIProvider, Message

from core.serializers.message import ViewMessageSerializer
from core.services.ingestion import get_chunks
from core.services.template_loader import TemplateLoader
from core.services.ai_client_service import AIClientService

logger = logging.getLogger(__name__)

AGENT_IDENTIFIER = getattr(settings, "DEFAULT_AGENT_IDENTIFIER", "agent_llm_001")

def _send_live_update(bot_message: Message, user_message: Message):
    channel_layer = get_channel_layer()
    
    if user_message.platform == 'widget':
        participants = list(
            user_message.chatroom.participants.filter(
                Q(user_identifier__startswith='widget_') |
                Q(user_identifier__startswith='dashboard_') |
                Q(role='human_agent')
            ).exclude(
                Q(role='agent')
            ).values_list('user_identifier', flat=True)
        )
    else:
        participants = list(
            user_message.chatroom.participants.filter(
                Q(user_identifier__startswith='dashboard_') | Q(role='human_agent')
            ).exclude(
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
            logger.info(f"Live update sent to {group_name}")
        except Exception as e:
            logger.error(f"Failed to send message to {group_name}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
    
    if not participants:
        logger.warning("No participants found for live update! ")

@shared_task
def generate_bot_response(message_id, app_uuid, ai_provider_id=None, model=None):
    app = Application.objects.get(uuid=app_uuid)
    user_message = Message.objects.get(id=message_id)
    chatroom = user_message.chatroom
    question = user_message.message

    ai_client_service = AIClientService()
    provider, model = ai_client_service.get_client_and_model(
        app=app,
        ai_provider_id=ai_provider_id,
        model=model,
        context='response',
        capability='text'
    )

    if not provider or not model:
        error_message = "No AI provider configured or available"
        answer = error_message
        metadata = {
            "status": "ERROR",
            "escalation": True,
            "reason_for_escalation": error_message,
            "error_details": error_message,
        }
        
        bot_message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=AGENT_IDENTIFIER,
            message=answer,
            metadata=metadata,
            ai_provider_id=ai_provider_id,
            model=model,
            platform=user_message.platform,
            ai_mode=True,
            is_internal=user_message.is_internal,
        )
        
        _send_live_update(bot_message, user_message)
        return

    has_chunks = IngestedChunk.objects.filter(
        knowledge_base__application__uuid=app_uuid
    ).exists()

    messages = Message.objects.filter(chatroom=chatroom).order_by("created_at")

    if has_chunks:
        kb_data = get_chunks(question, app, top_k=5)
    else:
        kb_data = "NO_CONTEXT"

    prompt_context = {
        "product_name": app.name,
        "tone": "professional",
    }

    system_instruction = TemplateLoader.render_template('prompts/default.j2', prompt_context)
    print(system_instruction)
    conversation = messages_to_llm_conversation(messages)
    conversation = add_instructions_to_convo(conversation, system_instruction)
    conversation = add_kb_to_convo(conversation, kb_data)

    prompt = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in conversation])

    try:
        agent_response = provider.generate_text(model, prompt)
        answer = agent_response.answer
        metadata = {
            "status": agent_response.status,
            "escalation": agent_response.escalation,
            "reason_for_escalation": agent_response.reason_for_escalation,
        }
    except Exception as e:
        logger.error(f"Failed to generate content: {e}")
        error_message = str(e)
        
        answer = error_message
        metadata = {
            "status": "ERROR",
            "escalation": True,
            "reason_for_escalation": error_message,
            "error_details": error_message,
        }

    bot_message = Message.objects.create(
        chatroom=chatroom,
        sender_identifier=AGENT_IDENTIFIER,
        message=answer,
        metadata=metadata,
        ai_provider_id=ai_provider_id,
        model=model,
        platform=user_message.platform,
        ai_mode=True,
        is_internal=user_message.is_internal,
    )

    _send_live_update(bot_message, user_message)
