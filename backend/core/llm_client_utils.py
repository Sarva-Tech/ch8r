from core.consts import AI_ROLE_AI_AGENT, AI_ROLE_USER, AI_ROLE_UNKNOWN, AI_ROLE_SYSTEM

AI_ROLE_MAP = {
    "agent_llm": AI_ROLE_AI_AGENT,
    "dashboard_": AI_ROLE_USER,
    "widget_": AI_ROLE_USER,
}

def messages_to_llm_conversation(messages_queryset, platform=None):
    conversation = []
    for msg in messages_queryset.order_by("created_at"):
        if platform == "widget" and msg.is_internal:
            continue
        role = next((r for prefix, r in AI_ROLE_MAP.items() if msg.sender_identifier.startswith(prefix)), AI_ROLE_UNKNOWN)
        conversation.append({"role": role, "content": msg.message})
    return conversation

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
