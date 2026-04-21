import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from core.tasks.message import _send_live_update, _send_live_update_to_dashboard, _build_usage_meta, generate_bot_response


@pytest.mark.unit
class TestSendLiveUpdate:
    @patch('core.tasks.message.get_channel_layer')
    @patch('core.tasks.message.async_to_sync')
    @patch('core.tasks.message.ViewMessageSerializer')
    def test_send_live_update_success(self, mock_serializer, mock_async_to_sync, mock_get_channel_layer):
        mock_bot_message = Mock()
        mock_bot_message.id = 1

        mock_user_message = Mock()
        mock_user_message.chatroom.participants.filter.return_value.exclude.return_value.values_list.return_value = ['widget_user1', 'dashboard_user2']

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        mock_serializer.return_value.data = {'id': 1, 'message': 'test'}

        def mock_async_to_sync_func(func):
            return func
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        _send_live_update(mock_bot_message, mock_user_message)

        mock_channel_layer.group_send.assert_called()

    @patch('core.tasks.message.get_channel_layer')
    @patch('core.tasks.message.async_to_sync')
    @patch('core.tasks.message.ViewMessageSerializer')
    def test_send_live_update_no_participants(self, mock_serializer, mock_async_to_sync, mock_get_channel_layer):
        mock_bot_message = Mock()
        mock_bot_message.id = 1

        mock_user_message = Mock()
        mock_user_message.chatroom.participants.filter.return_value.exclude.return_value.values_list.return_value = []

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        _send_live_update(mock_bot_message, mock_user_message)

        mock_channel_layer.group_send.assert_not_called()

    @patch('core.tasks.message.get_channel_layer')
    @patch('core.tasks.message.async_to_sync')
    @patch('core.tasks.message.ViewMessageSerializer')
    def test_send_live_update_exception(self, mock_serializer, mock_async_to_sync, mock_get_channel_layer):
        mock_bot_message = Mock()
        mock_bot_message.id = 1

        mock_user_message = Mock()
        mock_user_message.chatroom.participants.filter.return_value.exclude.return_value.values_list.return_value = ['widget_user1']

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        mock_serializer.return_value.data = {'id': 1, 'message': 'test'}

        def mock_async_to_sync_func(func):
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                raise Exception('WebSocket error')
            return wrapper
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        _send_live_update(mock_bot_message, mock_user_message)

        mock_channel_layer.group_send.assert_called_once()


@pytest.mark.unit
class TestSendLiveUpdateToDashboard:
    @patch('core.tasks.message.get_channel_layer')
    @patch('core.tasks.message.async_to_sync')
    @patch('core.tasks.message.ViewMessageSerializer')
    def test_send_live_update_to_dashboard_success(self, mock_serializer, mock_async_to_sync, mock_get_channel_layer):
        mock_message = Mock()
        mock_message.id = 1

        mock_user_message = Mock()
        mock_user_message.chatroom.participants.filter.return_value.exclude.return_value.values_list.return_value = ['dashboard_user1']

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        mock_serializer.return_value.data = {'id': 1, 'message': 'test'}

        def mock_async_to_sync_func(func):
            return func
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        _send_live_update_to_dashboard(mock_message, mock_user_message)

        mock_channel_layer.group_send.assert_called_once()

    @patch('core.tasks.message.get_channel_layer')
    @patch('core.tasks.message.async_to_sync')
    @patch('core.tasks.message.ViewMessageSerializer')
    def test_send_live_update_to_dashboard_exception(self, mock_serializer, mock_async_to_sync, mock_get_channel_layer):
        mock_message = Mock()
        mock_message.id = 1

        mock_user_message = Mock()
        mock_user_message.chatroom.participants.filter.return_value.exclude.return_value.values_list.return_value = ['dashboard_user1']

        mock_channel_layer = Mock()
        mock_get_channel_layer.return_value = mock_channel_layer

        mock_serializer.return_value.data = {'id': 1, 'message': 'test'}

        def mock_async_to_sync_func(func):
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                raise Exception('WebSocket error')
            return wrapper
        mock_async_to_sync.side_effect = mock_async_to_sync_func

        _send_live_update_to_dashboard(mock_message, mock_user_message)

        mock_channel_layer.group_send.assert_called_once()


@pytest.mark.unit
class TestBuildUsageMeta:
    def test_build_usage_meta_with_data(self):
        usage = {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}
        result = _build_usage_meta(usage)

        assert result == {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150}

    def test_build_usage_meta_none_values(self):
        usage = {'prompt_tokens': 100, 'completion_tokens': None, 'total_tokens': 150}
        result = _build_usage_meta(usage)

        assert result == {'prompt_tokens': 100, 'total_tokens': 150}

    def test_build_usage_meta_empty(self):
        usage = {}
        result = _build_usage_meta(usage)

        assert result == {}

    def test_build_usage_meta_none(self):
        usage = None
        result = _build_usage_meta(usage)

        assert result == {}


@pytest.mark.unit
class TestGenerateBotResponse:
    @patch('core.tasks.message._send_live_update')
    @patch('core.tasks.message.AIClientService')
    @patch('core.tasks.message.Application')
    @patch('core.tasks.message.Message')
    def test_generate_bot_response_no_ai_provider(self, mock_message_class, mock_app_class, mock_ai_client_service, mock_send_live_update):
        mock_app = Mock()
        mock_app.uuid = 'app-uuid'
        mock_app_class.objects.get.return_value = mock_app

        mock_user_message = Mock()
        mock_user_message.id = 1
        mock_user_message.chatroom = Mock()
        mock_user_message.message = 'test question'
        mock_user_message.platform = 'widget'
        mock_user_message.is_internal = False
        mock_message_class.objects.get.return_value = mock_user_message

        mock_ai_client_instance = Mock()
        mock_ai_client_instance.get_client_and_model.return_value = (None, None)
        mock_ai_client_service.return_value = mock_ai_client_instance

        mock_bot_message = Mock()
        mock_bot_message.id = 2
        mock_message_class.objects.create.return_value = mock_bot_message

        generate_bot_response(1, 'app-uuid')

        mock_message_class.objects.create.assert_called_once()
        mock_send_live_update.assert_called_once_with(mock_bot_message, mock_user_message)

    @patch('core.tasks.message._send_live_update')
    @patch('core.tasks.message._send_live_update_to_dashboard')
    @patch('core.tasks.message.EscalationService')
    @patch('core.tasks.message.ToolCallExecutor')
    @patch('core.tasks.message.TemplateLoader')
    @patch('core.tasks.message.get_chunks')
    @patch('core.tasks.message.get_enabled_tools_for_app')
    @patch('core.tasks.message.IngestedChunk')
    @patch('core.tasks.message.AIClientService')
    @patch('core.tasks.message.Application')
    @patch('core.tasks.message.Message')
    @patch('core.tasks.message.messages_to_llm_conversation')
    @patch('core.tasks.message.add_instructions_to_convo')
    @patch('core.tasks.message.add_kb_to_convo')
    @patch('core.models.AppIntegration')
    @patch('core.models.ToolConfig')
    def test_generate_bot_response_success_no_tools(self, mock_tool_config, mock_app_integration, mock_add_kb, mock_add_instructions, mock_messages_to_llm, mock_message_class, mock_app_class, mock_ai_client_service, mock_ingested_chunk, mock_get_tools, mock_get_chunks, mock_template_loader, mock_executor_class, mock_escalation_service, mock_send_dashboard, mock_send_live):
        mock_app = Mock()
        mock_app.uuid = 'app-uuid'
        mock_app.get_prompt_config.return_value = {
            'tone': 'professional',
            'response_style': 'concise',
            'custom_instructions': 'Be helpful',
            'role': 'assistant',
            'behavior': 'friendly'
        }
        mock_app.name = 'Test App'
        mock_app_class.objects.get.return_value = mock_app

        mock_user_message = Mock()
        mock_user_message.id = 1
        mock_user_message.chatroom = Mock()
        mock_user_message.message = 'test question'
        mock_user_message.platform = 'widget'
        mock_user_message.is_internal = False
        mock_user_message.metadata = {}
        mock_message_class.objects.get.return_value = mock_user_message

        mock_ai_client_instance = Mock()
        mock_provider = Mock()
        mock_agent_response = Mock()
        mock_agent_response.answer = 'test answer'
        mock_agent_response.status = 'SUCCESS'
        mock_agent_response.escalation = False
        mock_agent_response.reason_for_escalation = ''
        mock_agent_response.sentiment_score = 80
        mock_agent_response.escalation_score = 10
        mock_agent_response.criticality_score = 5
        mock_provider.generate_with_conversation.return_value = (mock_agent_response, None, {'prompt_tokens': 100})
        mock_ai_client_instance.get_client_and_model.return_value = (mock_provider, 'gpt-4')
        mock_ai_client_service.return_value = mock_ai_client_instance

        mock_ingested_chunk.objects.filter.return_value.exists.return_value = False
        mock_get_tools.return_value = None
        mock_get_chunks.return_value = []
        mock_template_loader.render_template.return_value = 'system instruction'

        mock_tool_config.objects.filter.return_value.values_list.return_value.distinct.return_value = []
        mock_app_integration.objects.filter.return_value.select_related.return_value = []

        mock_messages_qs = Mock()
        mock_messages_qs.count.return_value = 1
        mock_message_class.objects.filter.return_value.order_by.return_value = mock_messages_qs

        mock_messages_to_llm.side_effect = lambda *args, **kwargs: []
        mock_add_instructions.side_effect = lambda *args, **kwargs: []
        mock_add_kb.side_effect = lambda *args, **kwargs: []

        mock_bot_message = Mock()
        mock_bot_message.id = 2
        mock_message_class.objects.create.return_value = mock_bot_message

        mock_escalation_instance = Mock()
        mock_escalation_instance.should_escalate.return_value = False
        mock_escalation_service.return_value = mock_escalation_instance

        generate_bot_response(1, 'app-uuid')

        mock_send_live.assert_called_once()

    @patch('core.tasks.message._send_live_update')
    @patch('core.tasks.message._send_live_update_to_dashboard')
    @patch('core.tasks.message.EscalationService')
    @patch('core.tasks.message.ToolCallExecutor')
    @patch('core.tasks.message.TemplateLoader')
    @patch('core.tasks.message.get_chunks')
    @patch('core.tasks.message.get_enabled_tools_for_app')
    @patch('core.tasks.message.IngestedChunk')
    @patch('core.tasks.message.AIClientService')
    @patch('core.tasks.message.Application')
    @patch('core.tasks.message.Message')
    @patch('core.tasks.message.messages_to_llm_conversation')
    @patch('core.tasks.message.add_instructions_to_convo')
    @patch('core.tasks.message.add_kb_to_convo')
    @patch('core.models.AppIntegration')
    @patch('core.models.ToolConfig')
    def test_generate_bot_response_pipeline_error(self, mock_tool_config, mock_app_integration, mock_add_kb, mock_add_instructions, mock_messages_to_llm, mock_message_class, mock_app_class, mock_ai_client_service, mock_ingested_chunk, mock_get_tools, mock_get_chunks, mock_template_loader, mock_executor_class, mock_escalation_service, mock_send_dashboard, mock_send_live):
        mock_app = Mock()
        mock_app.uuid = 'app-uuid'
        mock_app.get_prompt_config.return_value = {
            'tone': 'professional',
            'response_style': 'concise',
            'custom_instructions': 'Be helpful',
            'role': 'assistant',
            'behavior': 'friendly'
        }
        mock_app.name = 'Test App'
        mock_app_class.objects.get.return_value = mock_app

        mock_user_message = Mock()
        mock_user_message.id = 1
        mock_user_message.chatroom = Mock()
        mock_user_message.message = 'test question'
        mock_user_message.platform = 'widget'
        mock_user_message.is_internal = False
        mock_message_class.objects.get.return_value = mock_user_message

        mock_ai_client_instance = Mock()
        mock_provider = Mock()
        mock_agent_response = Mock()
        mock_agent_response.status = 'SUCCESS'
        mock_agent_response.sentiment_score = 80
        mock_agent_response.escalation_score = 10
        mock_agent_response.criticality_score = 5
        mock_tool_calls = [{'name': 'test_tool', 'args': {}}]
        mock_provider.generate_with_conversation.return_value = ('Thinking...', mock_tool_calls, {'prompt_tokens': 100})
        mock_ai_client_instance.get_client_and_model.return_value = (mock_provider, 'gpt-4')
        mock_ai_client_service.return_value = mock_ai_client_instance

        mock_ingested_chunk.objects.filter.return_value.exists.return_value = False
        mock_get_tools.return_value = None
        mock_get_chunks.return_value = []
        mock_template_loader.render_template.return_value = 'system instruction'

        mock_tool_config.objects.filter.return_value.values_list.return_value.distinct.return_value = []
        mock_app_integration.objects.filter.return_value.select_related.return_value = []

        mock_messages_qs = Mock()
        mock_messages_qs.count.return_value = 1
        mock_message_class.objects.filter.return_value.order_by.return_value = mock_messages_qs

        mock_messages_to_llm.side_effect = lambda *args, **kwargs: []
        mock_add_instructions.side_effect = lambda *args, **kwargs: []
        mock_add_kb.side_effect = lambda *args, **kwargs: []

        mock_executor_instance = Mock()
        mock_executor_instance.execute_all.return_value = ([], [])
        mock_executor_class.return_value = mock_executor_instance
        mock_executor_instance.execute_all.side_effect = Exception('Pipeline error')

        mock_bot_message = Mock()
        mock_bot_message.id = 2
        mock_message_class.objects.create.return_value = mock_bot_message

        generate_bot_response(1, 'app-uuid')

        assert mock_message_class.objects.create.call_count >= 1
        mock_send_live.assert_called_once()

    @patch('core.tasks.message._send_live_update')
    @patch('core.tasks.message._send_live_update_to_dashboard')
    @patch('core.tasks.message.EscalationService')
    @patch('core.tasks.message.ToolCallExecutor')
    @patch('core.tasks.message.TemplateLoader')
    @patch('core.tasks.message.get_chunks')
    @patch('core.tasks.message.get_enabled_tools_for_app')
    @patch('core.tasks.message.IngestedChunk')
    @patch('core.tasks.message.AIClientService')
    @patch('core.tasks.message.Application')
    @patch('core.tasks.message.Message')
    @patch('core.tasks.message.messages_to_llm_conversation')
    @patch('core.tasks.message.add_instructions_to_convo')
    @patch('core.tasks.message.add_kb_to_convo')
    @patch('core.models.AppIntegration')
    @patch('core.models.ToolConfig')
    def test_generate_bot_response_escalation_triggered(self, mock_tool_config, mock_app_integration, mock_add_kb, mock_add_instructions, mock_messages_to_llm, mock_message_class, mock_app_class, mock_ai_client_service, mock_ingested_chunk, mock_get_tools, mock_get_chunks, mock_template_loader, mock_executor_class, mock_escalation_service, mock_send_dashboard, mock_send_live):
        mock_app = Mock()
        mock_app.uuid = 'app-uuid'
        mock_app.get_prompt_config.return_value = {
            'tone': 'professional',
            'response_style': 'concise',
            'custom_instructions': 'Be helpful',
            'role': 'assistant',
            'behavior': 'friendly'
        }
        mock_app.name = 'Test App'
        mock_app_class.objects.get.return_value = mock_app

        mock_user_message = Mock()
        mock_user_message.id = 1
        mock_user_message.chatroom = Mock()
        mock_user_message.message = 'test question'
        mock_user_message.platform = 'widget'
        mock_user_message.is_internal = False
        mock_user_message.metadata = {}
        mock_message_class.objects.get.return_value = mock_user_message

        mock_ai_client_instance = Mock()
        mock_provider = Mock()
        mock_agent_response = Mock()
        mock_agent_response.answer = 'test answer'
        mock_agent_response.status = 'SUCCESS'
        mock_agent_response.escalation = True
        mock_agent_response.reason_for_escalation = 'High escalation score'
        mock_agent_response.sentiment_score = 80
        mock_agent_response.escalation_score = 80
        mock_agent_response.criticality_score = 5
        mock_provider.generate_with_conversation.return_value = (mock_agent_response, None, {'prompt_tokens': 100})
        mock_ai_client_instance.get_client_and_model.return_value = (mock_provider, 'gpt-4')
        mock_ai_client_service.return_value = mock_ai_client_instance

        mock_ingested_chunk.objects.filter.return_value.exists.return_value = False
        mock_get_tools.return_value = None
        mock_get_chunks.return_value = []
        mock_template_loader.render_template.return_value = 'system instruction'

        mock_tool_config.objects.filter.return_value.values_list.return_value.distinct.return_value = []
        mock_app_integration.objects.filter.return_value.select_related.return_value = []

        mock_messages_qs = Mock()
        mock_messages_qs.count.return_value = 1
        mock_message_class.objects.filter.return_value.order_by.return_value = mock_messages_qs

        mock_messages_to_llm.side_effect = lambda *args, **kwargs: []
        mock_add_instructions.side_effect = lambda *args, **kwargs: []
        mock_add_kb.side_effect = lambda *args, **kwargs: []

        mock_bot_message = Mock()
        mock_bot_message.id = 2
        mock_message_class.objects.create.return_value = mock_bot_message

        mock_escalation_instance = Mock()
        mock_escalation_instance.should_escalate.return_value = True
        mock_escalation_instance.escalate.return_value = {'escalation_reason': 'High escalation score', 'notified_profiles': ['profile1']}
        mock_escalation_service.return_value = mock_escalation_instance

        generate_bot_response(1, 'app-uuid')

        mock_escalation_instance.escalate.assert_called_once()
        mock_send_live.assert_called_once()

    @patch('core.tasks.message._send_live_update')
    @patch('core.tasks.message._send_live_update_to_dashboard')
    @patch('core.tasks.message.EscalationService')
    @patch('core.tasks.message.ToolCallExecutor')
    @patch('core.tasks.message.TemplateLoader')
    @patch('core.tasks.message.get_chunks')
    @patch('core.tasks.message.get_enabled_tools_for_app')
    @patch('core.tasks.message.IngestedChunk')
    @patch('core.tasks.message.AIClientService')
    @patch('core.tasks.message.Application')
    @patch('core.tasks.message.Message')
    @patch('core.tasks.message.messages_to_llm_conversation')
    @patch('core.tasks.message.add_instructions_to_convo')
    @patch('core.tasks.message.add_kb_to_convo')
    @patch('core.models.AppIntegration')
    @patch('core.models.ToolConfig')
    def test_generate_bot_response_escalation_no_profiles(self, mock_tool_config, mock_app_integration, mock_add_kb, mock_add_instructions, mock_messages_to_llm, mock_message_class, mock_app_class, mock_ai_client_service, mock_ingested_chunk, mock_get_tools, mock_get_chunks, mock_template_loader, mock_executor_class, mock_escalation_service, mock_send_dashboard, mock_send_live):
        mock_app = Mock()
        mock_app.uuid = 'app-uuid'
        mock_app.get_prompt_config.return_value = {
            'tone': 'professional',
            'response_style': 'concise',
            'custom_instructions': 'Be helpful',
            'role': 'assistant',
            'behavior': 'friendly'
        }
        mock_app.name = 'Test App'
        mock_app_class.objects.get.return_value = mock_app

        mock_user_message = Mock()
        mock_user_message.id = 1
        mock_user_message.chatroom = Mock()
        mock_user_message.message = 'test question'
        mock_user_message.platform = 'widget'
        mock_user_message.is_internal = False
        mock_user_message.metadata = {}
        mock_message_class.objects.get.return_value = mock_user_message

        mock_ai_client_instance = Mock()
        mock_provider = Mock()
        mock_agent_response = Mock()
        mock_agent_response.answer = 'test answer'
        mock_agent_response.status = 'SUCCESS'
        mock_agent_response.escalation = True
        mock_agent_response.reason_for_escalation = 'High escalation score'
        mock_agent_response.sentiment_score = 80
        mock_agent_response.escalation_score = 80
        mock_agent_response.criticality_score = 5
        mock_provider.generate_with_conversation.return_value = (mock_agent_response, None, {'prompt_tokens': 100})
        mock_ai_client_instance.get_client_and_model.return_value = (mock_provider, 'gpt-4')
        mock_ai_client_service.return_value = mock_ai_client_instance

        mock_ingested_chunk.objects.filter.return_value.exists.return_value = False
        mock_get_tools.return_value = None
        mock_get_chunks.return_value = []
        mock_template_loader.render_template.return_value = 'system instruction'

        mock_tool_config.objects.filter.return_value.values_list.return_value.distinct.return_value = []
        mock_app_integration.objects.filter.return_value.select_related.return_value = []

        mock_messages_qs = Mock()
        mock_messages_qs.count.return_value = 1
        mock_message_class.objects.filter.return_value.order_by.return_value = mock_messages_qs

        mock_messages_to_llm.side_effect = lambda *args, **kwargs: []
        mock_add_instructions.side_effect = lambda *args, **kwargs: []
        mock_add_kb.side_effect = lambda *args, **kwargs: []

        mock_bot_message = Mock()
        mock_bot_message.id = 2
        mock_message_class.objects.create.return_value = mock_bot_message

        mock_escalation_instance = Mock()
        mock_escalation_instance.should_escalate.return_value = True
        mock_escalation_instance.escalate.return_value = {'escalation_reason': 'High escalation score', 'notified_profiles': []}
        mock_escalation_service.return_value = mock_escalation_instance

        generate_bot_response(1, 'app-uuid')

        assert mock_message_class.objects.create.call_count >= 2
        mock_send_live.assert_called_once()
