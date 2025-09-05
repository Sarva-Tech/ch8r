import json
import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Q

from core.consts import LIVE_UPDATES_PREFIX
from core.integrations import get_app_integrations, execute_tool_call
from core.llm_client import LLMClient
from core.llm_client_utils import messages_to_llm_conversation, get_agent_response_schema, add_kb_to_convo, \
    add_instructions_to_convo
from core.models import IngestedChunk, Application, LLMModel
from core.models.message import Message

from core.serializers.message import ViewMessageSerializer
from core.services import get_chunks
from core.services.template_loader import TemplateLoader
from core.utils import parse_llm_response

logger = logging.getLogger(__name__)

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

    messages = Message.objects.filter(chatroom=chatroom).order_by("created_at")

    if has_chunks:
        kb_data = get_chunks(question, app, top_k=5)
    else:
        kb_data = "NO_CONTEXT"

    prompt_context = {
        "product_name": app.name,
        "product_type": 'Software as a Service (SaaS)',
        "tone": "friendly and professional",
    }

    system_instruction = TemplateLoader.render_template('customer_support.j2', prompt_context)

    text_model = app.get_model_by_type(LLMModel.ModelType.TEXT)
    client = LLMClient(
        base_url=text_model.base_url,
        api_key=text_model.config,
    )
    conversation = messages_to_llm_conversation(messages)
    conversation = add_instructions_to_convo(conversation, system_instruction)
    conversation = add_kb_to_convo(conversation, kb_data)

    response_schema = get_agent_response_schema("support_response")

    tools = get_app_integrations(app)
    logger.info("Tools: %s ", tools)
    logger.info("Conversation: %s", conversation)
    tool_call_response = client.chat(
        messages=conversation,
        model=text_model.model_name,
        tools=tools
    )

    logger.info("Tool_call_response: %s", tool_call_response)
    tool_results = {}

    for choice in tool_call_response.choices:
        msg = choice.message
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name

                args = (
                    json.loads(tool_call.function.arguments)
                    if isinstance(tool_call.function.arguments, str)
                    else tool_call.function.arguments
                )

                tool_results[tool_name] = execute_tool_call(app, tool_name, **args)
                logger.info(f"Tool: {tool_name}, Result: {tool_results[tool_name]}")

                conversation.append({
                    "role": "assistant",
                    "type": "function_call_output",
                    "call_id": tool_call.id,
                    "content": json.dumps(tool_results[tool_name]),
                })

    llm_response = client.chat(
        conversation,
        model=text_model.model_name,
        response_schema=response_schema
    )

    try:
        llm_response_data = parse_llm_response(llm_response.choices[0].message.content)

        logger.info("Final LLM Response:\n%s", json.dumps(llm_response_data, indent=2))


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
