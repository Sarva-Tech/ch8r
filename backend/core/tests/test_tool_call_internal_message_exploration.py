"""
Bug condition exploration test for tool-call intermediate message delivery.

# Spec: tool-call-internal-message
# Task 3.2: Verify fix — assertions inverted to validate correct post-fix behavior

This test validates the FIXED behavior:
- intermediate_message.is_internal == True (always internal, never inherited)
- _send_live_update is NOT called with intermediate_message (not delivered to widget)
- _send_live_update_to_dashboard IS called with intermediate_message (dashboard only)

Validates: Requirements 2.1, 2.2, 2.3
"""
import pytest
from unittest.mock import patch, MagicMock, call
from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st

from core.agent_response_schema import ResponseStatus, SupportAgentResponse


def _make_agent_response(
    answer="Final answer",
    status=ResponseStatus.ANSWERED,
    escalation=False,
    reason="",
    sentiment_score=50,
    escalation_score=10,
    criticality_score=20,
) -> SupportAgentResponse:
    return SupportAgentResponse(
        answer=answer,
        status=status,
        escalation=escalation,
        reason_for_escalation=reason,
        sentiment_score=sentiment_score,
        escalation_score=escalation_score,
        criticality_score=criticality_score,
    )


# ---------------------------------------------------------------------------
# Property 1 (Bug Condition): Intermediate Message Delivered to Widget
# Validates: Requirements 1.1, 1.2, 1.3
# ---------------------------------------------------------------------------

@given(is_internal=st.booleans())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_bug_condition_intermediate_message_delivered_to_widget(is_internal):
    """
    **Validates: Requirements 1.1, 1.2, 1.3**

    Bug condition exploration: for widget user messages (is_internal=False) that
    trigger tool calls, the unfixed code:
      1. Creates intermediate_message with is_internal=False (inherited flag — root cause 1)
      2. Calls _send_live_update with intermediate_message (delivers to widget — bug)
      3. Calls _send_live_update TWICE for intermediate_message (duplicate delivery — root cause 2)

    This test PASSES on unfixed code, confirming the bug exists.
    It will be inverted in task 3.2 after the fix.
    """
    # Scope to widget users only (is_internal=False)
    assume(not is_internal)

    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    user_msg = Message.objects.create(
        chatroom=chatroom,
        sender_identifier="widget_user1",
        message="List my open issues",
        platform="widget",
        is_internal=is_internal,  # False (widget user)
    )

    # Round 0: returns a tool call
    raw_tool_calls = [{"name": "list_repository_issues", "args": {}, "id": "tc_1"}]
    first_response = _make_agent_response(answer="Calling tool: list_repository_issues")

    # Round 1: returns final structured answer (no tool calls)
    final_response = _make_agent_response(answer="Here are your open issues.")

    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.side_effect = [
        (first_response, raw_tool_calls, {}),   # round 0: tool calls
        (final_response, [], {}),                # round 1: final answer
    ]

    mock_executor = MagicMock()
    mock_executor.execute_all.return_value = (
        [{"name": "list_repository_issues", "raw_result": "issue1, issue2",
          "input_parameters": {}, "url": "", "raw_arguments": {},
          "timestamp": "2024-01-01T00:00:00+00:00", "duration_ms": 10}],
        [{"role": "tool", "tool_call_id": "tc_1",
          "name": "list_repository_issues", "content": "issue1, issue2"}],
    )

    with patch("core.tasks.message.AIClientService") as mock_ais, \
         patch("core.tasks.message.get_enabled_tools_for_app",
               return_value=[{"function": {"name": "list_repository_issues"}}]), \
         patch("core.tasks.message.IngestedChunk.objects.filter") as mock_chunks, \
         patch("core.tasks.message.get_chunks", return_value="NO_CONTEXT"), \
         patch("core.tasks.message.TemplateLoader.render_template", return_value="system prompt"), \
         patch("core.models.AppIntegration.objects.filter") as mock_ai_filter, \
         patch("core.tasks.message.ToolCallExecutor", return_value=mock_executor), \
         patch("core.tasks.message.EscalationService") as mock_esc_cls, \
         patch("core.tasks.message._send_live_update") as mock_send_live, \
         patch("core.tasks.message._send_live_update_to_dashboard") as mock_send_dashboard:

        mock_ais.return_value.get_client_and_model.return_value = (mock_provider, "gemini-pro")
        mock_chunks.return_value.exists.return_value = False
        mock_ai_filter.return_value.select_related.return_value.filter.return_value = []
        mock_esc_cls.return_value.should_escalate.return_value = False

        from core.tasks.message import generate_bot_response
        generate_bot_response(user_msg.id, str(app.uuid))

    # --- Fix verified: intermediate_message.is_internal == True ---
    intermediate_msgs = Message.objects.filter(
        chatroom=chatroom,
        ai_mode=True,
        metadata__stage="tool_planning",
    )
    assert intermediate_msgs.exists(), "Intermediate message must be created when tool calls occur"
    intermediate_message = intermediate_msgs.first()

    # FIX: intermediate_message.is_internal must always be True
    assert intermediate_message.is_internal is True, (
        "intermediate_message.is_internal must be True regardless of user message — "
        "tool-planning messages are always internal"
    )

    # --- Fix verified: _send_live_update NOT called with intermediate_message ---
    all_live_update_calls = mock_send_live.call_args_list
    intermediate_live_calls = [
        c for c in all_live_update_calls
        if c.args and c.args[0].id == intermediate_message.id
    ]
    assert len(intermediate_live_calls) == 0, (
        "_send_live_update must NOT be called with intermediate_message — "
        "widget users must not receive tool-planning messages"
    )

    # --- Fix verified: _send_live_update_to_dashboard called with intermediate_message ---
    dashboard_calls = [
        c for c in mock_send_dashboard.call_args_list
        if c.args and c.args[0].id == intermediate_message.id
    ]
    assert len(dashboard_calls) >= 1, (
        "_send_live_update_to_dashboard must be called with intermediate_message — "
        "dashboard users must still see tool-planning steps in real time"
    )
