import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from core.services.unread import (
    mark_unread_for_participants,
    broadcast_unread_update,
    mark_read_for_participant
)


@pytest.mark.unit
class TestMarkUnreadForParticipants:
    @patch('core.services.unread.ChatroomParticipant')
    def test_mark_unread_for_participants_success(self, mock_participant_class):
        mock_chatroom = Mock()
        mock_chatroom.uuid = uuid.uuid4()
        sender_identifier = 'user_123'

        mock_queryset = Mock()
        mock_queryset.exclude.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.update.return_value = 3
        mock_queryset.values_list.return_value = ['user_456', 'user_789', 'user_abc']
        mock_participant_class.objects.filter.return_value = mock_queryset

        result = mark_unread_for_participants(mock_chatroom, sender_identifier)

        mock_participant_class.objects.filter.assert_called_once_with(chatroom=mock_chatroom)
        mock_queryset.exclude.assert_called_once_with(user_identifier=sender_identifier)
        mock_queryset.update.assert_called_once_with(has_unread=True)
        assert result == ['user_456', 'user_789', 'user_abc']

    @patch('core.services.unread.ChatroomParticipant')
    def test_mark_unread_for_participants_internal(self, mock_participant_class):
        mock_chatroom = Mock()
        mock_chatroom.uuid = uuid.uuid4()
        sender_identifier = 'dashboard_admin'
        is_internal = True

        mock_queryset = Mock()
        mock_queryset.exclude.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.update.return_value = 2
        mock_queryset.values_list.return_value = ['dashboard_user1', 'dashboard_user2']
        mock_participant_class.objects.filter.return_value = mock_queryset

        result = mark_unread_for_participants(mock_chatroom, sender_identifier, is_internal)

        mock_queryset.exclude.assert_called_once_with(user_identifier=sender_identifier)
        mock_queryset.filter.assert_called_once_with(user_identifier__startswith='dashboard_')
        assert result == ['dashboard_user1', 'dashboard_user2']

    @patch('core.services.unread.ChatroomParticipant')
    def test_mark_unread_for_participants_no_participants(self, mock_participant_class):
        mock_chatroom = Mock()
        mock_chatroom.uuid = uuid.uuid4()
        sender_identifier = 'user_123'

        mock_queryset = Mock()
        mock_queryset.exclude.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.update.return_value = 0
        mock_queryset.values_list.return_value = []
        mock_participant_class.objects.filter.return_value = mock_queryset

        result = mark_unread_for_participants(mock_chatroom, sender_identifier)

        assert result == []

    @patch('core.services.unread.ChatroomParticipant')
    def test_mark_unread_for_participants_only_sender(self, mock_participant_class):
        mock_chatroom = Mock()
        mock_chatroom.uuid = uuid.uuid4()
        sender_identifier = 'user_123'

        mock_queryset = Mock()
        mock_queryset.exclude.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.update.return_value = 0
        mock_queryset.values_list.return_value = []
        mock_participant_class.objects.filter.return_value = mock_queryset

        result = mark_unread_for_participants(mock_chatroom, sender_identifier)

        mock_queryset.exclude.assert_called_once_with(user_identifier=sender_identifier)
        assert result == []


@pytest.mark.unit
class TestBroadcastUnreadUpdate:
    @patch('core.services.unread.async_to_sync')
    @patch('core.services.unread.get_channel_layer')
    def test_broadcast_unread_update_success(self, mock_get_channel_layer, mock_async_to_sync):
        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_async_to_sync.return_value = Mock()

        user_identifier = 'user_123'
        chatroom_uuid = str(uuid.uuid4())
        has_unread = True
        sender_identifier = 'user_456'

        broadcast_unread_update(user_identifier, chatroom_uuid, has_unread, sender_identifier)

        mock_get_channel_layer.assert_called_once()
        mock_async_to_sync.assert_called_once()
        assert mock_async_to_sync.return_value.called

    @patch('core.services.unread.async_to_sync')
    @patch('core.services.unread.get_channel_layer')
    def test_broadcast_unread_update_exception(self, mock_get_channel_layer, mock_async_to_sync):
        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_async_to_sync.side_effect = Exception('WebSocket error')

        user_identifier = 'user_123'
        chatroom_uuid = str(uuid.uuid4())
        has_unread = True
        sender_identifier = 'user_456'

        broadcast_unread_update(user_identifier, chatroom_uuid, has_unread, sender_identifier)

        mock_get_channel_layer.assert_called_once()
        mock_async_to_sync.assert_called_once()

    @patch('core.services.unread.async_to_sync')
    @patch('core.services.unread.get_channel_layer')
    @patch('core.services.unread.LIVE_UPDATES_PREFIX', 'live_updates')
    def test_broadcast_unread_update_group_name(self, mock_get_channel_layer, mock_async_to_sync):
        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer
        mock_async_to_sync.return_value = Mock()

        user_identifier = 'user_123'
        chatroom_uuid = str(uuid.uuid4())
        has_unread = False
        sender_identifier = 'user_456'

        broadcast_unread_update(user_identifier, chatroom_uuid, has_unread, sender_identifier)

        mock_async_to_sync.assert_called_once()


@pytest.mark.unit
class TestMarkReadForParticipant:
    @patch('core.services.unread.ChatroomParticipant')
    def test_mark_read_for_participant_success(self, mock_participant_class):
        mock_chatroom = Mock()
        mock_chatroom.uuid = uuid.uuid4()
        user_identifier = 'user_123'

        mock_queryset = Mock()
        mock_queryset.update.return_value = 1
        mock_participant_class.objects.filter.return_value = mock_queryset

        mark_read_for_participant(mock_chatroom, user_identifier)

        mock_participant_class.objects.filter.assert_called_once_with(
            chatroom=mock_chatroom,
            user_identifier=user_identifier
        )
        mock_queryset.update.assert_called_once_with(has_unread=False)

    @patch('core.services.unread.ChatroomParticipant')
    def test_mark_read_for_participant_not_found(self, mock_participant_class):
        mock_chatroom = Mock()
        mock_chatroom.uuid = uuid.uuid4()
        user_identifier = 'user_123'

        mock_queryset = Mock()
        mock_queryset.update.return_value = 0
        mock_participant_class.objects.filter.return_value = mock_queryset

        mark_read_for_participant(mock_chatroom, user_identifier)

        mock_participant_class.objects.filter.assert_called_once_with(
            chatroom=mock_chatroom,
            user_identifier=user_identifier
        )
        mock_queryset.update.assert_called_once_with(has_unread=False)

    @patch('core.services.unread.ChatroomParticipant')
    def test_mark_read_for_participant_multiple_updates(self, mock_participant_class):
        mock_chatroom = Mock()
        mock_chatroom.uuid = uuid.uuid4()
        user_identifier = 'user_123'

        mock_queryset = Mock()
        mock_queryset.update.return_value = 1
        mock_participant_class.objects.filter.return_value = mock_queryset

        mark_read_for_participant(mock_chatroom, user_identifier)
        mark_read_for_participant(mock_chatroom, user_identifier)

        assert mock_participant_class.objects.filter.call_count == 2
        assert mock_queryset.update.call_count == 2
