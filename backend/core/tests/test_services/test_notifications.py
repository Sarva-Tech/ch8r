import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from core.services.notifications import (
    find_channels,
    notify_users
)


@pytest.mark.unit
class TestFindChannels:
    @patch('core.models.AppNotificationProfile')
    def test_find_channels_success(self, mock_app_profile_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        
        mock_notification_profile = Mock()
        mock_notification_profile.type = 'email'
        mock_notification_profile.config = {'email': 'test@example.com'}
        
        mock_app_profile = Mock()
        mock_app_profile.notification_profile = mock_notification_profile
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = [mock_app_profile]
        mock_app_profile_class.objects = mock_queryset
        
        result = find_channels(mock_app)
        
        assert len(result) == 1
        assert result[0] == mock_notification_profile

    @patch('core.models.AppNotificationProfile')
    def test_find_channels_multiple(self, mock_app_profile_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        
        mock_notification_profile1 = Mock()
        mock_notification_profile1.type = 'email'
        mock_notification_profile1.config = {'email': 'test@example.com'}
        
        mock_notification_profile2 = Mock()
        mock_notification_profile2.type = 'slack'
        mock_notification_profile2.config = {'webhook': 'https://slack.com/webhook'}
        
        mock_app_profile1 = Mock()
        mock_app_profile1.notification_profile = mock_notification_profile1
        
        mock_app_profile2 = Mock()
        mock_app_profile2.notification_profile = mock_notification_profile2
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = [mock_app_profile1, mock_app_profile2]
        mock_app_profile_class.objects = mock_queryset
        
        result = find_channels(mock_app)
        
        assert len(result) == 2
        assert result[0] == mock_notification_profile1
        assert result[1] == mock_notification_profile2

    @patch('core.models.AppNotificationProfile')
    def test_find_channels_empty(self, mock_app_profile_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = []
        mock_app_profile_class.objects = mock_queryset
        
        result = find_channels(mock_app)
        
        assert result == []

    @patch('core.models.AppNotificationProfile')
    def test_find_channels_select_related_filter(self, mock_app_profile_class):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        
        mock_notification_profile = Mock()
        mock_app_profile = Mock()
        mock_app_profile.notification_profile = mock_notification_profile
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = [mock_app_profile]
        mock_app_profile_class.objects = mock_queryset
        
        find_channels(mock_app)
        
        mock_queryset.select_related.assert_called_once_with("notification_profile")
        mock_queryset.select_related.return_value.filter.assert_called_once_with(application=mock_app)


@pytest.mark.unit
class TestNotifyUsers:
    @patch('core.services.notifications.send_notification_task')
    @patch('core.services.notifications.find_channels')
    @patch('core.services.notifications.render_template')
    def test_notify_users_success(self, mock_render_template, mock_find_channels, mock_send_task):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        
        mock_channel = Mock()
        mock_channel.type = 'email'
        mock_channel.config = {'email': 'test@example.com'}
        mock_find_channels.return_value = [mock_channel]
        
        mock_render_template.return_value = 'Rendered message'
        
        mock_send_task.delay = Mock()
        
        notify_users(mock_app, 'template_str', {'key': 'value'})
        
        mock_render_template.assert_called_once_with('template_str', {'key': 'value'})
        mock_find_channels.assert_called_once_with(mock_app)
        mock_send_task.delay.assert_called_once()

    @patch('core.services.notifications.send_notification_task')
    @patch('core.services.notifications.find_channels')
    @patch('core.services.notifications.render_template')
    def test_notify_users_multiple_channels(self, mock_render_template, mock_find_channels, mock_send_task):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        
        mock_channel1 = Mock()
        mock_channel1.type = 'email'
        mock_channel1.config = {'email': 'test@example.com'}
        
        mock_channel2 = Mock()
        mock_channel2.type = 'slack'
        mock_channel2.config = {'webhook': 'https://slack.com/webhook'}
        
        mock_find_channels.return_value = [mock_channel1, mock_channel2]
        
        mock_render_template.return_value = 'Rendered message'
        
        mock_send_task.delay = Mock()
        
        notify_users(mock_app, 'template_str', {'key': 'value'})
        
        assert mock_send_task.delay.call_count == 2

    @patch('core.services.notifications.find_channels')
    @patch('core.services.notifications.render_template')
    def test_notify_users_no_channels(self, mock_render_template, mock_find_channels, capsys):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        
        mock_find_channels.return_value = []
        
        mock_render_template.return_value = 'Rendered message'
        
        notify_users(mock_app, 'template_str', {'key': 'value'})
        
        captured = capsys.readouterr()
        assert 'No notification channels found' in captured.out
        mock_render_template.assert_called_once_with('template_str', {'key': 'value'})

    @patch('core.services.notifications.send_notification_task')
    @patch('core.services.notifications.find_channels')
    @patch('core.services.notifications.render_template')
    def test_notify_users_channel_data_format(self, mock_render_template, mock_find_channels, mock_send_task):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        
        mock_channel = Mock()
        mock_channel.type = 'email'
        mock_channel.config = {'email': 'test@example.com'}
        mock_find_channels.return_value = [mock_channel]
        
        mock_render_template.return_value = 'Rendered message'
        
        mock_send_task.delay = Mock()
        
        notify_users(mock_app, 'template_str', {'key': 'value'})
        
        expected_channel_data = {
            'type': 'email',
            'config': {'email': 'test@example.com'}
        }
        mock_send_task.delay.assert_called_once_with(expected_channel_data, 'Rendered message')

    @patch('core.services.notifications.send_notification_task')
    @patch('core.services.notifications.find_channels')
    @patch('core.services.notifications.render_template')
    def test_notify_users_with_context(self, mock_render_template, mock_find_channels, mock_send_task):
        mock_app = Mock()
        mock_app.uuid = uuid.uuid4()
        
        mock_channel = Mock()
        mock_channel.type = 'slack'
        mock_channel.config = {'webhook': 'https://slack.com/webhook'}
        mock_find_channels.return_value = [mock_channel]
        
        mock_render_template.return_value = 'Rendered message with context'
        
        mock_send_task.delay = Mock()
        
        context = {
            'user_name': 'John',
            'action': 'created'
        }
        
        notify_users(mock_app, 'user_action_template', context)
        
        mock_render_template.assert_called_once_with('user_action_template', context)
        mock_send_task.delay.assert_called_once()
