from core.agent_response_schema import SupportAgentResponse
from core.consts import AI_ROLE_AI_AGENT, AI_ROLE_USER, AI_ROLE_UNKNOWN, AI_ROLE_SYSTEM

from openai.types.shared_params import ResponseFormatJSONSchema

AI_ROLE_MAP = {
    "agent_llm": AI_ROLE_AI_AGENT,
    "reg_": AI_ROLE_USER,
    "anon_": AI_ROLE_USER
}

def messages_to_llm_conversation(messages_queryset):
    conversation = []
    for msg in messages_queryset.order_by("created_at"):
        role = next((r for prefix, r in AI_ROLE_MAP.items() if msg.sender_identifier.startswith(prefix)), AI_ROLE_UNKNOWN)
        conversation.append({"role": role, "content": msg.message})
    return conversation

def get_agent_response_schema(schema_type: str):
    if schema_type == "support_response":
        schema_dict = SupportAgentResponse.model_json_schema()
        return ResponseFormatJSONSchema(
            type="json_schema",
            json_schema={
                "name": "support_agent_response",
                "description": "Schema for the support agent's reply and escalation decision.",
                "schema": schema_dict,
                "strict": True
            }
        )
    else:
        return None

def add_instructions_to_convo(
    conversation,
    instructions,
    role=AI_ROLE_SYSTEM
):
    if instructions:
        conversation.insert(0, {
            "role": role,
            "content": instructions
        })
    return conversation


def add_kb_to_convo(
    conversation,
    kb_data,
    role = AI_ROLE_SYSTEM
):
    if kb_data and kb_data != "NO_CONTEXT":
        conversation.insert(1, {
            "role": role,
            "content": f"Use the following context to answer the user’s question. Only use this information; do not add outside knowledge.\n {kb_data}"
        })
    return conversation
