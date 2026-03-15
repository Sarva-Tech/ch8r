import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.models.chatroom_participant import ChatroomParticipant
from core.consts import LIVE_UPDATES_PREFIX

logger = logging.getLogger(__name__)


def mark_unread_for_participants(chatroom, sender_identifier: str) -> list[str]:
    """
    Atomically set has_unread=True on all ChatroomParticipant records
    for the given chatroom, excluding the sender.

    Returns the list of user_identifier values that were updated,
    for use in broadcasting unread notifications.
    """
    ChatroomParticipant.objects.filter(
        chatroom=chatroom
    ).exclude(
        user_identifier=sender_identifier
    ).update(has_unread=True)

    updated_identifiers = list(
        ChatroomParticipant.objects.filter(
            chatroom=chatroom
        ).exclude(
            user_identifier=sender_identifier
        ).values_list("user_identifier", flat=True)
    )

    return updated_identifiers


def broadcast_unread_update(
    user_identifier: str,
    chatroom_uuid: str,
    has_unread: bool,
    sender_identifier: str,
) -> None:
    """
    Broadcast an unread_update event to the user's WebSocket group.
    Logs a warning and continues on failure.
    """
    channel_layer = get_channel_layer()
    group_name = f"{LIVE_UPDATES_PREFIX}_{user_identifier}"
    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_unread_update",
                "chatroom_uuid": chatroom_uuid,
                "has_unread": has_unread,
                "sender_identifier": sender_identifier,
            },
        )
    except Exception as e:
        logger.warning(
            "Failed to broadcast unread update to group %s: %s", group_name, e
        )


def mark_read_for_participant(chatroom, user_identifier: str) -> None:
    """
    Atomically set has_unread=False on the ChatroomParticipant record
    for the given chatroom and user_identifier.
    """
    ChatroomParticipant.objects.filter(
        chatroom=chatroom,
        user_identifier=user_identifier
    ).update(has_unread=False)
