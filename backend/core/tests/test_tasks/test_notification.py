import pytest
from unittest.mock import Mock, patch
from requests.exceptions import RequestException

from core.tasks.notification import send_notification_task, NotificationType


@pytest.mark.unit
class TestSendNotificationTask:
    @patch('core.tasks.notification.requests.post')
    def test_send_notification_discord_success(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        channel_data = {
            'type': 'discord',
            'config': {
                'webhook_url': 'https://discord.com/api/webhooks/123',
                'username': 'Test Bot'
            }
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://discord.com/api/webhooks/123'
        assert call_args[1]['json']['content'] == 'Test message'
        assert call_args[1]['json']['username'] == 'Test Bot'

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_discord_webhook_url_not_configured(self, mock_post):
        channel_data = {
            'type': 'discord',
            'config': {}
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_post.assert_not_called()

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_discord_webhook_url_alternative_key(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        channel_data = {
            'type': 'discord',
            'config': {
                'webhookUrl': 'https://discord.com/api/webhooks/123'
            }
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == 'https://discord.com/api/webhooks/123'

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_discord_default_username(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        channel_data = {
            'type': 'discord',
            'config': {
                'webhook_url': 'https://discord.com/api/webhooks/123'
            }
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_post.assert_called_once()
        assert mock_post.call_args[1]['json']['username'] == 'Ch8r Bot'

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_discord_webhook_error(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_post.return_value = mock_response

        channel_data = {
            'type': 'discord',
            'config': {
                'webhook_url': 'https://discord.com/api/webhooks/123'
            }
        }
        message = 'Test message'

        with pytest.raises(Exception, match='Discord webhook returned 400: Bad Request'):
            send_notification_task(channel_data, message)

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_slack_success(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        channel_data = {
            'type': 'slack',
            'config': {
                'webhook_url': 'https://slack.com/api/webhooks/123',
                'username': 'Test Bot'
            }
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://slack.com/api/webhooks/123'
        assert call_args[1]['json']['text'] == 'Test message'
        assert call_args[1]['json']['username'] == 'Test Bot'

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_slack_webhook_url_not_configured(self, mock_post):
        channel_data = {
            'type': 'slack',
            'config': {}
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_post.assert_not_called()

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_slack_webhook_url_alternative_key(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_post.return_value = mock_response

        channel_data = {
            'type': 'slack',
            'config': {
                'webhookUrl': 'https://slack.com/api/webhooks/123'
            }
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == 'https://slack.com/api/webhooks/123'

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_slack_webhook_error(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        channel_data = {
            'type': 'slack',
            'config': {
                'webhook_url': 'https://slack.com/api/webhooks/123'
            }
        }
        message = 'Test message'

        with pytest.raises(Exception, match='Slack webhook returned 500: Internal Server Error'):
            send_notification_task(channel_data, message)

    @patch('core.tasks.notification.send_mail')
    @patch('core.tasks.notification.settings')
    def test_send_notification_email_success(self, mock_settings, mock_send_mail):
        mock_settings.DEFAULT_FROM_EMAIL = 'noreply@ch8r.com'

        channel_data = {
            'type': 'email',
            'config': {
                'email': 'test@example.com',
                'subject': 'Test Subject'
            }
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_send_mail.assert_called_once_with(
            'Test Subject',
            'Test message',
            'noreply@ch8r.com',
            ['test@example.com'],
            fail_silently=False
        )

    @patch('core.tasks.notification.send_mail')
    @patch('core.tasks.notification.settings')
    def test_send_notification_email_default_subject(self, mock_settings, mock_send_mail):
        mock_settings.DEFAULT_FROM_EMAIL = 'noreply@ch8r.com'

        channel_data = {
            'type': 'email',
            'config': {
                'email': 'test@example.com'
            }
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_send_mail.assert_called_once()
        assert mock_send_mail.call_args[0][0] == 'Notification from Ch8r'

    @patch('core.tasks.notification.send_mail')
    def test_send_notification_email_no_recipient(self, mock_send_mail):
        channel_data = {
            'type': 'email',
            'config': {}
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

        mock_send_mail.assert_not_called()

    def test_send_notification_whatsapp(self):
        channel_data = {
            'type': 'whatsapp',
            'config': {}
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

    def test_send_notification_unsupported_type(self):
        channel_data = {
            'type': 'unsupported',
            'config': {}
        }
        message = 'Test message'

        send_notification_task(channel_data, message)

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_request_exception(self, mock_post):
        mock_post.side_effect = RequestException('Network error')

        channel_data = {
            'type': 'discord',
            'config': {
                'webhook_url': 'https://discord.com/api/webhooks/123'
            }
        }
        message = 'Test message'

        with pytest.raises(RequestException, match='Network error'):
            send_notification_task(channel_data, message)

    @patch('core.tasks.notification.requests.post')
    def test_send_notification_general_exception(self, mock_post):
        mock_post.side_effect = Exception('General error')

        channel_data = {
            'type': 'discord',
            'config': {
                'webhook_url': 'https://discord.com/api/webhooks/123'
            }
        }
        message = 'Test message'

        with pytest.raises(Exception, match='General error'):
            send_notification_task(channel_data, message)

