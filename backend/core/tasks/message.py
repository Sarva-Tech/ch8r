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
    prompt_context = {
        "product_name": app.name,
        "tone": config["tone"],
        "response_style": config["response_style"],
        "custom_instructions": config["custom_instructions"],
        "role": config["role"],
        "behavior": config["behavior"],
        "integration_context": integration_context,
    }
    system_instruction = TemplateLoader.render_template('prompts/default.j2', prompt_context)

    conversation = messages_to_llm_conversation(messages_qs, platform=user_message.platform)
    conversation = add_instructions_to_convo(conversation, system_instruction)
    conversation = add_kb_to_convo(conversation, kb_context)

    logger.info(
        "[generate_bot_response] Context ready | messages=%d kb=%s tools=%d",
        messages_qs.count(), has_chunks, len(tools or []),
    )

    from core.agent_response_schema import SupportAgentResponse, ResponseStatus

    agent_response = None
    tool_call_records: list[dict] = []
    intermediate_message = None
    escalation_metadata: dict = {}
    final_usage: dict = {}

    try:
        executor = ToolCallExecutor()

        for round_num in range(MAX_TOOL_ROUNDS):
            logger.info("[generate_bot_response] Pipeline round %d/%d", round_num + 1, MAX_TOOL_ROUNDS)

            tools_for_round = tools if round_num == 0 else None

            response_or_text, raw_tool_calls, usage = provider.generate_with_conversation(
                model, conversation, tools_for_round, SupportAgentResponse
            )
            final_usage = _build_usage_meta(usage)

            if not raw_tool_calls:
                agent_response = response_or_text
                logger.info(
                    "[generate_bot_response] Final answer | round=%d status=%s",
                    round_num + 1, agent_response.status,
                )
                try:
                    user_message.metadata = {
                        **(user_message.metadata or {}),
                        "status": str(agent_response.status),
                        "sentiment_score": agent_response.sentiment_score,
                        "escalation_score": agent_response.escalation_score,
                        "criticality_score": agent_response.criticality_score,
                    }
                    user_message.save(update_fields=["metadata"])
                    _send_live_update_to_dashboard(user_message, user_message)
                except Exception as score_err:
                    logger.warning("[generate_bot_response] Could not write scores to user message: %s", score_err)
                break

            logger.info(
                "[generate_bot_response] Tool calls | round=%d calls=%s",
                round_num + 1, [tc.get("name") for tc in raw_tool_calls],
            )

            if intermediate_message is None:
                tool_names_list = [tc.get("name", "") for tc in raw_tool_calls]
                intermediate_text = (
                    response_or_text
                    if isinstance(response_or_text, str) and response_or_text.strip()
                    else "Calling tool{}: {}".format(
                        "s" if len(tool_names_list) > 1 else "",
                        ", ".join(tool_names_list),
                    )
                )
                intermediate_message = Message.objects.create(
                    chatroom=chatroom,
                    sender_identifier=AGENT_IDENTIFIER,
                    message=intermediate_text,
                    metadata={
                        "stage": "tool_planning",
                        "tool_intent": tool_names_list,
                        "tool_calls": [],
                        "usage": _build_usage_meta(usage),
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
                _send_live_update_to_dashboard(intermediate_message, user_message)

            round_records, tool_result_messages = executor.execute_all(str(app.uuid), raw_tool_calls)
            tool_call_records.extend(round_records)
            conversation.extend(tool_result_messages)

        else:
            logger.warning(
                "[generate_bot_response] MAX_TOOL_ROUNDS (%d) exhausted — final structured call",
                MAX_TOOL_ROUNDS,
            )
            try:
                agent_response, _, usage = provider.generate_with_conversation(
                    model, conversation, None, SupportAgentResponse
                )
                final_usage = _build_usage_meta(usage)
            except Exception:
                agent_response = SupportAgentResponse(
                    answer="Unable to complete the request after maximum tool rounds.",
                    status=ResponseStatus.INSUFFICIENT_INFORMATION,
                    escalation=False,
                    reason_for_escalation="",
                    sentiment_score=50,
                    escalation_score=0,
                    criticality_score=0,
                )

        if intermediate_message is not None:
            intermediate_message.metadata = {
                **intermediate_message.metadata,
                "tool_calls": tool_call_records,
            }
            intermediate_message.save(update_fields=["metadata"])
            _send_live_update_to_dashboard(intermediate_message, user_message)

    except Exception as e:
        logger.error(
            "[generate_bot_response] Pipeline error | error=%s", e, exc_info=True,
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

    escalation_service = EscalationService()
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
    else:
        escalation_metadata = {}

    final_tool_calls = [] if intermediate_message is not None else tool_call_records

    final_metadata = {
        "status": str(agent_response.status),
        "escalation": agent_response.escalation,
        "reason_for_escalation": agent_response.reason_for_escalation,
        "sentiment_score": agent_response.sentiment_score,
        "escalation_score": agent_response.escalation_score,
        "criticality_score": agent_response.criticality_score,
        "tool_calls": final_tool_calls,
        "escalation_reason": escalation_metadata.get("escalation_reason", ""),
        "notified_profiles": escalation_metadata.get("notified_profiles", []),
        "usage": final_usage,
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
        "[generate_bot_response] Done | bot_message_id=%s status=%s",
        bot_message.id, final_metadata.get("status"),
    )

    _send_live_update(bot_message, user_message)
