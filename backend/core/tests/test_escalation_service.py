"""
Property and unit tests for EscalationService.

# Feature: intelligent-chat-pipeline, Property 9: Escalation triggers chatroom status update, notifications, and metadata
# Feature: intelligent-chat-pipeline, Property 10: Escalation cooldown suppresses re-escalation; expiry re-enables it
# Feature: intelligent-chat-pipeline, Property 11: User-requested escalation bypasses cooldown
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock, call

from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st

from core.agent_response_schema import ResponseStatus, SupportAgentResponse
from core.services.escalation_service import EscalationService

settings.register_profile("ci", max_examples=100)
settings.load_profile("ci")

# ---------------------------------------------------------------------------
# Helpers / builders
# ---------------------------------------------------------------------------

def _make_response(
    escalation_score: int = 50,
    status: ResponseStatus = ResponseStatus.ANSWERED,
    reason: str = "test reason",
) -> SupportAgentResponse:
    return SupportAgentResponse(
        answer="test answer",
        status=status,
        escalation=escalation_score >= 50,
        reason_for_escalation=reason,
        sentiment_score=50,
        escalation_score=escalation_score,
        criticality_score=50,
    )


def _make_chatroom(
    is_escalated: bool = False,
    escalated_at: datetime | None = None,
    cooldown_hours: int = 24,
    name: str = "Test Room",
):
    chatroom = MagicMock()
    chatroom.is_escalated = is_escalated
    chatroom.escalated_at = escalated_at
    chatroom.escalation_cooldown_hours = cooldown_hours
    chatroom.name = name
    return chatroom


def _make_application():
    app = MagicMock()
    app.name = "Test App"
    return app


def _make_app_profile(profile_name: str, profile_type: str = "slack"):
    profile = MagicMock()
    profile.name = profile_name
    profile.type = profile_type
    profile.config = {"webhookUrl": "https://hooks.slack.com/test"}

    app_profile = MagicMock()
    app_profile.notification_profile = profile
    return app_profile


# ---------------------------------------------------------------------------
# Property 9: Escalation triggers chatroom status update, notifications, and metadata
# Validates: Requirements 5.1, 5.2, 5.3, 5.4
# ---------------------------------------------------------------------------

@given(
    escalation_score=st.integers(min_value=0, max_value=100),
    threshold=st.integers(min_value=0, max_value=100),
    num_profiles=st.integers(min_value=0, max_value=5),
    reason=st.text(min_size=0, max_size=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property9_escalation_triggers_all_side_effects(
    escalation_score, threshold, num_profiles, reason
):
    """
    # Feature: intelligent-chat-pipeline, Property 9: Escalation triggers chatroom status update, notifications, and metadata
    Validates: Requirements 5.1, 5.2, 5.3, 5.4

    When escalation_score >= threshold (and no cooldown suppression), escalate() must:
    - Set chatroom.is_escalated = True
    - Set chatroom.escalated_at to a non-None datetime
    - Dispatch a notification for each NotificationProfile
    - Return dict with 'escalation_reason' and 'notified_profiles' keys
    """
    assume(escalation_score >= threshold)

    service = EscalationService()
    chatroom = _make_chatroom(is_escalated=False)
    application = _make_application()
    agent_response = _make_response(escalation_score=escalation_score, reason=reason)

    profile_names = [f"Profile {i}" for i in range(num_profiles)]
    app_profiles = [_make_app_profile(name) for name in profile_names]

    with patch("core.services.escalation_service.AppNotificationProfile") as mock_anp, \
         patch("core.services.escalation_service.send_notification_task") as mock_task:

        mock_anp.objects.select_related.return_value.filter.return_value = app_profiles

        result = service.escalate(chatroom, application, agent_response)

    # chatroom must be marked escalated
    assert chatroom.is_escalated is True
    assert chatroom.escalated_at is not None

    # save must have been called
    chatroom.save.assert_called_once()

    # one notification per profile
    assert mock_task.delay.call_count == num_profiles

    # metadata keys must be present
    assert "escalation_reason" in result
    assert "notified_profiles" in result
    assert isinstance(result["notified_profiles"], list)
    assert len(result["notified_profiles"]) == num_profiles
    for name in profile_names:
        assert name in result["notified_profiles"]


# ---------------------------------------------------------------------------
# Property 10: Escalation cooldown suppresses re-escalation; expiry re-enables it
# Validates: Requirements 5.5, 5.6
# ---------------------------------------------------------------------------

@given(
    escalation_score=st.integers(min_value=0, max_value=100),
    threshold=st.integers(min_value=0, max_value=100),
    cooldown_hours=st.integers(min_value=1, max_value=168),
    hours_since_escalation=st.floats(min_value=0.0, max_value=336.0, allow_nan=False),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
def test_property10_cooldown_suppresses_and_expiry_reenables(
    escalation_score, threshold, cooldown_hours, hours_since_escalation
):
    """
    # Feature: intelligent-chat-pipeline, Property 10: Escalation cooldown suppresses re-escalation; expiry re-enables it
    Validates: Requirements 5.5, 5.6

    For a chatroom already escalated:
    - If within cooldown window → should_escalate returns False (suppressed)
    - If cooldown has elapsed → should_escalate returns True (re-escalation allowed)
    """
    assume(escalation_score >= threshold)

    service = EscalationService()
    agent_response = _make_response(
        escalation_score=escalation_score,
        status=ResponseStatus.ANSWERED,
    )

    now = datetime.now(tz=timezone.utc)
    escalated_at = now - timedelta(hours=hours_since_escalation)

    chatroom = _make_chatroom(
        is_escalated=True,
        escalated_at=escalated_at,
        cooldown_hours=cooldown_hours,
    )

    result = service.should_escalate(chatroom, agent_response, threshold)

    within_cooldown = hours_since_escalation < cooldown_hours
    if within_cooldown:
        assert result is False, (
            f"Expected suppression: hours_since={hours_since_escalation:.2f}, "
            f"cooldown={cooldown_hours}"
        )
    else:
        assert result is True, (
            f"Expected re-escalation: hours_since={hours_since_escalation:.2f}, "
            f"cooldown={cooldown_hours}"
        )


# ---------------------------------------------------------------------------
# Property 11: User-requested escalation bypasses cooldown
# Validates: Requirements 5.7
# ---------------------------------------------------------------------------

@given(
    cooldown_hours=st.integers(min_value=1, max_value=168),
    hours_since_escalation=st.floats(min_value=0.0, max_value=48.0, allow_nan=False),
    threshold=st.integers(min_value=0, max_value=100),
    escalation_score=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property11_user_requested_bypasses_cooldown(
    cooldown_hours, hours_since_escalation, threshold, escalation_score
):
    """
    # Feature: intelligent-chat-pipeline, Property 11: User-requested escalation bypasses cooldown
    Validates: Requirements 5.7

    When status == USER_REQUESTED_ESCALATION, should_escalate must return True
    regardless of cooldown state, is_escalated flag, or escalation_score.
    """
    assume(hours_since_escalation < cooldown_hours)  # ensure we're within cooldown

    service = EscalationService()
    agent_response = _make_response(
        escalation_score=escalation_score,
        status=ResponseStatus.USER_REQUESTED_ESCALATION,
    )

    now = datetime.now(tz=timezone.utc)
    escalated_at = now - timedelta(hours=hours_since_escalation)

    # Chatroom is already escalated and within cooldown — normally suppressed
    chatroom = _make_chatroom(
        is_escalated=True,
        escalated_at=escalated_at,
        cooldown_hours=cooldown_hours,
    )

    result = service.should_escalate(chatroom, agent_response, threshold)

    assert result is True, (
        "USER_REQUESTED_ESCALATION must bypass cooldown and always return True"
    )


# ---------------------------------------------------------------------------
# Unit tests — threshold boundary conditions
# ---------------------------------------------------------------------------

class TestEscalationServiceUnit:

    def test_score_equal_to_threshold_triggers_escalation(self):
        """score == threshold should escalate (>= comparison)."""
        service = EscalationService()
        chatroom = _make_chatroom(is_escalated=False)
        response = _make_response(escalation_score=70)
        assert service.should_escalate(chatroom, response, escalation_threshold=70) is True

    def test_score_below_threshold_does_not_escalate(self):
        """score == threshold - 1 should NOT escalate."""
        service = EscalationService()
        chatroom = _make_chatroom(is_escalated=False)
        response = _make_response(escalation_score=69)
        assert service.should_escalate(chatroom, response, escalation_threshold=70) is False

    def test_score_above_threshold_triggers_escalation(self):
        service = EscalationService()
        chatroom = _make_chatroom(is_escalated=False)
        response = _make_response(escalation_score=80)
        assert service.should_escalate(chatroom, response, escalation_threshold=70) is True

    def test_cooldown_suppresses_when_within_window(self):
        service = EscalationService()
        now = datetime.now(tz=timezone.utc)
        chatroom = _make_chatroom(
            is_escalated=True,
            escalated_at=now - timedelta(hours=1),
            cooldown_hours=24,
        )
        response = _make_response(escalation_score=90)
        assert service.should_escalate(chatroom, response, escalation_threshold=50) is False

    def test_cooldown_allows_when_expired(self):
        service = EscalationService()
        now = datetime.now(tz=timezone.utc)
        chatroom = _make_chatroom(
            is_escalated=True,
            escalated_at=now - timedelta(hours=25),
            cooldown_hours=24,
        )
        response = _make_response(escalation_score=90)
        assert service.should_escalate(chatroom, response, escalation_threshold=50) is True

    def test_user_requested_bypasses_cooldown_unit(self):
        service = EscalationService()
        now = datetime.now(tz=timezone.utc)
        chatroom = _make_chatroom(
            is_escalated=True,
            escalated_at=now - timedelta(hours=1),
            cooldown_hours=24,
        )
        response = _make_response(
            escalation_score=10,
            status=ResponseStatus.USER_REQUESTED_ESCALATION,
        )
        assert service.should_escalate(chatroom, response, escalation_threshold=50) is True

    def test_escalate_sets_chatroom_fields(self):
        service = EscalationService()
        chatroom = _make_chatroom()
        application = _make_application()
        response = _make_response(reason="critical issue")

        with patch("core.services.escalation_service.AppNotificationProfile") as mock_anp, \
             patch("core.services.escalation_service.send_notification_task"):
            mock_anp.objects.select_related.return_value.filter.return_value = []
            service.escalate(chatroom, application, response)

        assert chatroom.is_escalated is True
        assert chatroom.escalated_at is not None
        chatroom.save.assert_called_once_with(update_fields=["is_escalated", "escalated_at"])

    def test_escalate_returns_correct_metadata_keys(self):
        service = EscalationService()
        chatroom = _make_chatroom()
        application = _make_application()
        response = _make_response(reason="urgent")

        with patch("core.services.escalation_service.AppNotificationProfile") as mock_anp, \
             patch("core.services.escalation_service.send_notification_task"):
            mock_anp.objects.select_related.return_value.filter.return_value = []
            result = service.escalate(chatroom, application, response)

        assert "escalation_reason" in result
        assert "notified_profiles" in result
        assert result["escalation_reason"] == "urgent"
        assert result["notified_profiles"] == []

    def test_escalate_logs_error_and_continues_on_notification_failure(self):
        """Notification errors must not propagate — log and continue."""
        service = EscalationService()
        chatroom = _make_chatroom()
        application = _make_application()
        response = _make_response()

        good_profile = _make_app_profile("GoodProfile")
        bad_profile = _make_app_profile("BadProfile")

        with patch("core.services.escalation_service.AppNotificationProfile") as mock_anp, \
             patch("core.services.escalation_service.send_notification_task") as mock_task:

            mock_anp.objects.select_related.return_value.filter.return_value = [
                bad_profile,
                good_profile,
            ]
            # First call raises, second succeeds
            mock_task.delay.side_effect = [RuntimeError("network error"), None]

            result = service.escalate(chatroom, application, response)

        # Should not raise; good profile still notified
        assert "GoodProfile" in result["notified_profiles"]
        assert "BadProfile" not in result["notified_profiles"]

    def test_not_escalated_chatroom_no_cooldown_check(self):
        """If chatroom is not escalated, cooldown is irrelevant."""
        service = EscalationService()
        chatroom = _make_chatroom(is_escalated=False, escalated_at=None)
        response = _make_response(escalation_score=80)
        assert service.should_escalate(chatroom, response, escalation_threshold=50) is True

    def test_escalated_at_none_treated_as_no_cooldown(self):
        """is_escalated=True but escalated_at=None → no cooldown active → escalate."""
        service = EscalationService()
        chatroom = _make_chatroom(is_escalated=True, escalated_at=None, cooldown_hours=24)
        response = _make_response(escalation_score=80)
        assert service.should_escalate(chatroom, response, escalation_threshold=50) is True
