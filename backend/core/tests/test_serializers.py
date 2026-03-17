"""
Tests for ViewMessageSerializer, ChatRoomViewSerializer, ChatRoomPreviewSerializer,
and ChatRoomWithMessagesSerializer.

Covers:
  - Task 6.1 / Property 18: Last message preview includes internal messages for dashboard
    Validates: Requirements 7.7
  - is_internal field exposed in ViewMessageSerializer
  - mode field exposed in ChatRoomViewSerializer, ChatRoomWithMessagesSerializer,
    ChatRoomPreviewSerializer
"""
import pytest
from django.contrib.auth.models import User

from core.models.application import Application
from core.models.chatroom import ChatRoom
from core.models.message import Message
from core.serializers.message import ViewMessageSerializer, CreateMessageSerializer
from core.serializers.chatroom import (
    ChatRoomViewSerializer,
    ChatRoomWithMessagesSerializer,
    ChatRoomPreviewSerializer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app():
    user = User.objects.create_user(username=f"u_{User.objects.count()}", password="x")
    return Application.objects.create(owner=user, name="TestApp")


def _make_chatroom(app=None, mode='ai'):
    if app is None:
        app = _make_app()
    return ChatRoom.objects.create(application=app, name="TestRoom", mode=mode)


def _make_message(chatroom, text="hello", is_internal=False, sender="widget_abc"):
    return Message.objects.create(
        chatroom=chatroom,
        message=text,
        sender_identifier=sender,
        is_internal=is_internal,
    )


# ---------------------------------------------------------------------------
# ViewMessageSerializer — is_internal field
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_view_message_serializer_includes_is_internal():
    """ViewMessageSerializer must expose the is_internal field."""
    chatroom = _make_chatroom()
    msg = _make_message(chatroom, is_internal=True)
    data = ViewMessageSerializer(msg).data
    assert 'is_internal' in data
    assert data['is_internal'] is True


@pytest.mark.django_db
def test_view_message_serializer_is_internal_false_by_default():
    """ViewMessageSerializer returns is_internal=False for participant messages."""
    chatroom = _make_chatroom()
    msg = _make_message(chatroom, is_internal=False)
    data = ViewMessageSerializer(msg).data
    assert data['is_internal'] is False


# ---------------------------------------------------------------------------
# CreateMessageSerializer — is_internal and mode fields; no send_to_participant
# ---------------------------------------------------------------------------

def test_create_message_serializer_has_is_internal():
    """CreateMessageSerializer must accept is_internal."""
    s = CreateMessageSerializer(data={'message': 'hi', 'is_internal': True})
    assert s.is_valid(), s.errors
    assert s.validated_data['is_internal'] is True


def test_create_message_serializer_is_internal_defaults_false():
    """CreateMessageSerializer defaults is_internal to False."""
    s = CreateMessageSerializer(data={'message': 'hi'})
    assert s.is_valid(), s.errors
    assert s.validated_data['is_internal'] is False


def test_create_message_serializer_has_mode():
    """CreateMessageSerializer must accept mode choices."""
    for mode in ('ai', 'direct'):
        s = CreateMessageSerializer(data={'message': 'hi', 'mode': mode})
        assert s.is_valid(), s.errors
        assert s.validated_data['mode'] == mode


def test_create_message_serializer_mode_defaults_ai():
    """CreateMessageSerializer defaults mode to None (no per-message override)."""
    s = CreateMessageSerializer(data={'message': 'hi'})
    assert s.is_valid(), s.errors
    assert s.validated_data['mode'] is None


def test_create_message_serializer_rejects_invalid_mode():
    """CreateMessageSerializer rejects unknown mode values."""
    s = CreateMessageSerializer(data={'message': 'hi', 'mode': 'human'})
    assert not s.is_valid()
    assert 'mode' in s.errors


def test_create_message_serializer_no_send_to_participant():
    """send_to_participant must no longer be a field on CreateMessageSerializer."""
    s = CreateMessageSerializer(data={'message': 'hi', 'send_to_participant': True})
    # send_to_participant is unknown — serializer should still be valid (extra fields ignored)
    # but the field must not appear in validated_data
    assert s.is_valid(), s.errors
    assert 'send_to_participant' not in s.validated_data


# ---------------------------------------------------------------------------
# ChatRoomViewSerializer — mode field
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_chatroom_view_serializer_includes_mode():
    """ChatRoomViewSerializer must expose the mode field."""
    chatroom = _make_chatroom(mode='direct')
    data = ChatRoomViewSerializer(chatroom).data
    assert 'mode' in data
    assert data['mode'] == 'direct'


# ---------------------------------------------------------------------------
# ChatRoomWithMessagesSerializer — mode field
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_chatroom_with_messages_serializer_includes_mode():
    """ChatRoomWithMessagesSerializer must expose the mode field."""
    chatroom = _make_chatroom(mode='ai')
    data = ChatRoomWithMessagesSerializer(chatroom).data
    assert 'mode' in data
    assert data['mode'] == 'ai'


# ---------------------------------------------------------------------------
# ChatRoomPreviewSerializer — mode field + get_last_message (Property 18)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_chatroom_preview_serializer_includes_mode():
    """ChatRoomPreviewSerializer must expose the mode field."""
    chatroom = _make_chatroom(mode='direct')
    data = ChatRoomPreviewSerializer(chatroom).data
    assert 'mode' in data
    assert data['mode'] == 'direct'


@pytest.mark.django_db
def test_get_last_message_returns_internal_when_most_recent():
    """
    **Property 18: Last message preview includes internal messages for dashboard**
    **Validates: Requirements 7.7**

    When the most recent message in a chatroom is internal, get_last_message must
    return that internal message for dashboard users (not the previous participant message).
    Widget users must NOT see the internal message as the last message.
    """
    chatroom = _make_chatroom()
    participant_msg = _make_message(chatroom, text="participant msg", is_internal=False, sender="widget_abc")
    internal_msg = _make_message(chatroom, text="internal msg", is_internal=True, sender="dashboard_1")

    # Dashboard user sees the internal message
    dashboard_data = ChatRoomPreviewSerializer(chatroom, context={'user_identifier': 'dashboard_1'}).data
    assert dashboard_data['last_message'] is not None
    assert dashboard_data['last_message']['is_internal'] is True
    assert dashboard_data['last_message']['message'] == "internal msg"
    assert str(dashboard_data['last_message']['uuid']) == str(internal_msg.uuid)

    # Widget user sees the previous non-internal message
    widget_data = ChatRoomPreviewSerializer(chatroom, context={'user_identifier': 'widget_abc'}).data
    assert widget_data['last_message'] is not None
    assert widget_data['last_message']['is_internal'] is False
    assert widget_data['last_message']['message'] == "participant msg"
    assert str(widget_data['last_message']['uuid']) == str(participant_msg.uuid)


@pytest.mark.django_db
def test_get_last_message_returns_participant_when_most_recent():
    """get_last_message returns the most recent message regardless of is_internal."""
    chatroom = _make_chatroom()
    _make_message(chatroom, text="internal msg", is_internal=True, sender="dashboard_1")
    participant_msg = _make_message(chatroom, text="participant msg", is_internal=False, sender="widget_abc")

    data = ChatRoomPreviewSerializer(chatroom).data
    assert data['last_message'] is not None
    assert data['last_message']['is_internal'] is False
    assert str(data['last_message']['uuid']) == str(participant_msg.uuid)


@pytest.mark.django_db
def test_get_last_message_returns_none_for_empty_chatroom():
    """get_last_message returns None when there are no messages."""
    chatroom = _make_chatroom()
    data = ChatRoomPreviewSerializer(chatroom).data
    assert data['last_message'] is None
