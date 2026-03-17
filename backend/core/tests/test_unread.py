"""
Tests for core.services.unread — mark_unread_for_participants

Covers:
  - Property 6: Internal messages update dashboard unread but not widget unread
    Validates: Requirements 2.8, 2.9, 6.7
  - Property 17: All dashboard participants (except sender) get has_unread=True on new message
    Validates: Requirements 7.2
"""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from django.contrib.auth.models import User

from core.models.application import Application
from core.models.chatroom import ChatRoom
from core.models.chatroom_participant import ChatroomParticipant
from core.services.unread import mark_unread_for_participants


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app():
    user = User.objects.create_user(username=f"u_{User.objects.count()}", password="x")
    return Application.objects.create(owner=user, name="TestApp")


def _make_chatroom(app=None):
    if app is None:
        app = _make_app()
    return ChatRoom.objects.create(application=app, name="TestRoom")


def _add_participant(chatroom, identifier, has_unread=False):
    return ChatroomParticipant.objects.create(
        chatroom=chatroom,
        user_identifier=identifier,
        has_unread=has_unread,
    )


# ---------------------------------------------------------------------------
# Property 6: Internal messages update dashboard unread but not widget unread
# Validates: Requirements 2.8, 2.9, 6.7
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@given(
    dashboard_ids=st.lists(
        st.integers(min_value=1, max_value=9999),
        min_size=1,
        max_size=5,
        unique=True,
    ),
    widget_ids=st.lists(
        st.from_regex(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', fullmatch=True),
        min_size=1,
        max_size=5,
        unique=True,
    ),
)
@settings(max_examples=10, deadline=5000)
def test_internal_message_unread_scoping(dashboard_ids, widget_ids):
    """
    **Property 6: Internal messages update dashboard unread but not widget unread**
    **Validates: Requirements 2.8, 2.9, 6.7**

    When mark_unread_for_participants is called with is_internal=True:
    - All returned identifiers must start with 'dashboard_'
    - No widget_ participant should have has_unread=True
    """
    chatroom = _make_chatroom()
    sender = f"dashboard_{dashboard_ids[0]}"

    # Add dashboard participants (first one is the sender)
    for did in dashboard_ids:
        _add_participant(chatroom, f"dashboard_{did}")

    # Add widget participants
    for wid in widget_ids:
        _add_participant(chatroom, f"widget_{wid}")

    updated = mark_unread_for_participants(chatroom, sender_identifier=sender, is_internal=True)

    # All returned identifiers must be dashboard_ prefixed
    for uid in updated:
        assert uid.startswith('dashboard_'), f"Expected dashboard_ prefix, got: {uid}"

    # No widget participant should have has_unread=True
    widget_unread = ChatroomParticipant.objects.filter(
        chatroom=chatroom,
        user_identifier__startswith='widget_',
        has_unread=True,
    )
    assert not widget_unread.exists(), "widget_ participants should not have has_unread=True for internal messages"


# ---------------------------------------------------------------------------
# Property 17: All dashboard participants (except sender) get has_unread=True
# Validates: Requirements 7.2
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@given(
    dashboard_ids=st.lists(
        st.integers(min_value=1, max_value=9999),
        min_size=2,
        max_size=6,
        unique=True,
    ),
    sender_index=st.integers(min_value=0, max_value=1),
)
@settings(max_examples=10, deadline=5000)
def test_dashboard_participants_get_unread_on_new_message(dashboard_ids, sender_index):
    """
    **Property 17: All dashboard participants (except sender) get has_unread=True on new message**
    **Validates: Requirements 7.2**

    When mark_unread_for_participants is called (is_internal=False by default):
    - All dashboard_ participants except the sender should have has_unread=True
    """
    chatroom = _make_chatroom()
    sender = f"dashboard_{dashboard_ids[sender_index % len(dashboard_ids)]}"

    for did in dashboard_ids:
        _add_participant(chatroom, f"dashboard_{did}")

    mark_unread_for_participants(chatroom, sender_identifier=sender)

    non_sender_dashboard = ChatroomParticipant.objects.filter(
        chatroom=chatroom,
        user_identifier__startswith='dashboard_',
    ).exclude(user_identifier=sender)

    for participant in non_sender_dashboard:
        assert participant.has_unread, (
            f"Expected has_unread=True for {participant.user_identifier}, got False"
        )
