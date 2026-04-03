import logging
from datetime import datetime, timezone

from core.models import AppNotificationProfile
from core.tasks.notification import send_notification_task

logger = logging.getLogger(__name__)


class EscalationService:
    def should_escalate(
        self,
        chatroom,
        agent_response,
        escalation_threshold: int,
    ) -> bool:
        from core.agent_response_schema import ResponseStatus

        if agent_response.status == ResponseStatus.USER_REQUESTED_ESCALATION:
            return True

        if agent_response.escalation_score >= escalation_threshold:
            if chatroom.is_escalated and self._within_cooldown(chatroom):
                return False
            return True

        return False

    def escalate(
        self,
        chatroom,
        application,
        agent_response,
        user_message=None,
    ) -> dict:
        from datetime import datetime, timezone as tz

        chatroom.is_escalated = True
        chatroom.escalated_at = datetime.now(tz=tz.utc)
        chatroom.save(update_fields=["is_escalated", "escalated_at"])

        escalation_reason = agent_response.reason_for_escalation or str(agent_response.status)
        timestamp = chatroom.escalated_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        user_msg_text = user_message.message if user_message else "N/A"
        platform = user_message.platform if user_message else "unknown"
        agent_answer = agent_response.answer if hasattr(agent_response, "answer") else "N/A"

        notification_body = (
            f"New Escalation Alert for {application.name}\n"
            f"{'─' * 40}\n"
            f"👤 User message:  {user_msg_text}\n"
            f"📱 Platform:      {platform}\n"
            f"⚠️  Reason:        {escalation_reason}\n"
            f"🤖 Agent reply:   {agent_answer[:300]}{'...' if len(agent_answer) > 300 else ''}\n"
            f"🕐 Timestamp:     {timestamp}\n"
            f"{'─' * 40}\n"
            f"Chatroom: {chatroom.name}"
        )

        app_profiles = (
            AppNotificationProfile.objects
            .select_related("notification_profile")
            .filter(application=application)
        )

        notified_profiles: list[dict] = []

        for app_profile in app_profiles:
            profile = app_profile.notification_profile
            try:
                channel_data = {
                    "type": profile.type,
                    "config": profile.config,
                }
                send_notification_task.delay(channel_data, notification_body)
                notified_profiles.append({
                    "name": profile.name,
                    "type": profile.type,
                })
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

    def _within_cooldown(self, chatroom) -> bool:
        if chatroom.escalated_at is None:
            return False

        now = datetime.now(tz=timezone.utc)
        escalated_at = chatroom.escalated_at

        if escalated_at.tzinfo is None:
            escalated_at = escalated_at.replace(tzinfo=timezone.utc)

        elapsed_hours = (now - escalated_at).total_seconds() / 3600
        return elapsed_hours < chatroom.escalation_cooldown_hours
