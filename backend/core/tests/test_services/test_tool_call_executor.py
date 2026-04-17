import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid

from core.services.tool_call_executor import (
    _extract_url_from_schema,
    _get_tool_url,
    ToolCallExecutor,
    _monotonic_ns,
    _elapsed_ms
)


@pytest.mark.unit
class TestExtractUrlFromSchema:
    def test_extract_url_from_schema_with_url(self):
        schema = 'https://example.com/api/endpoint'
        result = _extract_url_from_schema(schema)
        
        assert result == 'https://example.com/api/endpoint'

    def test_extract_url_from_schema_with_text(self):
        schema = 'The URL is https://example.com/api and some text'
        result = _extract_url_from_schema(schema)
        
        assert result == 'https://example.com/api'

    def test_extract_url_from_schema_http(self):
        schema = 'http://example.com'
        result = _extract_url_from_schema(schema)
        
        assert result == 'http://example.com'

    def test_extract_url_from_schema_no_url(self):
        schema = 'No URL here'
        result = _extract_url_from_schema(schema)
        
        assert result == ''

    def test_extract_url_from_schema_empty_string(self):
        result = _extract_url_from_schema('')
        
        assert result == ''

    def test_extract_url_from_schema_none(self):
        result = _extract_url_from_schema(None)
        
        assert result == ''


@pytest.mark.unit
class TestGetToolUrl:
    @patch('core.services.tool_call_executor._extract_url_from_schema')
    @patch('core.models.ToolConfig')
    @patch('core.models.AppIntegration')
    @patch('core.integrations.custom_tool_parser._derive_name')
    def test_get_tool_url_success(self, mock_derive_name, mock_app_integration_class, mock_tool_config_class, mock_extract_url):
        mock_app_uuid = str(uuid.uuid4())
        mock_tool_name = 'test_tool'
        
        mock_derive_name.return_value = 'test_tool'
        mock_extract_url.return_value = 'https://example.com/api'
        
        mock_tc = Mock()
        mock_tc.url_schema = 'https://example.com/api'
        mock_tc.title = 'Test Tool'
        mock_tool_config_class.objects.filter.return_value.first.return_value = mock_tc
        
        mock_ai = Mock()
        mock_ai.integration = Mock()
        mock_app_integration_class.objects.filter.return_value.select_related.return_value = [mock_ai]
        
        result = _get_tool_url(mock_app_uuid, mock_tool_name)
        
        assert result == 'https://example.com/api'
        mock_app_integration_class.objects.filter.assert_called_once_with(
            application__uuid=mock_app_uuid, is_active=True
        )

    @patch('core.services.tool_call_executor._extract_url_from_schema')
    @patch('core.models.ToolConfig')
    @patch('core.models.AppIntegration')
    @patch('core.integrations.custom_tool_parser._derive_name')
    def test_get_tool_url_name_mismatch(self, mock_derive_name, mock_app_integration_class, mock_tool_config_class, mock_extract_url):
        mock_app_uuid = str(uuid.uuid4())
        mock_tool_name = 'test_tool'
        
        mock_derive_name.return_value = 'different_tool'
        
        mock_tc = Mock()
        mock_tc.url_schema = 'https://example.com/api'
        mock_tc.title = 'Different Tool'
        mock_tool_config_class.objects.filter.return_value.first.return_value = mock_tc
        
        mock_ai = Mock()
        mock_ai.integration = Mock()
        mock_app_integration_class.objects.filter.return_value.select_related.return_value = [mock_ai]
        
        result = _get_tool_url(mock_app_uuid, mock_tool_name)
        
        assert result == ''

    @patch('core.models.ToolConfig')
    @patch('core.models.AppIntegration')
    def test_get_tool_url_no_tool_config(self, mock_app_integration_class, mock_tool_config_class):
        mock_app_uuid = str(uuid.uuid4())
        mock_tool_name = 'test_tool'
        
        mock_tool_config_class.objects.filter.return_value.first.return_value = None
        
        mock_ai = Mock()
        mock_ai.integration = Mock()
        mock_app_integration_class.objects.filter.return_value.select_related.return_value = [mock_ai]
        
        result = _get_tool_url(mock_app_uuid, mock_tool_name)
        
        assert result == ''

    @patch('core.models.AppIntegration')
    def test_get_tool_url_no_integrations(self, mock_app_integration_class):
        mock_app_uuid = str(uuid.uuid4())
        mock_tool_name = 'test_tool'
        
        mock_app_integration_class.objects.filter.return_value.select_related.return_value = []
        
        result = _get_tool_url(mock_app_uuid, mock_tool_name)
        
        assert result == ''

    @patch('core.models.AppIntegration')
    def test_get_tool_url_exception(self, mock_app_integration_class):
        mock_app_uuid = str(uuid.uuid4())
        mock_tool_name = 'test_tool'
        
        mock_app_integration_class.objects.filter.side_effect = Exception('DB Error')
        
        result = _get_tool_url(mock_app_uuid, mock_tool_name)
        
        assert result == ''


@pytest.mark.unit
class TestToolCallExecutor:
    @patch('core.services.tool_call_executor.execute_tool_call')
    @patch('core.services.tool_call_executor._get_tool_url')
    @patch('core.services.tool_call_executor._monotonic_ns')
    @patch('core.services.tool_call_executor._elapsed_ms')
    def test_execute_all_success(self, mock_elapsed_ms, mock_monotonic_ns, mock_get_tool_url, mock_execute_tool_call):
        mock_app_uuid = str(uuid.uuid4())
        mock_monotonic_ns.return_value = 1000000000
        mock_elapsed_ms.return_value = 100
        mock_get_tool_url.return_value = 'https://example.com/api'
        mock_execute_tool_call.return_value = {'result': 'success'}
        
        tool_calls = [
            {
                'name': 'test_tool',
                'args': {'param': 'value'},
                'id': 'call_123'
            }
        ]
        
        executor = ToolCallExecutor()
        records, messages = executor.execute_all(mock_app_uuid, tool_calls)
        
        assert len(records) == 1
        assert len(messages) == 1
        assert records[0]['name'] == 'test_tool'
        assert records[0]['input_parameters'] == {'param': 'value'}
        assert records[0]['raw_result'] == {'result': 'success'}
        assert records[0]['duration_ms'] == 100
        assert messages[0]['role'] == 'tool'
        assert messages[0]['tool_call_id'] == 'call_123'
        assert messages[0]['content'] == "{'result': 'success'}"

    @patch('core.services.tool_call_executor.execute_tool_call')
    @patch('core.services.tool_call_executor._get_tool_url')
    @patch('core.services.tool_call_executor._monotonic_ns')
    @patch('core.services.tool_call_executor._elapsed_ms')
    def test_execute_all_error(self, mock_elapsed_ms, mock_monotonic_ns, mock_get_tool_url, mock_execute_tool_call):
        mock_app_uuid = str(uuid.uuid4())
        mock_monotonic_ns.return_value = 1000000000
        mock_elapsed_ms.return_value = 100
        mock_get_tool_url.return_value = 'https://example.com/api'
        mock_execute_tool_call.side_effect = Exception('Tool failed')
        
        tool_calls = [
            {
                'name': 'test_tool',
                'args': {'param': 'value'},
                'id': 'call_123'
            }
        ]
        
        executor = ToolCallExecutor()
        records, messages = executor.execute_all(mock_app_uuid, tool_calls)
        
        assert len(records) == 1
        assert len(messages) == 1
        assert records[0]['name'] == 'test_tool'
        assert 'error' in records[0]
        assert records[0]['error']['message'] == 'Tool failed'
        assert messages[0]['content'] == 'Error: Tool failed'

    @patch('core.services.tool_call_executor.execute_tool_call')
    @patch('core.services.tool_call_executor._get_tool_url')
    @patch('core.services.tool_call_executor._monotonic_ns')
    @patch('core.services.tool_call_executor._elapsed_ms')
    def test_execute_all_multiple_calls(self, mock_elapsed_ms, mock_monotonic_ns, mock_get_tool_url, mock_execute_tool_call):
        mock_app_uuid = str(uuid.uuid4())
        mock_monotonic_ns.return_value = 1000000000
        mock_elapsed_ms.return_value = 100
        mock_get_tool_url.return_value = 'https://example.com/api'
        mock_execute_tool_call.side_effect = [
            {'result': 'success1'},
            {'result': 'success2'}
        ]
        
        tool_calls = [
            {
                'name': 'tool1',
                'args': {'param': 'value1'},
                'id': 'call_1'
            },
            {
                'name': 'tool2',
                'args': {'param': 'value2'},
                'id': 'call_2'
            }
        ]
        
        executor = ToolCallExecutor()
        records, messages = executor.execute_all(mock_app_uuid, tool_calls)
        
        assert len(records) == 2
        assert len(messages) == 2
        assert records[0]['name'] == 'tool1'
        assert records[1]['name'] == 'tool2'

    @patch('core.services.tool_call_executor.execute_tool_call')
    @patch('core.services.tool_call_executor._get_tool_url')
    @patch('core.services.tool_call_executor._monotonic_ns')
    @patch('core.services.tool_call_executor._elapsed_ms')
    def test_execute_all_empty_args(self, mock_elapsed_ms, mock_monotonic_ns, mock_get_tool_url, mock_execute_tool_call):
        mock_app_uuid = str(uuid.uuid4())
        mock_monotonic_ns.return_value = 1000000000
        mock_elapsed_ms.return_value = 100
        mock_get_tool_url.return_value = 'https://example.com/api'
        mock_execute_tool_call.return_value = {'result': 'success'}
        
        tool_calls = [
            {
                'name': 'test_tool',
                'args': None,
                'id': 'call_123'
            }
        ]
        
        executor = ToolCallExecutor()
        records, messages = executor.execute_all(mock_app_uuid, tool_calls)
        
        assert len(records) == 1
        assert records[0]['input_parameters'] == {}

    @patch('core.services.tool_call_executor.execute_tool_call')
    @patch('core.services.tool_call_executor._get_tool_url')
    @patch('core.services.tool_call_executor._monotonic_ns')
    @patch('core.services.tool_call_executor._elapsed_ms')
    def test_execute_all_missing_fields(self, mock_elapsed_ms, mock_monotonic_ns, mock_get_tool_url, mock_execute_tool_call):
        mock_app_uuid = str(uuid.uuid4())
        mock_monotonic_ns.return_value = 1000000000
        mock_elapsed_ms.return_value = 100
        mock_get_tool_url.return_value = ''
        mock_execute_tool_call.return_value = {'result': 'success'}
        
        tool_calls = [
            {
                'name': 'test_tool',
                'args': {'param': 'value'}
            }
        ]
        
        executor = ToolCallExecutor()
        records, messages = executor.execute_all(mock_app_uuid, tool_calls)
        
        assert len(records) == 1
        assert records[0]['name'] == 'test_tool'
        assert records[0]['url'] == ''
        assert messages[0]['tool_call_id'] == ''

    @patch('core.services.tool_call_executor.execute_tool_call')
    @patch('core.services.tool_call_executor._get_tool_url')
    @patch('core.services.tool_call_executor._monotonic_ns')
    @patch('core.services.tool_call_executor._elapsed_ms')
    def test_execute_all_empty_list(self, mock_elapsed_ms, mock_monotonic_ns, mock_get_tool_url, mock_execute_tool_call):
        mock_app_uuid = str(uuid.uuid4())
        
        tool_calls = []
        
        executor = ToolCallExecutor()
        records, messages = executor.execute_all(mock_app_uuid, tool_calls)
        
        assert records == []
        assert messages == []
        mock_execute_tool_call.assert_not_called()
