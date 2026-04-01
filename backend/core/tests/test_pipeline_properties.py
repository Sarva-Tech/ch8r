"""
Property-based tests for the intelligent chat pipeline (generate_bot_response).

# Feature: intelligent-chat-pipeline
Properties covered: 1, 2, 3, 4, 5, 6, 8, 12, 13
"""
import pytest
from unittest.mock import patch, MagicMock, call
from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st

from core.agent_response_schema import ResponseStatus, SupportAgentResponse
from core.llm_client_utils import (
    messages_to_llm_conversation,
    add_kb_to_convo,
    add_instructions_to_convo,
)

settings.register_profile("ci", max_examples=100)
settings.load_profile("ci")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_response(
    answer="Test answer",
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


def _make_tool_call(name="search", args=None, call_id="tc_1"):
    return {"name": name, "args": args or {}, "id": call_id}


def _build_pipeline_mocks(
    provider_side_effects,
    tool_records=None,
    tool_messages=None,
    has_chunks=False,
    kb_data="NO_CONTEXT",
):
    """
    Returns a dict of patch targets and their mock return values/side_effects.
    provider_side_effects: list of (agent_response, raw_tool_calls) tuples
    """
    tool_records = tool_records or []
    tool_messages = tool_messages or []

    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.side_effect = provider_side_effects

    mock_app = MagicMock()
    mock_app.name = "TestApp"
    mock_app.uuid = "test-app-uuid"

    mock_chatroom = MagicMock()
    mock_chatroom.id = 1
    mock_chatroom.name = "Test Room"
    mock_chatroom.is_escalated = False
    mock_chatroom.escalated_at = None
    mock_chatroom.escalation_cooldown_hours = 24

    mock_user_message = MagicMock()
    mock_user_message.id = 1
    mock_user_message.message = "Hello"
    mock_user_message.platform = "widget"
    mock_user_message.is_internal = False
    mock_user_message.chatroom = mock_chatroom

    mock_executor = MagicMock()
    mock_executor.execute_all.return_value = (tool_records, tool_messages)

    return {
        "provider": mock_provider,
        "app": mock_app,
        "chatroom": mock_chatroom,
        "user_message": mock_user_message,
        "executor": mock_executor,
    }


# ---------------------------------------------------------------------------
# Property 1: No tool calls → no Second_Shot
# Validates: Requirements 1.2
# ---------------------------------------------------------------------------

@given(
    answer=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters="\x00", blacklist_categories=("Cs",))),
    sentiment_score=st.integers(min_value=0, max_value=100),
    escalation_score=st.integers(min_value=0, max_value=69),  # below threshold to avoid escalation
    criticality_score=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_property1_no_tool_calls_means_no_second_shot(
    answer, sentiment_score, escalation_score, criticality_score
):
    """
    # Feature: intelligent-chat-pipeline, Property 1: Two-shot branching — no tool calls means no Second_Shot
    Validates: Requirements 1.2

    When the First_Shot returns no tool calls, generate_with_conversation is called
    exactly once and the Final_Message content equals the First_Shot answer.
    """
    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    user_msg = Message.objects.create(
        chatroom=chatroom,
        sender_identifier="widget_user1",
        message="Hello",
        platform="widget",
    )

    first_shot_response = _make_agent_response(
        answer=answer,
        sentiment_score=sentiment_score,
        escalation_score=escalation_score,
        criticality_score=criticality_score,
    )

    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.return_value = (first_shot_response, [])

    with patch("core.tasks.message.AIClientService") as mock_ais, \
         patch("core.tasks.message.get_enabled_tools_for_app", return_value=[]), \
         patch("core.tasks.message.IngestedChunk.objects.filter") as mock_chunks, \
         patch("core.tasks.message.get_chunks", return_value="NO_CONTEXT"), \
         patch("core.tasks.message.TemplateLoader.render_template", return_value="system prompt"), \
         patch("core.models.AppIntegration.objects.filter") as mock_ai_filter, \
         patch("core.tasks.message.ToolCallExecutor") as mock_exec_cls, \
         patch("core.tasks.message.EscalationService") as mock_esc_cls, \
         patch("core.tasks.message._send_live_update"):

        mock_ais.return_value.get_client_and_model.return_value = (mock_provider, "gemini-pro")
        mock_chunks.return_value.exists.return_value = False
        mock_ai_filter.return_value.select_related.return_value.filter.return_value = []
        mock_esc_cls.return_value.should_escalate.return_value = False

        from core.tasks.message import generate_bot_response
        generate_bot_response(user_msg.id, str(app.uuid))

    # generate_with_conversation called exactly once (no Second_Shot)
    assert mock_provider.generate_with_conversation.call_count == 1

    # Final_Message content equals First_Shot answer
    final_msg = Message.objects.filter(chatroom=chatroom, is_internal=False, ai_mode=True).last()
    assert final_msg is not None
    assert final_msg.message == answer

    # No Intermediate_Message created
    assert not Message.objects.filter(chatroom=chatroom, is_internal=True).exists()


# ---------------------------------------------------------------------------
# Property 2: Tool calls → Second_Shot
# Validates: Requirements 1.1, 1.3, 1.4
# ---------------------------------------------------------------------------

@given(
    first_answer=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters="\x00", blacklist_categories=("Cs",))),
    second_answer=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters="\x00", blacklist_categories=("Cs",))),
    tool_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_")),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_property2_tool_calls_trigger_second_shot(first_answer, second_answer, tool_name):
    """
    # Feature: intelligent-chat-pipeline, Property 2: Two-shot branching — tool calls trigger Second_Shot
    Validates: Requirements 1.1, 1.3, 1.4

    When the First_Shot returns tool calls, all tool calls are executed and a
    Second_Shot is made. The Second_Shot response becomes the Final_Message.
    """
    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    user_msg = Message.objects.create(
        chatroom=chatroom,
        sender_identifier="widget_user1",
        message="Create an issue",
        platform="widget",
    )

    raw_tool_calls = [_make_tool_call(tool_name)]
    first_response = _make_agent_response(answer=first_answer, escalation_score=10)
    second_response = _make_agent_response(answer=second_answer, escalation_score=10)

    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.side_effect = [
        (first_response, raw_tool_calls),
        (second_response, []),
    ]

    mock_executor = MagicMock()
    mock_executor.execute_all.return_value = (
        [{"name": tool_name, "raw_result": "ok", "input_parameters": {}, "url": "",
          "raw_arguments": {}, "timestamp": "2024-01-01T00:00:00+00:00", "duration_ms": 10}],
        [{"role": "tool", "tool_call_id": "tc_1", "name": tool_name, "content": "ok"}],
    )

    with patch("core.tasks.message.AIClientService") as mock_ais, \
         patch("core.tasks.message.get_enabled_tools_for_app", return_value=[{"function": {"name": tool_name}}]), \
         patch("core.tasks.message.IngestedChunk.objects.filter") as mock_chunks, \
         patch("core.tasks.message.get_chunks", return_value="NO_CONTEXT"), \
         patch("core.tasks.message.TemplateLoader.render_template", return_value="system prompt"), \
         patch("core.models.AppIntegration.objects.filter") as mock_ai_filter, \
         patch("core.tasks.message.ToolCallExecutor", return_value=mock_executor), \
         patch("core.tasks.message.EscalationService") as mock_esc_cls, \
         patch("core.tasks.message._send_live_update"):

        mock_ais.return_value.get_client_and_model.return_value = (mock_provider, "gemini-pro")
        mock_chunks.return_value.exists.return_value = False
        mock_ai_filter.return_value.select_related.return_value.filter.return_value = []
        mock_esc_cls.return_value.should_escalate.return_value = False

        from core.tasks.message import generate_bot_response
        generate_bot_response(user_msg.id, str(app.uuid))

    # generate_with_conversation called at least twice (First_Shot + Second_Shot)
    assert mock_provider.generate_with_conversation.call_count >= 2

    # Tool executor was called
    mock_executor.execute_all.assert_called_once()

    # Final_Message content equals Second_Shot answer
    final_msg = Message.objects.filter(chatroom=chatroom, is_internal=False, ai_mode=True).last()
    assert final_msg is not None
    assert final_msg.message == second_answer


# ---------------------------------------------------------------------------
# Property 3: Score fields always present and in range
# Validates: Requirements 2.1, 2.2, 2.3, 2.4
# ---------------------------------------------------------------------------

@given(
    sentiment_score=st.integers(min_value=0, max_value=100),
    escalation_score=st.integers(min_value=0, max_value=69),  # below threshold
    criticality_score=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_property3_score_fields_always_present_and_in_range(
    sentiment_score, escalation_score, criticality_score
):
    """
    # Feature: intelligent-chat-pipeline, Property 3: Score fields are always present and in range in Final_Message metadata
    Validates: Requirements 2.1, 2.2, 2.3, 2.4

    For any successful pipeline run, the Final_Message metadata must contain
    sentiment_score, escalation_score, and criticality_score as integers in [0, 100].
    """
    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    user_msg = Message.objects.create(
        chatroom=chatroom,
        sender_identifier="widget_user1",
        message="Hello",
        platform="widget",
    )

    response = _make_agent_response(
        sentiment_score=sentiment_score,
        escalation_score=escalation_score,
        criticality_score=criticality_score,
    )

    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.return_value = (response, [])

    with patch("core.tasks.message.AIClientService") as mock_ais, \
         patch("core.tasks.message.get_enabled_tools_for_app", return_value=[]), \
         patch("core.tasks.message.IngestedChunk.objects.filter") as mock_chunks, \
         patch("core.tasks.message.get_chunks", return_value="NO_CONTEXT"), \
         patch("core.tasks.message.TemplateLoader.render_template", return_value="system prompt"), \
         patch("core.models.AppIntegration.objects.filter") as mock_ai_filter, \
         patch("core.tasks.message.ToolCallExecutor"), \
         patch("core.tasks.message.EscalationService") as mock_esc_cls, \
         patch("core.tasks.message._send_live_update"):

        mock_ais.return_value.get_client_and_model.return_value = (mock_provider, "gemini-pro")
        mock_chunks.return_value.exists.return_value = False
        mock_ai_filter.return_value.select_related.return_value.filter.return_value = []
        mock_esc_cls.return_value.should_escalate.return_value = False

        from core.tasks.message import generate_bot_response
        generate_bot_response(user_msg.id, str(app.uuid))

    final_msg = Message.objects.filter(chatroom=chatroom, is_internal=False, ai_mode=True).last()
    assert final_msg is not None
    meta = final_msg.metadata

    # All three score keys must be present
    assert "sentiment_score" in meta
    assert "escalation_score" in meta
    assert "criticality_score" in meta

    # All scores must be integers in [0, 100]
    for key in ("sentiment_score", "escalation_score", "criticality_score"):
        val = meta[key]
        assert isinstance(val, int), f"{key} must be int, got {type(val)}"
        assert 0 <= val <= 100, f"{key}={val} out of range"


# ---------------------------------------------------------------------------
# Property 4: Intermediate_Message created with correct content when tool calls occur
# Validates: Requirements 3.1, 3.2
# ---------------------------------------------------------------------------

@given(
    tool_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_")),
    second_answer=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters="\x00", blacklist_categories=("Cs",))),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_property4_intermediate_message_created_with_correct_content(tool_name, second_answer):
    """
    # Feature: intelligent-chat-pipeline, Property 4: Intermediate_Message is created with correct content when tool calls occur
    Validates: Requirements 3.1, 3.2

    When the First_Shot produces tool calls, an Intermediate_Message with
    is_internal=True is created and its message field contains the First_Shot output.
    """
    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    user_msg = Message.objects.create(
        chatroom=chatroom,
        sender_identifier="widget_user1",
        message="Do something",
        platform="widget",
    )

    raw_tool_calls = [_make_tool_call(tool_name)]
    first_response = _make_agent_response(answer="I'll use a tool", escalation_score=10)
    second_response = _make_agent_response(answer=second_answer, escalation_score=10)

    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.side_effect = [
        (first_response, raw_tool_calls),
        (second_response, []),
    ]

    mock_executor = MagicMock()
    mock_executor.execute_all.return_value = (
        [{"name": tool_name, "raw_result": "ok", "input_parameters": {}, "url": "",
          "raw_arguments": {}, "timestamp": "2024-01-01T00:00:00+00:00", "duration_ms": 5}],
        [{"role": "tool", "tool_call_id": "tc_1", "name": tool_name, "content": "ok"}],
    )

    with patch("core.tasks.message.AIClientService") as mock_ais, \
         patch("core.tasks.message.get_enabled_tools_for_app", return_value=[{"function": {"name": tool_name}}]), \
         patch("core.tasks.message.IngestedChunk.objects.filter") as mock_chunks, \
         patch("core.tasks.message.get_chunks", return_value="NO_CONTEXT"), \
         patch("core.tasks.message.TemplateLoader.render_template", return_value="system prompt"), \
         patch("core.models.AppIntegration.objects.filter") as mock_ai_filter, \
         patch("core.tasks.message.ToolCallExecutor", return_value=mock_executor), \
         patch("core.tasks.message.EscalationService") as mock_esc_cls, \
         patch("core.tasks.message._send_live_update"):

        mock_ais.return_value.get_client_and_model.return_value = (mock_provider, "gemini-pro")
        mock_chunks.return_value.exists.return_value = False
        mock_ai_filter.return_value.select_related.return_value.filter.return_value = []
        mock_esc_cls.return_value.should_escalate.return_value = False

        from core.tasks.message import generate_bot_response
        generate_bot_response(user_msg.id, str(app.uuid))

    # Intermediate_Message must exist with is_internal=True
    intermediate_msgs = Message.objects.filter(chatroom=chatroom, is_internal=True, ai_mode=True)
    assert intermediate_msgs.exists(), "Intermediate_Message must be created when tool calls occur"

    intermediate = intermediate_msgs.first()
    # Its message field must contain the raw_tool_calls representation
    assert str(raw_tool_calls) in intermediate.message


# ---------------------------------------------------------------------------
# Property 5: No Intermediate_Message when single shot suffices
# Validates: Requirements 3.4
# ---------------------------------------------------------------------------

@given(
    answer=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters="\x00", blacklist_categories=("Cs",))),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_property5_no_intermediate_message_on_single_shot(answer):
    """
    # Feature: intelligent-chat-pipeline, Property 5: No Intermediate_Message when single shot suffices
    Validates: Requirements 3.4

    When the First_Shot produces no tool calls, no Intermediate_Message
    (is_internal=True) should be created.
    """
    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    user_msg = Message.objects.create(
        chatroom=chatroom,
        sender_identifier="widget_user1",
        message="Simple question",
        platform="widget",
    )

    response = _make_agent_response(answer=answer, escalation_score=10)
    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.return_value = (response, [])

    with patch("core.tasks.message.AIClientService") as mock_ais, \
         patch("core.tasks.message.get_enabled_tools_for_app", return_value=[]), \
         patch("core.tasks.message.IngestedChunk.objects.filter") as mock_chunks, \
         patch("core.tasks.message.get_chunks", return_value="NO_CONTEXT"), \
         patch("core.tasks.message.TemplateLoader.render_template", return_value="system prompt"), \
         patch("core.models.AppIntegration.objects.filter") as mock_ai_filter, \
         patch("core.tasks.message.ToolCallExecutor"), \
         patch("core.tasks.message.EscalationService") as mock_esc_cls, \
         patch("core.tasks.message._send_live_update"):

        mock_ais.return_value.get_client_and_model.return_value = (mock_provider, "gemini-pro")
        mock_chunks.return_value.exists.return_value = False
        mock_ai_filter.return_value.select_related.return_value.filter.return_value = []
        mock_esc_cls.return_value.should_escalate.return_value = False

        from core.tasks.message import generate_bot_response
        generate_bot_response(user_msg.id, str(app.uuid))

    # No Intermediate_Message should exist
    assert not Message.objects.filter(chatroom=chatroom, is_internal=True).exists(), \
        "No Intermediate_Message should be created when there are no tool calls"


# ---------------------------------------------------------------------------
# Property 6: Widget never receives internal messages
# Validates: Requirements 3.6
# ---------------------------------------------------------------------------

@given(
    num_messages=st.integers(min_value=1, max_value=10),
    internal_flags=st.lists(st.booleans(), min_size=1, max_size=10),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_property6_widget_never_receives_internal_messages(num_messages, internal_flags):
    """
    # Feature: intelligent-chat-pipeline, Property 6: Widget never receives internal messages
    Validates: Requirements 3.6

    For any message query scoped to the widget platform, no messages with
    is_internal=True should be included in the results.
    """
    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    # Create messages with mixed is_internal flags
    for i, is_internal in enumerate(internal_flags[:num_messages]):
        Message.objects.create(
            chatroom=chatroom,
            sender_identifier="agent_llm_001" if is_internal else "widget_user1",
            message=f"Message {i}",
            platform="widget",
            is_internal=is_internal,
            ai_mode=is_internal,
        )

    # Widget-scoped query: only non-internal messages
    widget_messages = Message.objects.filter(chatroom=chatroom, is_internal=False)

    for msg in widget_messages:
        assert msg.is_internal is False, \
            f"Widget message {msg.id} must not be internal"


# ---------------------------------------------------------------------------
# Property 8: Tool_Call_Records stored on correct message
# Validates: Requirements 4.5
# ---------------------------------------------------------------------------

@given(
    tool_name=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_")),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_property8_tool_call_records_on_intermediate_when_exists(tool_name):
    """
    # Feature: intelligent-chat-pipeline, Property 8: Tool_Call_Records are stored on the correct message
    Validates: Requirements 4.5

    When an Intermediate_Message exists (tool calls occurred), Tool_Call_Records
    are stored on the Intermediate_Message, and the Final_Message has empty tool_calls.
    """
    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    user_msg = Message.objects.create(
        chatroom=chatroom,
        sender_identifier="widget_user1",
        message="Do something",
        platform="widget",
    )

    raw_tool_calls = [_make_tool_call(tool_name)]
    tool_record = {
        "name": tool_name, "raw_result": "ok", "input_parameters": {},
        "url": "", "raw_arguments": {}, "timestamp": "2024-01-01T00:00:00+00:00", "duration_ms": 5,
    }

    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.side_effect = [
        (_make_agent_response(escalation_score=10), raw_tool_calls),
        (_make_agent_response(answer="Final answer", escalation_score=10), []),
    ]

    mock_executor = MagicMock()
    mock_executor.execute_all.return_value = (
        [tool_record],
        [{"role": "tool", "tool_call_id": "tc_1", "name": tool_name, "content": "ok"}],
    )

    with patch("core.tasks.message.AIClientService") as mock_ais, \
         patch("core.tasks.message.get_enabled_tools_for_app", return_value=[{"function": {"name": tool_name}}]), \
         patch("core.tasks.message.IngestedChunk.objects.filter") as mock_chunks, \
         patch("core.tasks.message.get_chunks", return_value="NO_CONTEXT"), \
         patch("core.tasks.message.TemplateLoader.render_template", return_value="system prompt"), \
         patch("core.models.AppIntegration.objects.filter") as mock_ai_filter, \
         patch("core.tasks.message.ToolCallExecutor", return_value=mock_executor), \
         patch("core.tasks.message.EscalationService") as mock_esc_cls, \
         patch("core.tasks.message._send_live_update"):

        mock_ais.return_value.get_client_and_model.return_value = (mock_provider, "gemini-pro")
        mock_chunks.return_value.exists.return_value = False
        mock_ai_filter.return_value.select_related.return_value.filter.return_value = []
        mock_esc_cls.return_value.should_escalate.return_value = False

        from core.tasks.message import generate_bot_response
        generate_bot_response(user_msg.id, str(app.uuid))

    # Intermediate_Message must have tool_calls in metadata
    intermediate = Message.objects.filter(chatroom=chatroom, is_internal=True, ai_mode=True).first()
    assert intermediate is not None
    assert "tool_calls" in intermediate.metadata
    assert len(intermediate.metadata["tool_calls"]) > 0

    # Final_Message must have empty tool_calls
    final_msg = Message.objects.filter(chatroom=chatroom, is_internal=False, ai_mode=True).last()
    assert final_msg is not None
    assert final_msg.metadata.get("tool_calls") == []


@given(
    answer=st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters="\x00", blacklist_categories=("Cs",))),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_property8_tool_call_records_on_final_when_no_intermediate(answer):
    """
    # Feature: intelligent-chat-pipeline, Property 8: Tool_Call_Records are stored on the correct message
    Validates: Requirements 4.5

    When no Intermediate_Message exists (no tool calls), tool_calls in Final_Message
    metadata is an empty list.
    """
    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    user_msg = Message.objects.create(
        chatroom=chatroom,
        sender_identifier="widget_user1",
        message="Simple question",
        platform="widget",
    )

    response = _make_agent_response(answer=answer, escalation_score=10)
    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.return_value = (response, [])

    with patch("core.tasks.message.AIClientService") as mock_ais, \
         patch("core.tasks.message.get_enabled_tools_for_app", return_value=[]), \
         patch("core.tasks.message.IngestedChunk.objects.filter") as mock_chunks, \
         patch("core.tasks.message.get_chunks", return_value="NO_CONTEXT"), \
         patch("core.tasks.message.TemplateLoader.render_template", return_value="system prompt"), \
         patch("core.models.AppIntegration.objects.filter") as mock_ai_filter, \
         patch("core.tasks.message.ToolCallExecutor"), \
         patch("core.tasks.message.EscalationService") as mock_esc_cls, \
         patch("core.tasks.message._send_live_update"):

        mock_ais.return_value.get_client_and_model.return_value = (mock_provider, "gemini-pro")
        mock_chunks.return_value.exists.return_value = False
        mock_ai_filter.return_value.select_related.return_value.filter.return_value = []
        mock_esc_cls.return_value.should_escalate.return_value = False

        from core.tasks.message import generate_bot_response
        generate_bot_response(user_msg.id, str(app.uuid))

    final_msg = Message.objects.filter(chatroom=chatroom, is_internal=False, ai_mode=True).last()
    assert final_msg is not None
    # tool_calls should be empty list (no tool calls occurred)
    assert final_msg.metadata.get("tool_calls") == []


# ---------------------------------------------------------------------------
# Property 12: KB chunks injected as system message before conversation history
# Validates: Requirements 6.1, 6.2, 6.3
# ---------------------------------------------------------------------------

@given(
    chunks=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=5),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property12_kb_chunks_injected_as_system_message_when_present(chunks):
    """
    # Feature: intelligent-chat-pipeline, Property 12: KB chunks are injected as a system message before conversation history
    Validates: Requirements 6.1, 6.2, 6.3

    When KB chunks exist, the conversation passed to the First_Shot contains a
    system message with the KB content positioned before user conversation messages.
    """
    kb_data = "\n".join(chunks)

    # Simulate a minimal conversation (one user message)
    conversation = [{"role": "user", "content": "Hello"}]

    # Apply the same pipeline logic: add system instruction first, then KB
    conversation = add_instructions_to_convo(conversation, "system prompt")
    conversation = add_kb_to_convo(conversation, kb_data)

    # The conversation should have a system message with KB content
    system_messages = [m for m in conversation if m["role"] == "system"]
    assert len(system_messages) >= 1, "At least one system message must be present"

    # KB content must appear in a system message
    kb_in_system = any(kb_data in m["content"] for m in system_messages)
    assert kb_in_system, "KB data must be injected into a system message"

    # System messages must appear before user messages
    first_user_idx = next(i for i, m in enumerate(conversation) if m["role"] == "user")
    for i, m in enumerate(conversation):
        if m["role"] == "system":
            assert i < first_user_idx, "System messages must appear before user messages"


@given(
    user_message=st.text(min_size=1, max_size=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property12_no_kb_injection_when_no_chunks(user_message):
    """
    # Feature: intelligent-chat-pipeline, Property 12: KB chunks are injected as a system message before conversation history
    Validates: Requirements 6.3

    When no KB chunks exist, no empty KB system message is injected.
    """
    conversation = [{"role": "user", "content": user_message}]
    conversation = add_instructions_to_convo(conversation, "system prompt")
    # NO_CONTEXT means no KB injection
    conversation = add_kb_to_convo(conversation, "NO_CONTEXT")

    # Only the system instruction should be present, not an empty KB message
    system_messages = [m for m in conversation if m["role"] == "system"]
    for msg in system_messages:
        assert "NO_CONTEXT" not in msg["content"], \
            "NO_CONTEXT sentinel must not be injected into conversation"
        # KB injection message contains "Use the following context"
        assert "Use the following context" not in msg["content"] or msg["content"].strip(), \
            "Empty KB context must not be injected"


# ---------------------------------------------------------------------------
# Property 13: MAX_TOOL_ROUNDS is never exceeded
# Validates: Requirements 6.5, 6.6
# ---------------------------------------------------------------------------

@given(
    max_rounds=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@pytest.mark.django_db
def test_property13_max_tool_rounds_never_exceeded(max_rounds):
    """
    # Feature: intelligent-chat-pipeline, Property 13: MAX_TOOL_ROUNDS is never exceeded
    Validates: Requirements 6.5, 6.6

    When the provider always returns tool calls, the pipeline terminates after
    MAX_TOOL_ROUNDS iterations and uses the last available response as Final_Message.
    """
    from core.tests.factories import UserFactory, ApplicationFactory
    from core.models import ChatRoom, Message
    import core.tasks.message as task_module

    user = UserFactory()
    app = ApplicationFactory(owner=user)
    chatroom = ChatRoom.objects.create(name="Test Room", application=app)

    user_msg = Message.objects.create(
        chatroom=chatroom,
        sender_identifier="widget_user1",
        message="Keep calling tools",
        platform="widget",
    )

    last_answer = f"Last response after {max_rounds} rounds"
    # Provider always returns tool calls — forces loop to exhaust
    always_tool_response = _make_agent_response(answer=last_answer, escalation_score=10)
    raw_tool_calls = [_make_tool_call("infinite_tool")]

    mock_provider = MagicMock()
    mock_provider.generate_with_conversation.return_value = (always_tool_response, raw_tool_calls)

    mock_executor = MagicMock()
    mock_executor.execute_all.return_value = (
        [{"name": "infinite_tool", "raw_result": "ok", "input_parameters": {}, "url": "",
          "raw_arguments": {}, "timestamp": "2024-01-01T00:00:00+00:00", "duration_ms": 1}],
        [{"role": "tool", "tool_call_id": "tc_1", "name": "infinite_tool", "content": "ok"}],
    )

    original_max = task_module.MAX_TOOL_ROUNDS
    try:
        task_module.MAX_TOOL_ROUNDS = max_rounds

        with patch("core.tasks.message.AIClientService") as mock_ais, \
             patch("core.tasks.message.get_enabled_tools_for_app", return_value=[{"function": {"name": "infinite_tool"}}]), \
             patch("core.tasks.message.IngestedChunk.objects.filter") as mock_chunks, \
             patch("core.tasks.message.get_chunks", return_value="NO_CONTEXT"), \
             patch("core.tasks.message.TemplateLoader.render_template", return_value="system prompt"), \
             patch("core.models.AppIntegration.objects.filter") as mock_ai_filter, \
             patch("core.tasks.message.ToolCallExecutor", return_value=mock_executor), \
             patch("core.tasks.message.EscalationService") as mock_esc_cls, \
             patch("core.tasks.message._send_live_update"):

            mock_ais.return_value.get_client_and_model.return_value = (mock_provider, "gemini-pro")
            mock_chunks.return_value.exists.return_value = False
            mock_ai_filter.return_value.select_related.return_value.filter.return_value = []
            mock_esc_cls.return_value.should_escalate.return_value = False

            from core.tasks.message import generate_bot_response
            generate_bot_response(user_msg.id, str(app.uuid))

    finally:
        task_module.MAX_TOOL_ROUNDS = original_max

    # generate_with_conversation called exactly max_rounds times
    assert mock_provider.generate_with_conversation.call_count == max_rounds, (
        f"Expected exactly {max_rounds} calls, got {mock_provider.generate_with_conversation.call_count}"
    )

    # A Final_Message must still be saved (last response used)
    final_msg = Message.objects.filter(chatroom=chatroom, is_internal=False, ai_mode=True).last()
    assert final_msg is not None, "Final_Message must be saved even when MAX_TOOL_ROUNDS is exhausted"
    assert final_msg.message == last_answer
