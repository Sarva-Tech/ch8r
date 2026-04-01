"""
EscalationService — smart escalation with cooldown logic.

Requirements: 5.1, 5.2, 5.3, 5.5, 5.6, 5.7
"""
import logging
from datetime import datetime, timezone

from core.models import AppNotificationProfile
from core.tasks.notification import send_notification_task

logger = logging.getLogger(__name__)


class EscalationService:
    """
    Encapsulates all escalation logic including cooldown checks and
    notification dispatch.
    """

    def should_escalate(
        self,
        chatroom,
        agent_response,
        escalation_threshold: int,
    ) -> bool:
        """
        Determine whether the current pipeline run should trigger escalation.

        Rules (in priority order):
        1. If status == USER_REQUESTED_ESCALATION → always True (bypasses cooldown).
        2. If escalation_score >= escalation_threshold:
           a. If chatroom.is_escalated and still within cooldown window → False (suppressed).
           b. Otherwise → True.
        3. Otherwise → False.

        Requirements: 5.1, 5.5, 5.6, 5.7
        """
        from core.agent_response_schema import ResponseStatus

        # Rule 1: user explicitly requested escalation — bypass everything.
        if agent_response.status == ResponseStatus.USER_REQUESTED_ESCALATION:
            return True

        # Rule 2: score-based escalation.
        if agent_response.escalation_score >= escalation_threshold:
            if chatroom.is_escalated and self._within_cooldown(chatroom):
                return False  # suppressed by cooldown
            return True

        return False

    def escalate(
        self,
        chatroom,
        application,
        agent_response,
    ) -> dict:
        """
        Perform escalation:
        - Mark chatroom as escalated.
        - Dispatch notifications to all NotificationProfiles for the application.
        - Return metadata dict with ``escalation_reason`` and ``notified_profiles``.

        Notification errors are logged per channel and never re-raised.

        Requirements: 5.1, 5.2, 5.3
        """
        # Update chatroom state.
        chatroom.is_escalated = True
        chatroom.escalated_at = datetime.now(tz=timezone.utc)
        chatroom.save(update_fields=["is_escalated", "escalated_at"])

        escalation_reason = agent_response.reason_for_escalation or str(agent_response.status)

        # Fetch all notification profiles for this application.
        app_profiles = (
            AppNotificationProfile.objects
            .select_related("notification_profile")
            .filter(application=application)
        )

        notified_profiles: list[str] = []

        for app_profile in app_profiles:
            profile = app_profile.notification_profile
            try:
                channel_data = {
                    "type": profile.type,
                    "config": profile.config,
                }
                message = (
                    f"Escalation alert for chatroom '{chatroom.name}'.\n"
                    f"Reason: {escalation_reason}"
                )
                send_notification_task.delay(channel_data, message)
                notified_profiles.append(profile.name)
                logger.info(
                    "[EscalationService] Notification dispatched | profile=%s type=%s",
                    profile.name, profile.type,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "[EscalationService] Failed to dispatch notification | profile=%s error=%s",
                    profile.name, exc, exc_info=True,
                )

        return {
            "escalation_reason": escalation_reason,
            "notified_profiles": notified_profiles,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _within_cooldown(self, chatroom) -> bool:
        """Return True if the chatroom is still within its escalation cooldown window."""
        if chatroom.escalated_at is None:
            return False

        now = datetime.now(tz=timezone.utc)
        escalated_at = chatroom.escalated_at

        # Ensure escalated_at is timezone-aware.
        if escalated_at.tzinfo is None:
            escalated_at = escalated_at.replace(tzinfo=timezone.utc)

        elapsed_hours = (now - escalated_at).total_seconds() / 3600
        return elapsed_hours < chatroom.escalation_cooldown_hours
