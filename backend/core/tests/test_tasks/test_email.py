import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from core.tasks.email import send_verification_email_task, send_discord_notification_task


@pytest.mark.unit
class TestSendVerificationEmailTask:
    @patch('core.tasks.email.TemplateLoader')
    @patch('core.tasks.email.MailerSendClient')
    @patch('core.tasks.email.settings')
    def test_send_verification_email_success(self, mock_settings, mock_ms_client_class, mock_template_loader):
        mock_settings.FRONTEND_URL = 'https://example.com'
        mock_settings.MAILERSEND_API_KEY = 'test_api_key'
        mock_settings.DEFAULT_FROM_EMAIL = 'noreply@example.com'
        
        mock_template_loader.render_template.return_value = 'rendered content'
        
        mock_ms_client = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.id = 'email_id_123'
        mock_response.status_code = 200
        mock_ms_client.emails.send.return_value = mock_response
        mock_ms_client_class.return_value = mock_ms_client
        
        mock_email_builder = Mock()
        mock_email_builder_instance = Mock()
        mock_email_builder_instance.from_email.return_value = mock_email_builder_instance
        mock_email_builder_instance.to_many.return_value = mock_email_builder_instance
        mock_email_builder_instance.subject.return_value = mock_email_builder_instance
        mock_email_builder_instance.text.return_value = mock_email_builder_instance
        mock_email_builder_instance.html.return_value = mock_email_builder_instance
        mock_email_builder_instance.build.return_value = mock_email_builder_instance
        mock_email_builder.return_value = mock_email_builder_instance
        
        with patch('core.tasks.email.EmailBuilder', return_value=mock_email_builder):
            send_verification_email_task(1, 'test@example.com', 'testuser', 'token123', 'VERIFY_EMAIL')
        
        mock_template_loader.render_template.assert_called()
        mock_ms_client.emails.send.assert_called_once()

    @patch('core.tasks.email.TemplateLoader')
    @patch('core.tasks.email.MailerSendClient')
    @patch('core.tasks.email.settings')
    def test_send_reset_password_email_success(self, mock_settings, mock_ms_client_class, mock_template_loader):
        mock_settings.FRONTEND_URL = 'https://example.com'
        mock_settings.MAILERSEND_API_KEY = 'test_api_key'
        mock_settings.DEFAULT_FROM_EMAIL = 'noreply@example.com'
        
        mock_template_loader.render_template.return_value = 'rendered content'
        
        mock_ms_client = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.id = 'email_id_123'
        mock_response.status_code = 200
        mock_ms_client.emails.send.return_value = mock_response
        mock_ms_client_class.return_value = mock_ms_client
        
        mock_email_builder = Mock()
        mock_email_builder_instance = Mock()
        mock_email_builder_instance.from_email.return_value = mock_email_builder_instance
        mock_email_builder_instance.to_many.return_value = mock_email_builder_instance
        mock_email_builder_instance.subject.return_value = mock_email_builder_instance
        mock_email_builder_instance.text.return_value = mock_email_builder_instance
        mock_email_builder_instance.html.return_value = mock_email_builder_instance
        mock_email_builder_instance.build.return_value = mock_email_builder_instance
        mock_email_builder.return_value = mock_email_builder_instance
        
        with patch('core.tasks.email.EmailBuilder', return_value=mock_email_builder):
            send_verification_email_task(1, 'test@example.com', 'testuser', 'token123', 'RESET_PASSWORD')
        
        mock_template_loader.render_template.assert_called()

    @patch('core.tasks.email.TemplateLoader')
    @patch('core.tasks.email.MailerSendClient')
    @patch('core.tasks.email.settings')
    def test_send_verification_email_invalid_purpose(self, mock_settings, mock_ms_client_class, mock_template_loader):
        mock_settings.FRONTEND_URL = 'https://example.com'
        
        with pytest.raises(ValueError, match="Invalid email purpose"):
            send_verification_email_task(1, 'test@example.com', 'testuser', 'token123', 'INVALID_PURPOSE')

    @patch('core.tasks.email.TemplateLoader')
    @patch('core.tasks.email.MailerSendClient')
    @patch('core.tasks.email.settings')
    def test_send_verification_email_retry_on_failure(self, mock_settings, mock_ms_client_class, mock_template_loader):
        mock_settings.FRONTEND_URL = 'https://example.com'
        mock_settings.MAILERSEND_API_KEY = 'test_api_key'
        mock_settings.DEFAULT_FROM_EMAIL = 'noreply@example.com'
        
        mock_template_loader.render_template.return_value = 'rendered content'
        
        mock_ms_client = Mock()
        mock_response = Mock()
        mock_response.success = False
        mock_response.data = 'error_data'
        mock_ms_client.emails.send.return_value = mock_response
        mock_ms_client_class.return_value = mock_ms_client
        
        mock_email_builder = Mock()
        mock_email_builder_instance = Mock()
        mock_email_builder_instance.from_email.return_value = mock_email_builder_instance
        mock_email_builder_instance.to_many.return_value = mock_email_builder_instance
        mock_email_builder_instance.subject.return_value = mock_email_builder_instance
        mock_email_builder_instance.text.return_value = mock_email_builder_instance
        mock_email_builder_instance.html.return_value = mock_email_builder_instance
        mock_email_builder_instance.build.return_value = mock_email_builder_instance
        mock_email_builder.return_value = mock_email_builder_instance
        
        with patch.object(send_verification_email_task, 'retry', side_effect=Exception('Retry')) as mock_retry:
            with patch('core.tasks.email.EmailBuilder', return_value=mock_email_builder):
                with pytest.raises(Exception):
                    send_verification_email_task(1, 'test@example.com', 'testuser', 'token123', 'VERIFY_EMAIL')
            
            assert mock_retry.call_count >= 1

    @patch('core.tasks.email.TemplateLoader')
    @patch('core.tasks.email.MailerSendClient')
    @patch('core.tasks.email.settings')
    def test_send_verification_email_rate_limit_retry(self, mock_settings, mock_ms_client_class, mock_template_loader):
        mock_settings.FRONTEND_URL = 'https://example.com'
        mock_settings.MAILERSEND_API_KEY = 'test_api_key'
        mock_settings.DEFAULT_FROM_EMAIL = 'noreply@example.com'
        
        mock_template_loader.render_template.return_value = 'rendered content'
        
        mock_ms_client = Mock()
        mock_response = Mock()
        mock_response.success = True
        mock_response.status_code = 429
        mock_response.retry_after = 30
        mock_ms_client.emails.send.return_value = mock_response
        mock_ms_client_class.return_value = mock_ms_client
        
        mock_email_builder = Mock()
        mock_email_builder_instance = Mock()
        mock_email_builder_instance.from_email.return_value = mock_email_builder_instance
        mock_email_builder_instance.to_many.return_value = mock_email_builder_instance
        mock_email_builder_instance.subject.return_value = mock_email_builder_instance
        mock_email_builder_instance.text.return_value = mock_email_builder_instance
        mock_email_builder_instance.html.return_value = mock_email_builder_instance
        mock_email_builder_instance.build.return_value = mock_email_builder_instance
        mock_email_builder.return_value = mock_email_builder_instance
        
        with patch.object(send_verification_email_task, 'retry', side_effect=Exception('Retry')) as mock_retry:
            with patch('core.tasks.email.EmailBuilder', return_value=mock_email_builder):
                with pytest.raises(Exception):
                    send_verification_email_task(1, 'test@example.com', 'testuser', 'token123', 'VERIFY_EMAIL')
            
            assert mock_retry.call_count >= 1


@pytest.mark.unit
class TestSendDiscordNotificationTask:
    @patch('core.tasks.email.settings')
    @patch('core.tasks.email.requests')
    def test_send_discord_notification_success(self, mock_requests, mock_settings):
        mock_settings.DISCORD_SIGNUP_WEBHOOK_URL = 'https://discord.com/api/webhook/test'
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response
        
        send_discord_notification_task('Test message')
        
        mock_requests.post.assert_called_once_with(
            'https://discord.com/api/webhook/test',
            json={'content': 'Test message'}
        )

    @patch('core.tasks.email.settings')
    @patch('core.tasks.email.requests')
    def test_send_discord_notification_no_webhook_url(self, mock_requests, mock_settings):
        mock_settings.DISCORD_SIGNUP_WEBHOOK_URL = None
        
        send_discord_notification_task('Test message')
        
        mock_requests.post.assert_not_called()

