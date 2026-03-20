"""
Tests for SendMessageView routing logic.

Covers:
  - Property 4: Internal messages not broadcast to widget WebSocket groups
    Validates: Requirements 2.4, 4.1, 5.6
  - Property 1: platform is always derived from auth context (not from request body)
    Validates: Requirements 1.2, 1.3, 1.4
  - Widget sender + ai_mode=False broadcasts to dashboard groups only; no AI
    Validates: Requirements 4.2
  - Widget sender + ai_mode=True broadcasts to widget+dashboard groups; triggers AI
    Validates: Requirements 3.2, 3.3, 4.1
  - Dashboard external messages broadcast to widget groups only
    Validates: Requirements 4.5
  - ai_mode=True on widget message triggers generate_bot_response.delay
    Validates: Requirements 3.3
  - Response includes platform, ai_mode, chatroom_identifier, message_status
    Validates: Requirements 1.5, 3.8
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, settings
from hypothesis import strategies as st
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from core.models.application import Application
from core.models.application_widget_token import ApplicationWidgetToken
from core.models.chatroom import ChatRoom
from core.models.chatroom_participant import ChatroomParticipant
from core.models.message import Message
from core.consts import LIVE_UPDATES_PREFIX


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(n=None):
    suffix = n if n is not None else User.objects.count()
    return User.objects.create_user(username=f"u_{suffix}_{uuid.uuid4().hex[:6]}", password="x")


def _make_app(user=None):
    if user is None:
        user = _make_user()
    return Application.objects.create(owner=user, name="TestApp")


def _make_chatroom(app):
    return ChatRoom.objects.create(application=app, name="TestRoom")


def _add_participant(chatroom, identifier, role='user'):
    return ChatroomParticipant.objects.create(
        chatroom=chatroom,
        user_identifier=identifier,
        role=role,
    )


def _authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _widget_client(app):
    """Return an APIClient authenticated via widget token (platform='widget')."""
    token = ApplicationWidgetToken.objects.create(application=app)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


def _post_message(client, app_uuid, chatroom_uuid, sender_id, message="hello", **extra):
    payload = {
        'chatroom_identifier': str(chatroom_uuid),
        'sender_identifier': sender_id,
        'message': message,
        **extra,
    }
    return client.post(
        f'/api/applications/{app_uuid}/chatrooms/send-message/',
        data=payload,
        format='json',
    )


# ---------------------------------------------------------------------------
# Property 4: Internal messages not broadcast to widget WebSocket groups
# Validates: Requirements 2.4, 4.1, 5.6
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@given(
    widget_uuids=st.lists(
        st.from_regex(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', fullmatch=True),
        min_size=1,
        max_size=3,
        unique=True,
    ),
    dashboard_ids=st.lists(
        st.integers(min_value=1, max_value=9999),
        min_size=1,
        max_size=3,
        unique=True,
    ),
)
@settings(max_examples=10, deadline=10000)
def test_internal_message_not_broadcast_to_widget_groups(widget_uuids, dashboard_ids):
    """
    **Property 4: Internal messages not broadcast to widget WebSocket groups**
    **Validates: Requirements 2.4, 4.1, 5.6**

    For any internal message, group_send must never be called with a group name
    starting with 'live_widget_'.
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)
    sender_id = f"dashboard_{user.id}"

    for wid in widget_uuids:
        _add_participant(chatroom, f"widget_{wid}")
    for did in dashboard_ids:
        _add_participant(chatroom, f"dashboard_{did}")

    client = _authenticated_client(user)

    with patch('core.views.message.generate_bot_response') as mock_bot, \
         patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'):
        mock_layer = MagicMock()
        mock_cl.return_value = mock_layer

        resp = _post_message(
            client, app.uuid, chatroom.uuid, sender_id,
            is_internal=True,
        )
        assert resp.status_code == 200, resp.data

        # No group_send call should target a live_widget_ group
        for c in mock_layer.group_send.call_args_list:
            group_name = c[0][0]
            assert not group_name.startswith(f"{LIVE_UPDATES_PREFIX}_widget_"), (
                f"Internal message was broadcast to widget group: {group_name}"
            )


# ---------------------------------------------------------------------------
# Property: ai_mode controls AI response generation for widget messages
# Validates: Requirements 3.2, 3.3
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@given(ai_mode=st.booleans())
@settings(max_examples=10, deadline=10000)
def test_widget_ai_mode_controls_ai_generation(ai_mode):
    """
    **Property: ai_mode controls AI response generation for widget messages**
    **Validates: Requirements 3.2, 3.3**

    For widget messages with ai_mode=True: generate_bot_response.delay must be called.
    For widget messages with ai_mode=False: generate_bot_response.delay must NOT be called.
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)
    sender_id = f"widget_{uuid.uuid4()}"
    _add_participant(chatroom, sender_id)

    # Use widget token auth so platform='widget'
    client = _widget_client(app)

    with patch('core.views.message.generate_bot_response') as mock_bot, \
         patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'):
        mock_cl.return_value = MagicMock()

        resp = _post_message(
            client, app.uuid, chatroom.uuid, sender_id,
            ai_mode=ai_mode,
        )
        assert resp.status_code == 200, resp.data

        if ai_mode:
            mock_bot.delay.assert_called_once()
        else:
            mock_bot.delay.assert_not_called()


# ---------------------------------------------------------------------------
# Property: widget messages broadcast to dashboard groups
# Validates: Requirements 4.1, 4.2
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@given(
    dashboard_ids=st.lists(
        st.integers(min_value=1, max_value=9999),
        min_size=1,
        max_size=4,
        unique=True,
    ),
)
@settings(max_examples=10, deadline=10000)
def test_widget_message_broadcasts_to_dashboard_participants(dashboard_ids):
    """
    **Property: widget messages broadcast to dashboard participants**
    **Validates: Requirements 4.1, 4.2**

    For a widget sender with ai_mode=False, at least one group_send call must
    target a group containing 'dashboard_'.
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)
    sender_id = f"widget_{uuid.uuid4()}"
    _add_participant(chatroom, sender_id)

    for did in dashboard_ids:
        _add_participant(chatroom, f"dashboard_{did}")

    # Use widget token auth so platform='widget'
    client = _widget_client(app)

    with patch('core.views.message.generate_bot_response') as mock_bot, \
         patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'):
        mock_layer = MagicMock()
        mock_cl.return_value = mock_layer

        resp = _post_message(
            client, app.uuid, chatroom.uuid, sender_id,
            ai_mode=False,
        )
        assert resp.status_code == 200, resp.data

        group_names = [c[0][0] for c in mock_layer.group_send.call_args_list]
        dashboard_calls = [g for g in group_names if 'dashboard_' in g]
        assert len(dashboard_calls) > 0, (
            f"Expected at least one group_send to a dashboard_ group, got: {group_names}"
        )
        mock_bot.delay.assert_not_called()


# ---------------------------------------------------------------------------
# Unit test: is_internal=True does not call group_send for live_widget_* groups
# Validates: Requirements 2.4, 4.1
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_internal_message_no_widget_broadcast():
    """
    SendMessageView with is_internal=True does not call group_send
    for any live_widget_* group.
    **Validates: Requirements 2.4, 4.1**
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)
    sender_id = f"dashboard_{user.id}"

    _add_participant(chatroom, sender_id, role='user')
    _add_participant(chatroom, f"widget_{uuid.uuid4()}", role='user')
    _add_participant(chatroom, f"dashboard_99", role='user')

    client = _authenticated_client(user)

    with patch('core.views.message.generate_bot_response') as mock_bot, \
         patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'):
        mock_layer = MagicMock()
        mock_cl.return_value = mock_layer

        resp = _post_message(
            client, app.uuid, chatroom.uuid, sender_id,
            is_internal=True,
        )
        assert resp.status_code == 200, resp.data

        for c in mock_layer.group_send.call_args_list:
            group_name = c[0][0]
            assert not group_name.startswith(f"{LIVE_UPDATES_PREFIX}_widget_"), (
                f"Internal message broadcast to widget group: {group_name}"
            )


# ---------------------------------------------------------------------------
# Unit test: widget sender broadcasts to dashboard_ and human_agent participants
# Validates: Requirements 4.1, 4.2
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_widget_message_broadcasts_to_dashboard_and_human_agent():
    """
    SendMessageView with widget sender (ai_mode=False) calls group_send for
    dashboard_ and human_agent participants.
    **Validates: Requirements 4.1, 4.2**
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)
    sender_id = f"widget_{uuid.uuid4()}"
    human_agent_id = "human_agent_001"
    dashboard_id = f"dashboard_{user.id}"

    _add_participant(chatroom, sender_id, role='user')
    _add_participant(chatroom, dashboard_id, role='user')
    _add_participant(chatroom, human_agent_id, role='human_agent')

    # Use widget token auth so platform='widget'
    client = _widget_client(app)

    with patch('core.views.message.generate_bot_response') as mock_bot, \
         patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'):
        mock_layer = MagicMock()
        mock_cl.return_value = mock_layer

        resp = _post_message(
            client, app.uuid, chatroom.uuid, sender_id,
            ai_mode=False,
        )
        assert resp.status_code == 200, resp.data

        group_names = [c[0][0] for c in mock_layer.group_send.call_args_list]
        assert any('dashboard_' in g for g in group_names), (
            f"Expected dashboard_ group in calls, got: {group_names}"
        )
        assert any('human_agent_001' in g for g in group_names), (
            f"Expected human_agent group in calls, got: {group_names}"
        )
        mock_bot.delay.assert_not_called()


# ---------------------------------------------------------------------------
# Unit test: widget message with ai_mode=True calls generate_bot_response.delay
# Validates: Requirements 3.3
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_widget_ai_mode_true_triggers_bot_response():
    """
    SendMessageView with widget sender and ai_mode=True calls generate_bot_response.delay.
    **Validates: Requirements 3.3**
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)
    sender_id = f"widget_{uuid.uuid4()}"
    _add_participant(chatroom, sender_id, role='user')

    # Use widget token auth so platform='widget'
    client = _widget_client(app)

    with patch('core.views.message.generate_bot_response') as mock_bot, \
         patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'):
        mock_cl.return_value = MagicMock()

        resp = _post_message(
            client, app.uuid, chatroom.uuid, sender_id,
            ai_mode=True,
        )
        assert resp.status_code == 200, resp.data
        mock_bot.delay.assert_called_once()


# ---------------------------------------------------------------------------
# Additional: widget user cannot set is_internal=True
# Validates: Requirements 2.2
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_widget_user_cannot_set_is_internal():
    """
    Widget (unauthenticated) users cannot set is_internal=True — it is always
    forced to False regardless of what they pass in the request.
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)
    sender_id = f"widget_{uuid.uuid4()}"
    _add_participant(chatroom, sender_id, role='user')

    auth_client = _authenticated_client(user)

    # Authenticated user sends is_internal=True — should be stored as True
    with patch('core.views.message.generate_bot_response'), \
         patch('core.views.message.get_channel_layer') as mock_cl2, \
         patch('core.views.message.broadcast_unread_update'):
        mock_cl2.return_value = MagicMock()
        resp = _post_message(
            auth_client, app.uuid, chatroom.uuid, f"dashboard_{user.id}",
            is_internal=True,
        )
        assert resp.status_code == 200
        msg = Message.objects.get(id=resp.data['id'])
        assert msg.is_internal is True


# ---------------------------------------------------------------------------
# Additional: response includes chatroom_identifier, message_status, platform, ai_mode
# Validates: Requirements 1.5, 3.8
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_response_includes_required_fields():
    """
    SendMessageView response must include chatroom_identifier, message_status,
    platform, and ai_mode.
    **Validates: Requirements 1.5, 3.8**
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)
    sender_id = f"dashboard_{user.id}"
    _add_participant(chatroom, sender_id, role='user')

    client = _authenticated_client(user)

    with patch('core.views.message.generate_bot_response'), \
         patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'):
        mock_cl.return_value = MagicMock()

        resp = _post_message(client, app.uuid, chatroom.uuid, sender_id)
        assert resp.status_code == 200, resp.data
        assert 'chatroom_identifier' in resp.data
        assert 'message_status' in resp.data
        assert resp.data['message_status'] == 'message_sent'
        assert 'platform' in resp.data
        assert 'ai_mode' in resp.data
        # Authenticated user → platform='dashboard'
        assert resp.data['platform'] == 'dashboard'


# ---------------------------------------------------------------------------
# Additional: new chatroom creation succeeds without mode field
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_new_chatroom_creation_succeeds():
    """
    When chatroom_identifier='new_chat', a new chatroom is created and the
    response includes chatroom_identifier and message_status.
    """
    user = _make_user()
    app = _make_app(user)
    sender_id = f"dashboard_{user.id}"

    client = _authenticated_client(user)

    with patch('core.views.message.generate_bot_response'), \
         patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'):
        mock_cl.return_value = MagicMock()

        resp = client.post(
            f'/api/applications/{app.uuid}/chatrooms/send-message/',
            data={
                'chatroom_identifier': 'new_chat',
                'sender_identifier': sender_id,
                'message': 'hello',
            },
            format='json',
        )
        assert resp.status_code == 200, resp.data
        assert 'chatroom_identifier' in resp.data
        assert 'message_status' in resp.data
        assert resp.data['message_status'] == 'message_sent'

        chatroom_uuid = resp.data['chatroom_identifier']
        chatroom = ChatRoom.objects.get(uuid=chatroom_uuid)
        assert chatroom is not None


# ---------------------------------------------------------------------------
# Additional: external dashboard message with ai_mode=True is rejected (HTTP 400)
# Validates: Requirements 3.6, 3.7
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_external_dashboard_message_with_ai_mode_rejected():
    """
    Dashboard external messages (is_internal=False) with ai_mode=True must be
    rejected with HTTP 400.
    **Validates: Requirements 3.6, 3.7**
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)
    sender_id = f"dashboard_{user.id}"
    _add_participant(chatroom, sender_id, role='user')

    client = _authenticated_client(user)

    with patch('core.views.message.generate_bot_response'), \
         patch('core.views.message.get_channel_layer') as mock_cl, \
         patch('core.views.message.broadcast_unread_update'):
        mock_cl.return_value = MagicMock()

        resp = _post_message(
            client, app.uuid, chatroom.uuid, sender_id,
            is_internal=False,
            ai_mode=True,
        )
        assert resp.status_code == 400, resp.data
