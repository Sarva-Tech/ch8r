import json
import os
import logging

from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db.models import Q
from google.genai.types import FunctionResponse, Content, Part

from core.consts import LIVE_UPDATES_PREFIX, SupportAgentResponse
from core.integrations.utils import get_tools_for_app, execute_tool_call
from core.models import IngestedChunk, Application
from core.models.message import Message

from core.serializers.message import ViewMessageSerializer
from core.services import get_chunks
from core.services.template_loader import TemplateLoader
from core.utils import parse_llm_response

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
AGENT_IDENTIFIER = getattr(settings, "DEFAULT_AGENT_IDENTIFIER", "agent_llm_001")

client = genai.Client()

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
    }

    system_instruction = TemplateLoader.render_template('customer_support.j2', prompt_context)
    print(':::DEBUG System Instruction:::', system_instruction)

    tools = get_tools_for_app(app)

    initial_response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            tools=tools
        ),
        contents=question
    )

    llm_response = ""

    function_calls = [
        part.function_call
        for candidate in initial_response.candidates
        for part in candidate.content.parts
        if part.function_call
    ]

    if function_calls:
        function_responses_parts = []
        for function_call in function_calls:
            print(f"Executing tool: {function_call.name} with args: {function_call.args}")
            try:
                tool_result = execute_tool_call(app, function_call)
                print('tool result ', tool_result)
            except Exception as e:
                print(f"Error executing tool {function_call.name}: {e}")
                tool_result = {"error": f"Failed to execute tool: {e}"}

            function_responses_parts.append(
                FunctionResponse(
                    name=function_call.name,
                    response=tool_result
                )
            )

        conversation_history_with_tools = []
        for entry in chat_history_entries:
            if entry.startswith("AI Agent:"):
                role = "model"
                text = entry[len("AI Agent: "):]
            elif entry.startswith("Human Agent:"):
                role = "model"
                text = entry[len("Human Agent: "):]
            elif entry.startswith("User:"):
                role = "user"
                text = entry[len("User: "):]
            else:
                role = "user"
                text = entry

            conversation_history_with_tools.append(
                Content(role=role, parts=[Part(text=text.strip())])
            )

        conversation_history_with_tools.append(
            initial_response.candidates[0].content
        )

        conversation_history_with_tools.append(
            Content(role='user', parts=[Part(function_response=fr) for fr in function_responses_parts])
        )

        final_response_object = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="Re-write response",
                response_mime_type="application/json",
                response_schema=SupportAgentResponse,
            ),
            contents=conversation_history_with_tools
        )

        llm_response = final_response_object.text

    else:
        conversation_history_without_tools = [
            *chat_history,
            types.Content(role='model', parts=initial_response.candidates[0].content.parts)
        ]
        final_response_object = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="Rewrite response",
                response_mime_type="application/json",
                response_schema=SupportAgentResponse,
            ),
            contents=conversation_history_without_tools
        )
        llm_response = final_response_object.text

    try:
        llm_response_data = parse_llm_response(llm_response)

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
