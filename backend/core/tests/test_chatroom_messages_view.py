"""
Tests for ChatRoomMessagesView message filtering.

Covers:
  - Task 9.1 / Property 5: Widget history excludes internal messages
    Validates: Requirements 2.5, 4.2
  - Task 9.2 / Property 12: Dashboard history returns all messages
    Validates: Requirements 4.3
  - Task 9.3: ChatRoomMessagesView returns only is_internal=False for widget token auth
    Validates: Requirements 2.5, 4.2
  - Task 9.4: ChatRoomMessagesView returns all messages for session-authenticated dashboard user
    Validates: Requirements 4.3
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(suffix=None):
    s = suffix if suffix is not None else uuid.uuid4().hex[:8]
    return User.objects.create_user(username=f"u_{s}", password="x")


def _make_app(user=None):
    if user is None:
        user = _make_user()
    return Application.objects.create(owner=user, name="TestApp")


def _make_chatroom(app):
    return ChatRoom.objects.create(application=app, name="TestRoom")


def _make_message(chatroom, sender_id="widget_abc", text="hello", is_internal=False):
    return Message.objects.create(
        chatroom=chatroom,
        sender_identifier=sender_id,
        message=text,
        is_internal=is_internal,
    )


def _dashboard_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _widget_client(app):
    """Return an APIClient authenticated via widget token."""
    token = ApplicationWidgetToken.objects.create(application=app)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return client


def _get_messages(client, app_uuid, chatroom_uuid, sender_id=None):
    url = f'/api/applications/{app_uuid}/chatrooms/{chatroom_uuid}/messages/'
    if sender_id:
        url += f'?sender_identifier={sender_id}'
    with patch('core.views.chatroom.mark_read_for_participant'), \
         patch('core.views.chatroom.broadcast_unread_update'):
        return client.get(url)


# ---------------------------------------------------------------------------
# Property 5: Widget history excludes internal messages
# Validates: Requirements 2.5, 4.2
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@given(
    internal_count=st.integers(min_value=1, max_value=5),
    public_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=5, deadline=10000)
def test_widget_history_excludes_internal_messages(internal_count, public_count):
    """
    **Property 5: Widget history excludes internal messages**
    **Validates: Requirements 2.5, 4.2**

    For any chatroom with a mix of internal and public messages, a
    widget-authenticated GET must return only messages where is_internal=False.
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)

    for i in range(public_count):
        _make_message(chatroom, sender_id=f"widget_{uuid.uuid4()}", text=f"pub {i}", is_internal=False)
    for i in range(internal_count):
        _make_message(chatroom, sender_id=f"dashboard_{user.id}", text=f"int {i}", is_internal=True)

    client = _widget_client(app)
    resp = _get_messages(client, app.uuid, chatroom.uuid)

    assert resp.status_code == 200, resp.data
    for msg in resp.data['messages']:
        assert msg['is_internal'] is False, f"Widget received internal message: {msg}"
    assert len(resp.data['messages']) == public_count


# ---------------------------------------------------------------------------
# Property 12: Dashboard history returns all messages
# Validates: Requirements 4.3
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@given(
    internal_count=st.integers(min_value=1, max_value=5),
    public_count=st.integers(min_value=1, max_value=5),
)
@settings(max_examples=5, deadline=10000)
def test_dashboard_history_returns_all_messages(internal_count, public_count):
    """
    **Property 12: Dashboard history returns all messages**
    **Validates: Requirements 4.3**

    For any chatroom with a mix of internal and public messages, a
    dashboard-authenticated GET must return all messages regardless of is_internal.
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)

    for i in range(public_count):
        _make_message(chatroom, sender_id=f"widget_{uuid.uuid4()}", text=f"pub {i}", is_internal=False)
    for i in range(internal_count):
        _make_message(chatroom, sender_id=f"dashboard_{user.id}", text=f"int {i}", is_internal=True)

    client = _dashboard_client(user)
    resp = _get_messages(client, app.uuid, chatroom.uuid)

    assert resp.status_code == 200, resp.data
    total = chatroom.messages.count()
    assert len(resp.data['messages']) == total, (
        f"Expected {total} messages, got {len(resp.data['messages'])}"
    )


# ---------------------------------------------------------------------------
# Unit test 9.3: Widget token auth returns only is_internal=False messages
# Validates: Requirements 2.5, 4.2
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_widget_auth_returns_only_public_messages():
    """
    **Task 9.3**: ChatRoomMessagesView returns only is_internal=False messages
    for widget token auth.
    **Validates: Requirements 2.5, 4.2**
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)

    pub1 = _make_message(chatroom, sender_id="widget_aaa", text="public 1", is_internal=False)
    pub2 = _make_message(chatroom, sender_id="widget_bbb", text="public 2", is_internal=False)
    _make_message(chatroom, sender_id=f"dashboard_{user.id}", text="internal", is_internal=True)

    client = _widget_client(app)
    resp = _get_messages(client, app.uuid, chatroom.uuid)

    assert resp.status_code == 200, resp.data
    returned_ids = {m['uuid'] for m in resp.data['messages']}
    assert str(pub1.uuid) in returned_ids
    assert str(pub2.uuid) in returned_ids
    assert len(resp.data['messages']) == 2


# ---------------------------------------------------------------------------
# Unit test 9.4: Dashboard session auth returns all messages
# Validates: Requirements 4.3
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_dashboard_auth_returns_all_messages():
    """
    **Task 9.4**: ChatRoomMessagesView returns all messages for
    session-authenticated dashboard user.
    **Validates: Requirements 4.3**
    """
    user = _make_user()
    app = _make_app(user)
    chatroom = _make_chatroom(app)

    pub = _make_message(chatroom, sender_id="widget_aaa", text="public", is_internal=False)
    internal = _make_message(chatroom, sender_id=f"dashboard_{user.id}", text="internal", is_internal=True)

    client = _dashboard_client(user)
    resp = _get_messages(client, app.uuid, chatroom.uuid)

    assert resp.status_code == 200, resp.data
    returned_ids = {m['uuid'] for m in resp.data['messages']}
    assert str(pub.uuid) in returned_ids
    assert str(internal.uuid) in returned_ids
    assert len(resp.data['messages']) == 2
