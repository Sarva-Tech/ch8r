import json
import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Q

from core.consts import LIVE_UPDATES_PREFIX
from core.integrations.integration_dispatcher import get_enabled_tools_for_app, execute_tool_call
from core.llm_client_utils import messages_to_llm_conversation, add_kb_to_convo, \
    add_instructions_to_convo
from core.models import IngestedChunk, Application, Message

from core.serializers.message import ViewMessageSerializer
from core.services.ingestion import get_chunks
from core.services.template_loader import TemplateLoader
from core.services.ai_client_service import AIClientService
from core.services.providers.ai.gemini_provider import GeminiProvider

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

    conversation = messages_to_llm_conversation(messages)
    conversation = add_instructions_to_convo(conversation, system_instruction)
    conversation = add_kb_to_convo(conversation, kb_data)

    answer = ""
    metadata = {"status": "RESOLVED", "escalation": False, "reason_for_escalation": ""}

    try:
        if tools and isinstance(provider, GeminiProvider):
            logger.info(
                "[generate_bot_response] Starting Gemini function-calling loop | max_rounds=%d",
                MAX_TOOL_ROUNDS,
            )
            # --- Gemini function calling loop ---
            contents = [
                {"role": m["role"], "parts": [{"text": m["content"]}]}
                for m in conversation
            ]

            response = None
            for round_num in range(MAX_TOOL_ROUNDS):
                logger.info("[generate_bot_response] Gemini round %d/%d", round_num + 1, MAX_TOOL_ROUNDS)
                response = provider.generate_with_tools(model, contents, tools)
                function_calls = getattr(response, "function_calls", None) or []

                if not function_calls:
                    answer = response.text or ""
                    logger.info(
                        "[generate_bot_response] Gemini final answer received | round=%d answer_length=%d",
                        round_num + 1, len(answer),
                    )
                    break

                logger.info(
                    "[generate_bot_response] Gemini requested %d tool call(s) | round=%d calls=%s",
                    len(function_calls), round_num + 1, [fc.name for fc in function_calls],
                )

                contents.append(response.candidates[0].content)

                tool_response_parts = []
                for fc in function_calls:
                    logger.info(
                        "[generate_bot_response] Executing tool | name=%s args=%s",
                        fc.name, dict(fc.args),
                    )
                    try:
                        result = execute_tool_call(str(app.uuid), fc.name, **dict(fc.args))
                        logger.info(
                            "[generate_bot_response] Tool result | name=%s result=%.200r",
                            fc.name, result,
                        )
                    except Exception as exc:
                        logger.error(
                            "[generate_bot_response] Tool execution failed | name=%s args=%s error=%s",
                            fc.name, dict(fc.args), exc,
                        )
                        result = {"error": str(exc)}

                    tool_response_parts.append({
                        "function_response": {
                            "id": fc.id,
                            "name": fc.name,
                            "response": {"result": result},
                        }
                    })

                contents.append({"role": "user", "parts": tool_response_parts})
            else:
                answer = getattr(response, "text", "") or "Unable to complete the request."
                logger.warning(
                    "[generate_bot_response] Gemini tool loop exhausted max rounds (%d), using last response",
                    MAX_TOOL_ROUNDS,
                )

        else:
            logger.info(
                "[generate_bot_response] Using standard text generation | provider=%s has_tools=%s",
                type(provider).__name__, bool(tools),
            )
            # --- Standard text generation (no tools or non-Gemini provider) ---
            prompt = "\n".join(
                [f"{m.get('role', 'user')}: {m.get('content', '')}" for m in conversation]
            )
            agent_response = provider.generate_text(model, prompt)
            answer = agent_response.answer
            metadata = {
                "status": agent_response.status,
                "escalation": agent_response.escalation,
                "reason_for_escalation": agent_response.reason_for_escalation,
            }
            logger.info(
                "[generate_bot_response] Standard generation complete | status=%s escalation=%s "
                "reason=%r answer_length=%d",
                agent_response.status, agent_response.escalation,
                agent_response.reason_for_escalation, len(answer),
            )

    except Exception as e:
        logger.error(
            "[generate_bot_response] Failed to generate content | error=%s",
            e, exc_info=True,
        )
        answer = str(e)
        metadata = {
            "status": "ERROR",
            "escalation": True,
            "reason_for_escalation": str(e),
            "error_details": str(e),
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
    logger.info(
        "[generate_bot_response] Bot message saved | bot_message_id=%s status=%s escalation=%s",
        bot_message.id, metadata.get("status"), metadata.get("escalation"),
    )

    _send_live_update(bot_message, user_message)
    logger.info(
        "[generate_bot_response] Task complete | message_id=%s bot_message_id=%s",
        message_id, bot_message.id,
    )
