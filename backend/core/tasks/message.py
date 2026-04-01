import json
import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Q

from core.consts import LIVE_UPDATES_PREFIX
from core.integrations.integration_dispatcher import get_enabled_tools_for_app
from core.llm_client_utils import messages_to_llm_conversation, add_kb_to_convo, \
    add_instructions_to_convo
from core.models import IngestedChunk, Application, Message

from core.serializers.message import ViewMessageSerializer
from core.services.ingestion import get_chunks
from core.services.template_loader import TemplateLoader
from core.services.ai_client_service import AIClientService
from core.services.tool_call_executor import ToolCallExecutor
from core.services.escalation_service import EscalationService

logger = logging.getLogger(__name__)

AGENT_IDENTIFIER = getattr(settings, "DEFAULT_AGENT_IDENTIFIER", "agent_llm_001")
MAX_TOOL_ROUNDS = 5


def _send_live_update(bot_message: Message, user_message: Message):
    channel_layer = get_channel_layer()

    if user_message.platform == 'widget':
        participants = list(
            user_message.chatroom.participants.filter(
                Q(user_identifier__startswith='widget_') |
                Q(user_identifier__startswith='dashboard_') |
                Q(role='human_agent')
            ).exclude(Q(role='agent')).values_list('user_identifier', flat=True)
        )
    else:
        participants = list(
            user_message.chatroom.participants.filter(
                Q(user_identifier__startswith='dashboard_') | Q(role='human_agent')
            ).exclude(Q(role='agent')).values_list('user_identifier', flat=True)
        )

    for participant_id in participants:
        group_name = f"{LIVE_UPDATES_PREFIX}_{participant_id}"
        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {"type": "send.message", "message": ViewMessageSerializer(bot_message).data}
            )
            logger.info(f"Live update sent to {group_name}")
        except Exception as e:
            logger.error(f"Failed to send message to {group_name}: {e}")

    if not participants:
        logger.warning("No participants found for live update!")


@shared_task
def generate_bot_response(message_id, app_uuid, ai_provider_id=None, model=None):
    logger.info(
        "[generate_bot_response] Task started | message_id=%s app_uuid=%s ai_provider_id=%s model=%s",
        message_id, app_uuid, ai_provider_id, model,
    )

    app = Application.objects.get(uuid=app_uuid)
    user_message = Message.objects.get(id=message_id)
    chatroom = user_message.chatroom
    question = user_message.message

    logger.info(
        "[generate_bot_response] Message received | chatroom_id=%s platform=%s is_internal=%s "
        "question_length=%d question_preview=%.120r",
        chatroom.id, user_message.platform, user_message.is_internal,
        len(question), question,
    )

    ai_client_service = AIClientService()
    provider, model = ai_client_service.get_client_and_model(
        app=app,
        ai_provider_id=ai_provider_id,
        model=model,
        context='response',
        capability='text'
    )

    logger.info(
        "[generate_bot_response] AI provider resolved | provider=%s model=%s",
        type(provider).__name__ if provider else None, model,
    )

    if not provider or not model:
        error_message = "No AI provider configured or available"
        logger.error("[generate_bot_response] %s | app_uuid=%s", error_message, app_uuid)
        bot_message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=AGENT_IDENTIFIER,
            message=error_message,
            metadata={"status": "ERROR", "escalation": True,
                      "reason_for_escalation": error_message, "error_details": error_message},
            ai_provider_id=ai_provider_id,
            model=model,
            platform=user_message.platform,
            ai_mode=True,
            is_internal=user_message.is_internal,
        )
        _send_live_update(bot_message, user_message)
        return

    tools = get_enabled_tools_for_app(str(app.uuid))
    tool_names = [t.get("function", t).get("name") for t in (tools or [])]
    logger.info(
        "[generate_bot_response] Tools resolved | app_uuid=%s tool_count=%d tools=%s",
        app_uuid, len(tools) if tools else 0, tool_names,
    )

    has_chunks = IngestedChunk.objects.filter(
        knowledge_base__application__uuid=app_uuid
    ).exists()
    logger.info("[generate_bot_response] Knowledge base | has_chunks=%s", has_chunks)

    messages = Message.objects.filter(chatroom=chatroom).order_by("created_at")
    kb_data = get_chunks(question, app, top_k=5) if has_chunks else "NO_CONTEXT"
    logger.info(
        "[generate_bot_response] Context prepared | conversation_message_count=%d kb_data_length=%d",
        messages.count(), len(kb_data) if isinstance(kb_data, str) else len(str(kb_data)),
    )

    integration_context_lines = []
    from core.models import AppIntegration
    for ai in AppIntegration.objects.filter(application=app, is_active=True).select_related('integration'):
        repo = (ai.metadata or {}).get("repo", "")
        if repo:
            integration_context_lines.append(
                f"- {ai.integration.provider} ({ai.integration_type}): repo={repo}"
            )
    integration_context = "\n".join(integration_context_lines)

    prompt_context = {"product_name": app.name, "tone": "professional", "integration_context": integration_context}
    system_instruction = TemplateLoader.render_template('prompts/default.j2', prompt_context)

    conversation = messages_to_llm_conversation(messages, platform=user_message.platform)
    conversation = add_instructions_to_convo(conversation, system_instruction)
    conversation = add_kb_to_convo(conversation, kb_data)

    from core.agent_response_schema import SupportAgentResponse

    agent_response = None
    tool_call_records: list[dict] = []
    intermediate_message = None
    escalation_metadata: dict = {}

    try:
        logger.info(
            "[generate_bot_response] Starting two-shot pipeline | max_rounds=%d",
            MAX_TOOL_ROUNDS,
        )

        executor = ToolCallExecutor()

        for round_num in range(MAX_TOOL_ROUNDS):
            logger.info("[generate_bot_response] Pipeline round %d/%d", round_num + 1, MAX_TOOL_ROUNDS)

            # On the first round, pass tools so the model can decide to call them.
            # On subsequent rounds (tool results already in conversation), pass no tools
            # so the model produces a structured final answer instead of more tool calls.
            tools_for_round = tools if round_num == 0 else None

            agent_response, raw_tool_calls = provider.generate_with_conversation(
                model, conversation, tools_for_round, SupportAgentResponse
            )

            if not raw_tool_calls:
                # No tool calls — this is the final response
                logger.info(
                    "[generate_bot_response] No tool calls in round %d — using as final response | "
                    "answer_length=%d status=%s",
                    round_num + 1, len(agent_response.answer), agent_response.status,
                )
                break

            # Tool calls present
            logger.info(
                "[generate_bot_response] Tool calls requested | round=%d count=%d calls=%s",
                round_num + 1, len(raw_tool_calls), [tc.get("name") for tc in raw_tool_calls],
            )

            # Save Intermediate_Message on the first round with tool calls
            if intermediate_message is None:
                intermediate_message = Message.objects.create(
                    chatroom=chatroom,
                    sender_identifier=AGENT_IDENTIFIER,
                    message=str(raw_tool_calls),
                    metadata={
                        "tool_intent": [tc.get("name") for tc in raw_tool_calls],
                        "tool_calls": [],
                    },
                    ai_provider_id=ai_provider_id,
                    model=model,
                    platform=user_message.platform,
                    ai_mode=True,
                    is_internal=True,
                )
                logger.info(
                    "[generate_bot_response] Intermediate_Message saved | id=%s",
                    intermediate_message.id,
                )

            # Execute all tool calls
            round_records, tool_result_messages = executor.execute_all(str(app.uuid), raw_tool_calls)
            tool_call_records.extend(round_records)

            # Append tool results to conversation for next round
            conversation.extend(tool_result_messages)

        else:
            # MAX_TOOL_ROUNDS exhausted
            logger.warning(
                "[generate_bot_response] MAX_TOOL_ROUNDS (%d) exhausted — using last response",
                MAX_TOOL_ROUNDS,
            )

        # Update Intermediate_Message with accumulated tool_call_records
        if intermediate_message is not None:
            intermediate_message.metadata = {
                **intermediate_message.metadata,
                "tool_calls": tool_call_records,
            }
            intermediate_message.save(update_fields=["metadata"])

    except Exception as e:
        logger.error(
            "[generate_bot_response] Failed to generate content | error=%s",
            e, exc_info=True,
        )
        bot_message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=AGENT_IDENTIFIER,
            message=str(e),
            metadata={
                "status": "ERROR",
                "escalation": True,
                "reason_for_escalation": str(e),
                "error_details": str(e),
            },
            ai_provider_id=ai_provider_id,
            model=model,
            platform=user_message.platform,
            ai_mode=True,
            is_internal=user_message.is_internal,
        )
        _send_live_update(bot_message, user_message)
        return

    # --- Escalation check — only for non-internal conversations ---
    escalation_service = EscalationService()
    if not user_message.is_internal and escalation_service.should_escalate(chatroom, agent_response, escalation_threshold=70):
        logger.info(
            "[generate_bot_response] Escalation triggered | score=%s status=%s",
            agent_response.escalation_score, agent_response.status,
        )
        escalation_metadata = escalation_service.escalate(chatroom, app, agent_response)
    else:
        escalation_metadata = {}

    # --- Build Final_Message metadata ---
    # tool_calls go on Intermediate_Message when it exists, otherwise on Final_Message
    final_tool_calls = [] if intermediate_message is not None else tool_call_records

    metadata = {
        "status": str(agent_response.status),
        "escalation": agent_response.escalation,
        "reason_for_escalation": agent_response.reason_for_escalation,
        "sentiment_score": agent_response.sentiment_score,
        "escalation_score": agent_response.escalation_score,
        "criticality_score": agent_response.criticality_score,
        "tool_calls": final_tool_calls,
        "escalation_reason": escalation_metadata.get("escalation_reason", ""),
        "notified_profiles": escalation_metadata.get("notified_profiles", []),
    }

    bot_message = Message.objects.create(
        chatroom=chatroom,
        sender_identifier=AGENT_IDENTIFIER,
        message=agent_response.answer,
        metadata=metadata,
        ai_provider_id=ai_provider_id,
        model=model,
        platform=user_message.platform,
        ai_mode=True,
        is_internal=user_message.is_internal,
    )
    logger.info(
        "[generate_bot_response] Final_Message saved | bot_message_id=%s status=%s escalation=%s",
        bot_message.id, metadata.get("status"), metadata.get("escalation"),
    )

    _send_live_update(bot_message, user_message)
    logger.info(
        "[generate_bot_response] Task complete | message_id=%s bot_message_id=%s",
        message_id, bot_message.id,
    )
