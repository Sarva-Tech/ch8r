import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from core.services.escalation_service import EscalationService


@pytest.mark.unit
class TestEscalationServiceShouldEscalate:
    def test_should_escalate_user_requested_escalation(self):
        from core.agent_response_schema import ResponseStatus
        
        service = EscalationService()
        chatroom = Mock()
        agent_response = Mock()
        agent_response.status = ResponseStatus.USER_REQUESTED_ESCALATION
        
        result = service.should_escalate(chatroom, agent_response, 80)
        
        assert result is True

    def test_should_escalate_score_above_threshold_not_escalated(self):
        service = EscalationService()
        chatroom = Mock()
        chatroom.is_escalated = False
        agent_response = Mock()
        agent_response.escalation_score = 85
        agent_response.status = Mock()
        
        result = service.should_escalate(chatroom, agent_response, 80)
        
        assert result is True

    def test_should_escalate_score_above_threshold_escalated_not_in_cooldown(self):
        service = EscalationService()
        chatroom = Mock()
        chatroom.is_escalated = True
        chatroom.escalated_at = datetime.now(timezone.utc) - timedelta(hours=25)
        chatroom.escalation_cooldown_hours = 24
        agent_response = Mock()
        agent_response.escalation_score = 85
        agent_response.status = Mock()
        
        with patch.object(service, '_within_cooldown', return_value=False):
            result = service.should_escalate(chatroom, agent_response, 80)
        
        assert result is True

    def test_should_escalate_score_above_threshold_escalated_in_cooldown(self):
        service = EscalationService()
        chatroom = Mock()
        chatroom.is_escalated = True
        chatroom.escalated_at = datetime.now(timezone.utc) - timedelta(hours=1)
        chatroom.escalation_cooldown_hours = 24
        agent_response = Mock()
        agent_response.escalation_score = 85
        agent_response.status = Mock()
        
        with patch.object(service, '_within_cooldown', return_value=True):
            result = service.should_escalate(chatroom, agent_response, 80)
        
        assert result is False

    def test_should_escalate_score_below_threshold(self):
        service = EscalationService()
        chatroom = Mock()
        agent_response = Mock()
        agent_response.escalation_score = 70
        agent_response.status = Mock()
        
        result = service.should_escalate(chatroom, agent_response, 80)
        
        assert result is False

    def test_should_escalate_score_equals_threshold(self):
        service = EscalationService()
        chatroom = Mock()
        chatroom.is_escalated = False
        agent_response = Mock()
        agent_response.escalation_score = 80
        agent_response.status = Mock()
        
        result = service.should_escalate(chatroom, agent_response, 80)
        
        assert result is True


@pytest.mark.unit
class TestEscalationServiceEscalate:
    @patch('core.services.escalation_service.AppNotificationProfile')
    @patch('core.services.escalation_service.send_notification_task')
    def test_escalate_success(self, mock_send_task, mock_app_profile):
        service = EscalationService()
        
        chatroom = Mock()
        chatroom.name = 'test-chatroom'
        chatroom.is_escalated = False
        chatroom.escalated_at = None
        
        application = Mock()
        application.name = 'test-app'
        
        agent_response = Mock()
        agent_response.reason_for_escalation = 'Complex issue'
        agent_response.status = 'FAILED'
        agent_response.answer = 'This is the agent answer'
        
        user_message = Mock()
        user_message.message = 'Help me please'
        user_message.platform = 'slack'
        
        mock_profile = Mock()
        mock_profile.name = 'test-profile'
        mock_profile.type = 'email'
        mock_profile.config = {'email': 'test@example.com'}
        
        mock_app_profile_instance = Mock()
        mock_app_profile_instance.notification_profile = mock_profile
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = [mock_app_profile_instance]
        mock_app_profile.objects = mock_queryset
        
        result = service.escalate(chatroom, application, agent_response, user_message)
        
        assert chatroom.is_escalated is True
        assert chatroom.escalated_at is not None
        chatroom.save.assert_called_once_with(update_fields=["is_escalated", "escalated_at"])
        assert result['escalation_reason'] == 'Complex issue'
        assert len(result['notified_profiles']) == 1
        assert result['notified_profiles'][0]['name'] == 'test-profile'
        mock_send_task.delay.assert_called_once()

    @patch('core.services.escalation_service.AppNotificationProfile')
    @patch('core.services.escalation_service.send_notification_task')
    def test_escalate_without_user_message(self, mock_send_task, mock_app_profile):
        service = EscalationService()
        
        chatroom = Mock()
        chatroom.name = 'test-chatroom'
        chatroom.is_escalated = False
        chatroom.escalated_at = None
        
        application = Mock()
        application.name = 'test-app'
        
        agent_response = Mock()
        agent_response.reason_for_escalation = None
        agent_response.status = 'ESCALATED'
        agent_response.answer = 'Agent response'
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = []
        mock_app_profile.objects = mock_queryset
        
        result = service.escalate(chatroom, application, agent_response, None)
        
        assert chatroom.is_escalated is True
        assert result['escalation_reason'] == 'ESCALATED'
        assert result['notified_profiles'] == []

    @patch('core.services.escalation_service.AppNotificationProfile')
    @patch('core.services.escalation_service.send_notification_task')
    def test_escalate_agent_answer_truncated(self, mock_send_task, mock_app_profile):
        service = EscalationService()
        
        chatroom = Mock()
        chatroom.name = 'test-chatroom'
        chatroom.is_escalated = False
        
        application = Mock()
        application.name = 'test-app'
        
        agent_response = Mock()
        agent_response.reason_for_escalation = 'Test reason'
        agent_response.status = 'FAILED'
        agent_response.answer = 'a' * 400  # Long answer
        
        user_message = Mock()
        user_message.message = 'Test message'
        user_message.platform = 'slack'
        
        mock_profile = Mock()
        mock_profile.name = 'test-profile'
        mock_profile.type = 'email'
        mock_profile.config = {}
        
        mock_app_profile_instance = Mock()
        mock_app_profile_instance.notification_profile = mock_profile
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = [mock_app_profile_instance]
        mock_app_profile.objects = mock_queryset
        
        result = service.escalate(chatroom, application, agent_response, user_message)
        
        assert result['escalation_reason'] == 'Test reason'

    @patch('core.services.escalation_service.AppNotificationProfile')
    @patch('core.services.escalation_service.send_notification_task')
    def test_escalate_multiple_notification_profiles(self, mock_send_task, mock_app_profile):
        service = EscalationService()
        
        chatroom = Mock()
        chatroom.name = 'test-chatroom'
        chatroom.is_escalated = False
        
        application = Mock()
        application.name = 'test-app'
        
        agent_response = Mock()
        agent_response.reason_for_escalation = 'Test'
        agent_response.status = 'FAILED'
        agent_response.answer = 'Answer'
        
        user_message = Mock()
        user_message.message = 'Message'
        user_message.platform = 'slack'
        
        mock_profile1 = Mock()
        mock_profile1.name = 'profile1'
        mock_profile1.type = 'email'
        mock_profile1.config = {}
        
        mock_profile2 = Mock()
        mock_profile2.name = 'profile2'
        mock_profile2.type = 'slack'
        mock_profile2.config = {}
        
        mock_app_profile_instance1 = Mock()
        mock_app_profile_instance1.notification_profile = mock_profile1
        
        mock_app_profile_instance2 = Mock()
        mock_app_profile_instance2.notification_profile = mock_profile2
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = [
            mock_app_profile_instance1, mock_app_profile_instance2
        ]
        mock_app_profile.objects = mock_queryset
        
        result = service.escalate(chatroom, application, agent_response, user_message)
        
        assert len(result['notified_profiles']) == 2
        assert mock_send_task.delay.call_count == 2

    @patch('core.services.escalation_service.AppNotificationProfile')
    @patch('core.services.escalation_service.send_notification_task')
    def test_escalate_notification_error_handling(self, mock_send_task, mock_app_profile):
        service = EscalationService()
        
        chatroom = Mock()
        chatroom.name = 'test-chatroom'
        chatroom.is_escalated = False
        
        application = Mock()
        application.name = 'test-app'
        
        agent_response = Mock()
        agent_response.reason_for_escalation = 'Test'
        agent_response.status = 'FAILED'
        agent_response.answer = 'Answer'
        
        user_message = Mock()
        user_message.message = 'Message'
        user_message.platform = 'slack'
        
        mock_profile = Mock()
        mock_profile.name = 'failing-profile'
        mock_profile.type = 'email'
        mock_profile.config = {}
        
        mock_app_profile_instance = Mock()
        mock_app_profile_instance.notification_profile = mock_profile
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = [mock_app_profile_instance]
        mock_app_profile.objects = mock_queryset
        
        mock_send_task.delay.side_effect = Exception('Notification failed')
        
        result = service.escalate(chatroom, application, agent_response, user_message)
        
        assert result['escalation_reason'] == 'Test'
        assert result['notified_profiles'] == []

    @patch('core.services.escalation_service.AppNotificationProfile')
    @patch('core.services.escalation_service.send_notification_task')
    def test_escalate_agent_without_answer(self, mock_send_task, mock_app_profile):
        service = EscalationService()
        
        chatroom = Mock()
        chatroom.name = 'test-chatroom'
        chatroom.is_escalated = False
        
        application = Mock()
        application.name = 'test-app'
        
        agent_response = Mock()
        agent_response.reason_for_escalation = 'Test'
        agent_response.status = 'FAILED'
        del agent_response.answer  # Simulate missing answer attribute
        
        user_message = Mock()
        user_message.message = 'Message'
        user_message.platform = 'slack'
        
        mock_queryset = Mock()
        mock_queryset.select_related.return_value.filter.return_value = []
        mock_app_profile.objects = mock_queryset
        
        result = service.escalate(chatroom, application, agent_response, user_message)
        
        assert result['escalation_reason'] == 'Test'
        assert result['notified_profiles'] == []


@pytest.mark.unit
class TestEscalationServiceWithinCooldown:
    def test_within_cooldown_no_escalation_time(self):
        service = EscalationService()
        chatroom = Mock()
        chatroom.escalated_at = None
        chatroom.escalation_cooldown_hours = 24
        
        result = service._within_cooldown(chatroom)
        
        assert result is False

    def test_within_cooldown_true(self):
        service = EscalationService()
        chatroom = Mock()
        chatroom.escalated_at = datetime.now(timezone.utc) - timedelta(hours=1)
        chatroom.escalation_cooldown_hours = 24
        
        result = service._within_cooldown(chatroom)
        
        assert result is True

    def test_within_cooldown_false(self):
        service = EscalationService()
        chatroom = Mock()
        chatroom.escalated_at = datetime.now(timezone.utc) - timedelta(hours=25)
        chatroom.escalation_cooldown_hours = 24
        
        result = service._within_cooldown(chatroom)
        
        assert result is False

    def test_within_cooldown_exactly_at_threshold(self):
        service = EscalationService()
        chatroom = Mock()
        chatroom.escalated_at = datetime.now(timezone.utc) - timedelta(hours=24)
        chatroom.escalation_cooldown_hours = 24
        
        result = service._within_cooldown(chatroom)
        
        assert result is False

    def test_within_cooldown_naive_datetime(self):
        service = EscalationService()
        chatroom = Mock()
        naive_time = datetime.now() - timedelta(hours=1)
        chatroom.escalated_at = naive_time.replace(tzinfo=None)
        chatroom.escalation_cooldown_hours = 24
        
        result = service._within_cooldown(chatroom)
        
        assert result is True

    def test_within_cooldown_zero_cooldown(self):
        service = EscalationService()
        chatroom = Mock()
        chatroom.escalated_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        chatroom.escalation_cooldown_hours = 0
        
        result = service._within_cooldown(chatroom)
        
        assert result is False
