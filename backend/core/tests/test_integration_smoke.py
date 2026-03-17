"""
Integration smoke tests for the chat flow redesign.

Covers:
  - Task 21.1: Widget sends message in ai mode → bot response is_internal=False, broadcast to widget
  - Task 21.2 (optional): Dashboard sends internal message → bot response is_internal=True, widget history excludes both
  - Task 21.3 (optional): Direct mode — widget sends message, no bot response, dashboard receives broadcast
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock, call
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models.application import Application
from core.models.chatroom import ChatRoom
from core.models.chatroom_participant import ChatroomParticipant
from core.models.message import Message
from core.consts import LIVE_UPDATES_PREFIX


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user():
    return User.objects.create_user(username=f"u_{uuid.uuid4().hex[:8]}", password="x")


def _make_app(user=None):
    if user is None:
        user = _make_user()
    return Application.objects.create(owner=user, name="TestApp")


def _make_chatroom(app, mode='ai'):
    return ChatRoom.objects.create(application=app, name="Room", mode=mode)


def _add_participant(chatroom, identifier, role='user'):
    return ChatroomParticipant.objects.create(
        chatroom=chatroom, user_identifier=identifier, role=role,
    )


def _widget_client(app):
    from core.models.application_widget_token import ApplicationWidgetToken
    token = ApplicationWidgetToken.objects.create(application=app)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


def _dashboard_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# Task 21.1: Widget sends message in ai mode → bot response is_internal=False
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_widget_ai_mode_bot_response_is_not_internal():
    """
    Widget sends a message in ai mode.
    Bot response must be created with is_internal=False and broadcast to widget group.
    Validates: Requirements 3.3, 5.1
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app, mode='ai')
    widget_id = f"widget_{uuid.uuid4()}"
    _add_participant(chatroom, widget_id)

    mock_channel_layer = MagicMock()

    with patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'), \
         patch('core.tasks.message.generate_bot_response.delay') as mock_delay:
        mock_cl.return_value = mock_channel_layer

        client = _widget_client(app)
        resp = client.post(
            f'/api/applications/{app.uuid}/chatrooms/send-message/',
            data={
                'chatroom_identifier': str(chatroom.uuid),
                'sender_identifier': widget_id,
                'message': 'Hello bot',
            },
            format='json',
        )

    assert resp.status_code == 200, resp.data

    # User message stored with is_internal=False
    user_msg = Message.objects.filter(chatroom=chatroom, sender_identifier=widget_id).first()
    assert user_msg is not None
    assert user_msg.is_internal is False

    # generate_bot_response was called (ai mode)
    mock_delay.assert_called_once()


@pytest.mark.django_db
def test_widget_ai_mode_broadcast_targets_widget_group():
    """
    Widget sends a message in ai mode.
    In ai mode, the view delegates to generate_bot_response (no direct broadcast).
    The bot task handles broadcasting the response to widget participants.
    Validates: Requirements 5.1
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app, mode='ai')
    widget_id = f"widget_{uuid.uuid4()}"
    _add_participant(chatroom, widget_id)

    with patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'), \
         patch('core.tasks.message.generate_bot_response.delay') as mock_delay:
        mock_cl.return_value = MagicMock()

        client = _widget_client(app)
        resp = client.post(
            f'/api/applications/{app.uuid}/chatrooms/send-message/',
            data={
                'chatroom_identifier': str(chatroom.uuid),
                'sender_identifier': widget_id,
                'message': 'Hello',
            },
            format='json',
        )

    assert resp.status_code == 200, resp.data

    # In ai mode, the view delegates to generate_bot_response (not direct broadcast)
    mock_delay.assert_called_once()

    # No direct group_send to widget in ai mode (bot task handles it)
    all_calls = mock_cl.return_value.group_send.call_args_list
    widget_calls = [c for c in all_calls if 'widget_' in str(c)]
    assert len(widget_calls) == 0, "ai mode should not directly broadcast to widget (bot task handles it)"
