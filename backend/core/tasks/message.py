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

from core.agent_response_schema import SupportAgentResponse
from core.intent_classification_schema import IntentClassificationResponse

logger = logging.getLogger(__name__)

AGENT_IDENTIFIER = getattr(settings, "DEFAULT_AGENT_IDENTIFIER", "agent_llm_001")


def _send_live_update(bot_message: Message, user_message: Message):
    channel_layer = get_channel_layer()

    participants = list(
        user_message.chatroom.participants.filter(
            Q(user_identifier__startswith='widget_') |
            Q(user_identifier__startswith='dashboard_') |
            Q(role='human_agent')
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


def _send_live_update_to_dashboard(message: Message, user_message: Message):
    channel_layer = get_channel_layer()
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
                {"type": "send.message", "message": ViewMessageSerializer(message).data}
            )
        except Exception as e:
            logger.error(f"Failed to send dashboard update to {group_name}: {e}")


def _build_usage_meta(usage: dict) -> dict:
    return {k: v for k, v in usage.items() if v is not None} if usage else {}


def _format_conversation_history(messages_qs, platform: str) -> list[dict]:
    history = []
    for msg in messages_qs:
        role = "assistant" if msg.sender_identifier == AGENT_IDENTIFIER else "user"
        history.append({
            "role": role,
            "content": msg.message
        })
    return history


@shared_task
def generate_bot_response(message_id, app_uuid, ai_provider_id=None, model=None):
    logger.info(
        "[generate_bot_response] Task started | message_id=%s app_uuid=%s",
        message_id, app_uuid,
    )

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
        capability='text',
    )

    if not provider or not model:
        error_message = "No AI provider configured or available"
        logger.error("[generate_bot_response] %s | app_uuid=%s", error_message, app_uuid)
        bot_message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=AGENT_IDENTIFIER,
            message=error_message,
            metadata={"status": "ERROR", "escalation": True,
                      "reason_for_escalation": error_message},
            ai_provider_id=ai_provider_id,
            model=model,
            platform=user_message.platform,
            ai_mode=True,
            is_internal=user_message.is_internal,
        )
        _send_live_update(bot_message, user_message)
        return

    tools = get_enabled_tools_for_app(str(app.uuid))
    has_chunks = IngestedChunk.objects.filter(
        knowledge_base__application__uuid=app_uuid
    ).exists()

    messages_qs = Message.objects.filter(chatroom=chatroom).order_by("created_at")
    kb_data = get_chunks(question, app, top_k=5) if has_chunks else []
    kb_context = "\n".join(c["content"] for c in kb_data) if kb_data else ""

    from core.models import AppIntegration, ToolConfig
    active_integration_ids = ToolConfig.objects.filter(
        app_integration__application=app,
        app_integration__is_active=True,
        is_enabled=True,
    ).values_list('app_integration_id', flat=True).distinct()

    integration_context_lines = []
    for ai in AppIntegration.objects.filter(id__in=active_integration_ids).select_related('integration'):
        repo = (ai.metadata or {}).get("repo", "")
        if repo:
            integration_context_lines.append(
                f"- {ai.integration.provider} ({ai.integration_type}): repo={repo}"
            )
    integration_context = "\n".join(integration_context_lines)

    config = app.get_prompt_config()
    conversation_history = _format_conversation_history(messages_qs, user_message.platform)

    # === STEP 1: INTENT CLASSIFICATION & TOOL DECISION ===
    logger.info("[generate_bot_response] Step 1: Intent classification")

    intent_prompt_context = {
        "product_name": app.name,
        "tone": config["tone"],
        "role": config["role"],
        "behavior": config["behavior"],
        "conversation_history": conversation_history,
        "kb_context": kb_context,
        "integration_context": integration_context,
        "tools": tools,
    }
    intent_system_instruction = TemplateLoader.render_template('prompts/intent_classification.j2', intent_prompt_context)
    logger.debug("[generate_bot_response] Step 1 prompt: %s", intent_system_instruction)

    intent_conversation = [{"role": "system", "content": intent_system_instruction}]
    intent_conversation.extend(messages_to_llm_conversation(messages_qs, platform=user_message.platform))

    intent_usage = {}
    tool_call_records: list[dict] = []
    intermediate_message = None

    try:
        intent_response, intent_usage_meta = provider.classify_intent(
            model, intent_conversation, tools, IntentClassificationResponse
        )
        intent_usage = _build_usage_meta(intent_usage_meta)

        logger.info(
            "[generate_bot_response] Intent classified | intent=%s kb_sufficient=%s tools=%d",
            intent_response.intent,
            intent_response.kb_sufficient,
            len(intent_response.tools_to_call),
        )

        
        # === STEP 1.5: CREATE REASONING MESSAGE ===
        reasoning_message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=AGENT_IDENTIFIER,
            message=intent_response.reasoning,
            metadata={
                "stage": "intent_reasoning",
                "intent": intent_response.intent.value,
                "kb_sufficient": intent_response.kb_sufficient,
                "sentiment_score": intent_response.sentiment_score,
                "escalation_score": intent_response.escalation_score,
                "criticality_score": intent_response.criticality_score,
                "usage": intent_usage,
            },
            ai_provider_id=ai_provider_id,
            model=model,
            platform=user_message.platform,
            ai_mode=True,
            is_internal=True,
        )
        logger.info(
            "[generate_bot_response] Reasoning message saved | id=%s",
            reasoning_message.id,
        )
        _send_live_update_to_dashboard(reasoning_message, user_message)

    except Exception as e:
        logger.error("[generate_bot_response] Intent classification failed: %s", e, exc_info=True)
        bot_message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=AGENT_IDENTIFIER,
            message=str(e),
            metadata={"status": "ERROR", "escalation": True, "reason_for_escalation": str(e)},
            ai_provider_id=ai_provider_id,
            model=model,
            platform=user_message.platform,
            ai_mode=True,
            is_internal=user_message.is_internal,
        )
        _send_live_update(bot_message, user_message)
        return

    # === STEP 2: EXECUTE TOOLS (if needed) ===
    executor = ToolCallExecutor()

    if intent_response.tools_to_call:
        logger.info(
            "[generate_bot_response] Step 2: Executing %d tools",
            len(intent_response.tools_to_call),
        )

        tool_names_list = [tool.name for tool in intent_response.tools_to_call]
        intermediate_text = f"Executing tool{'s' if len(tool_names_list) > 1 else ''}: {', '.join(tool_names_list)}"

        intermediate_message = Message.objects.create(
            chatroom=chatroom,
            sender_identifier=AGENT_IDENTIFIER,
            message=intermediate_text,
            metadata={
                "stage": "tool_execution",
                "tool_intent": tool_names_list,
                "tool_calls": [],
                "usage": intent_usage,
            },
            ai_provider_id=ai_provider_id,
            model=model,
            platform=user_message.platform,
            ai_mode=True,
            is_internal=True,
        )
        logger.info(
            "[generate_bot_response] Intermediate message saved | id=%s",
            intermediate_message.id,
        )
        _send_live_update_to_dashboard(intermediate_message, user_message)

        raw_tool_calls = []
        for i, tool in enumerate(intent_response.tools_to_call):
            try:
                params = json.loads(tool.parameters_json) if tool.parameters_json else {}
            except json.JSONDecodeError:
                params = {}
            raw_tool_calls.append({
                "name": tool.name,
                "args": params,
                "id": f"{tool.name}_{i}",
            })

        round_records, _ = executor.execute_all(str(app.uuid), raw_tool_calls)
        tool_call_records.extend(round_records)

        intermediate_message.metadata = {
            **intermediate_message.metadata,
            "tool_calls": tool_call_records,
        }
        intermediate_message.save(update_fields=["metadata"])
        _send_live_update_to_dashboard(intermediate_message, user_message)

    else:
        logger.info("[generate_bot_response] Step 2: Skipping tools (KB sufficient or no tools needed)")

    # === STEP 3: FINAL RESPONSE GENERATION ===
    logger.info("[generate_bot_response] Step 3: Generating final response")

    final_prompt_context = {
        "product_name": app.name,
        "tone": config["tone"],
        "response_style": config["response_style"],
        "role": config["role"],
        "behavior": config["behavior"],
        "conversation_history": conversation_history,
        "intent": intent_response.intent.value,
        "reasoning": intent_response.reasoning,
        "kb_context": kb_context,
        "tool_results": tool_call_records,
    }
    final_system_instruction = TemplateLoader.render_template('prompts/final_response.j2', final_prompt_context)
    logger.debug("[generate_bot_response] Step 3 prompt: %s", final_system_instruction)

    final_conversation = [{"role": "system", "content": final_system_instruction}]
    final_conversation.extend(messages_to_llm_conversation(messages_qs, platform=user_message.platform))


    try:
        agent_response, final_usage_meta = provider.generate_final_response(
            model, final_conversation, SupportAgentResponse
        )
        final_usage = _build_usage_meta(final_usage_meta)

    except Exception as e:
        logger.error(
            "[generate_bot_response] Final response generation failed: %s",
            e, exc_info=True,
        )
        agent_response = SupportAgentResponse(
            answer="I apologize, but I encountered an error while generating the response.",
            status="INSUFFICIENT_INFORMATION",
            escalation=False,
            reason_for_escalation="",
            sentiment_score=intent_response.sentiment_score,
            escalation_score=intent_response.escalation_score,
            criticality_score=intent_response.criticality_score,
        )
        final_usage = {}

    # === ESCALATION CHECK ===
    escalation_service = EscalationService()
    escalation_metadata: dict = {}

    if not user_message.is_internal and escalation_service.should_escalate(
        chatroom, agent_response, escalation_threshold=70
    ):
        logger.info(
            "[generate_bot_response] Escalation triggered | score=%s status=%s",
            agent_response.escalation_score, agent_response.status,
        )
        escalation_metadata = escalation_service.escalate(chatroom, app, agent_response, user_message=user_message)

        try:
            user_message.metadata = {
                **(user_message.metadata or {}),
                "escalation": True,
                "reason_for_escalation": escalation_metadata.get("escalation_reason", ""),
                "notified_profiles": escalation_metadata.get("notified_profiles", []),
            }
            user_message.save(update_fields=["metadata"])
            _send_live_update_to_dashboard(user_message, user_message)
        except Exception as esc_err:
            logger.warning("[generate_bot_response] Could not write escalation to user message: %s", esc_err)

        if not escalation_metadata.get("notified_profiles"):
            warning_message = Message.objects.create(
                chatroom=chatroom,
                sender_identifier=AGENT_IDENTIFIER,
                message=(
                    "Escalation triggered but no notification profiles are configured for this application. "
                    "Please configure a notification profile to receive alerts."
                ),
                metadata={"stage": "escalation_warning"},
                ai_provider_id=ai_provider_id,
                model=model,
                platform=user_message.platform,
                ai_mode=True,
                is_internal=True,
            )
            _send_live_update_to_dashboard(warning_message, user_message)

    # === COMBINE USAGE ===
    combined_usage = intent_usage.copy()
    combined_usage.update(final_usage)

    # === CREATE FINAL MESSAGE ===
    final_metadata = {
        "status": str(agent_response.status),
        "escalation": agent_response.escalation,
        "reason_for_escalation": agent_response.reason_for_escalation,
        "intent": intent_response.intent.value,
        "intent_reasoning": intent_response.reasoning,
        "kb_sufficient": intent_response.kb_sufficient,
        "escalation_reason": escalation_metadata.get("escalation_reason", ""),
        "notified_profiles": escalation_metadata.get("notified_profiles", []),
        "usage": combined_usage,
    }

    if kb_data:
        final_metadata["kb_citations"] = kb_data

    bot_message = Message.objects.create(
        chatroom=chatroom,
        sender_identifier=AGENT_IDENTIFIER,
        message=agent_response.answer,
        metadata=final_metadata,
        ai_provider_id=ai_provider_id,
        model=model,
        platform=user_message.platform,
        ai_mode=True,
        is_internal=user_message.is_internal,
    )
    logger.info(
        "[generate_bot_response] Done | bot_message_id=%s status=%s intent=%s",
        bot_message.id, final_metadata.get("status"), intent_response.intent.value,
    )

    _send_live_update(bot_message, user_message)
