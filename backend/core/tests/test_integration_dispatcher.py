import pytest
from unittest.mock import Mock, patch, MagicMock

from core.integrations.integration_dispatcher import (
    get_enabled_tools_for_app,
    execute_tool_call,
)


@pytest.mark.unit
class TestGetEnabledToolsForApp:
    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.ToolConfig")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_TOOLS")
    def test_get_enabled_tools_no_integrations(self, mock_tools, mock_tc, mock_ai):
        mock_ai.objects.filter.return_value.select_related.return_value = []

        result = get_enabled_tools_for_app("app-uuid-123")

        assert result == []
        mock_ai.objects.filter.assert_called_once_with(application__uuid="app-uuid-123", is_active=True)

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.ToolConfig")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_TOOLS")
    def test_get_enabled_tools_with_builtin_tools_enabled(self, mock_tools, mock_tc, mock_ai):
        mock_app_integration = Mock()
        mock_app_integration.integration.provider = "github"
        mock_app_integration.integration_type = "version_control"
        mock_ai.objects.filter.return_value.select_related.return_value = [mock_app_integration]

        mock_tools.get.return_value = {
            "list_commits": {
                "id": "list_commits",
                "title": "List Commits",
                "schema": {"type": "function", "function": {"name": "list_commits"}}
            }
        }

        def filter_side_effect(*args, **kwargs):
            if kwargs.get("is_builtin") is True:
                return [
                    Mock(tool_id="github_version_control:list_commits", is_enabled=True)
                ]
            return []

        mock_tc.objects.filter.side_effect = filter_side_effect

        result = get_enabled_tools_for_app("app-uuid-123")

        assert len(result) == 1
        assert result[0]["function"]["name"] == "list_commits"

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.ToolConfig")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_TOOLS")
    def test_get_enabled_tools_with_builtin_tools_disabled(self, mock_tools, mock_tc, mock_ai):
        mock_app_integration = Mock()
        mock_app_integration.integration.provider = "github"
        mock_app_integration.integration_type = "version_control"
        mock_ai.objects.filter.return_value.select_related.return_value = [mock_app_integration]

        mock_tools.get.return_value = {
            "list_commits": {
                "id": "list_commits",
                "title": "List Commits",
                "schema": {"type": "function", "function": {"name": "list_commits"}}
            }
        }

        def filter_side_effect(*args, **kwargs):
            if kwargs.get("is_builtin") is True:
                return [
                    Mock(tool_id="github_version_control:list_commits", is_enabled=False)
                ]
            return []

        mock_tc.objects.filter.side_effect = filter_side_effect

        result = get_enabled_tools_for_app("app-uuid-123")

        assert len(result) == 0

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.ToolConfig")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_TOOLS")
    @patch("core.integrations.integration_dispatcher.parse_url_schema")
    def test_get_enabled_tools_with_custom_tools(self, mock_parse, mock_tools, mock_tc, mock_ai):
        mock_app_integration = Mock()
        mock_app_integration.integration.provider = "github"
        mock_app_integration.integration_type = "version_control"
        mock_ai.objects.filter.return_value.select_related.return_value = [mock_app_integration]

        mock_tools.get.return_value = {}

        def filter_side_effect(*args, **kwargs):
            if kwargs.get("is_builtin") is True:
                return []
            elif kwargs.get("is_builtin") is False and kwargs.get("is_enabled") is True:
                mock_custom_tc = Mock()
                mock_custom_tc.title = "Custom Tool"
                mock_custom_tc.description = "A custom tool"
                mock_custom_tc.url_schema = 'curl -X POST https://api.example.com/endpoint --data \'{"test": "value"}\''
                return [mock_custom_tc]
            return []

        mock_tc.objects.filter.side_effect = filter_side_effect

        mock_parse.return_value = {
            "type": "function",
            "function": {"name": "custom_tool", "description": "A custom tool"}
        }

        result = get_enabled_tools_for_app("app-uuid-123")

        assert len(result) == 1
        assert result[0]["function"]["name"] == "custom_tool"

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.ToolConfig")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_TOOLS")
    def test_get_enabled_tools_multiple_integrations(self, mock_tools, mock_tc, mock_ai):
        mock_integration1 = Mock()
        mock_integration1.integration.provider = "github"
        mock_integration1.integration_type = "version_control"

        mock_integration2 = Mock()
        mock_integration2.integration.provider = "github"
        mock_integration2.integration_type = "project_management"

        mock_ai.objects.filter.return_value.select_related.return_value = [mock_integration1, mock_integration2]

        def tools_side_effect(key, default=None):
            if key == "github_version_control":
                return {
                    "list_commits": {
                        "id": "list_commits",
                        "title": "List Commits",
                        "schema": {"type": "function", "function": {"name": "list_commits"}}
                    }
                }
            elif key == "github_project_management":
                return {
                    "list_tickets": {
                        "id": "list_tickets",
                        "title": "List Tickets",
                        "schema": {"type": "function", "function": {"name": "list_tickets"}}
                    }
                }
            return default or {}

        mock_tools.get.side_effect = tools_side_effect

        filter_call_count = [0]

        def tc_filter_side_effect(*args, **kwargs):
            filter_call_count[0] += 1
            if kwargs.get("is_builtin") is True:
                if filter_call_count[0] == 1:
                    return [
                        Mock(tool_id="github_version_control:list_commits", is_enabled=True)
                    ]
                else:
                    return [
                        Mock(tool_id="github_project_management:list_tickets", is_enabled=True)
                    ]
            return []

        mock_tc.objects.filter.side_effect = tc_filter_side_effect

        result = get_enabled_tools_for_app("app-uuid-123")

        assert len(result) == 2
        tool_names = [t["function"]["name"] for t in result]
        assert "list_commits" in tool_names
        assert "list_tickets" in tool_names

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.ToolConfig")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_TOOLS")
    def test_get_enabled_tools_unknown_integration_key(self, mock_tools, mock_tc, mock_ai):
        mock_app_integration = Mock()
        mock_app_integration.integration.provider = "unknown"
        mock_app_integration.integration_type = "type"
        mock_ai.objects.filter.return_value.select_related.return_value = [mock_app_integration]

        mock_tools.get.return_value = {}

        def filter_side_effect(*args, **kwargs):
            return []

        mock_tc.objects.filter.side_effect = filter_side_effect

        result = get_enabled_tools_for_app("app-uuid-123")

        assert result == []

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.ToolConfig")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_TOOLS")
    def test_get_enabled_tools_no_tool_configs(self, mock_tools, mock_tc, mock_ai):
        mock_app_integration = Mock()
        mock_app_integration.integration.provider = "github"
        mock_app_integration.integration_type = "version_control"
        mock_ai.objects.filter.return_value.select_related.return_value = [mock_app_integration]

        mock_tools.get.return_value = {
            "list_commits": {
                "id": "list_commits",
                "title": "List Commits",
                "schema": {"type": "function", "function": {"name": "list_commits"}}
            }
        }

        def filter_side_effect(*args, **kwargs):
            return []

        mock_tc.objects.filter.side_effect = filter_side_effect

        result = get_enabled_tools_for_app("app-uuid-123")

        assert result == []

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.ToolConfig")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_TOOLS")
    def test_get_enabled_tools_exception_returns_empty(self, mock_tools, mock_tc, mock_ai):
        mock_ai.objects.filter.side_effect = Exception("Database error")

        result = get_enabled_tools_for_app("app-uuid-123")

        assert result == []

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.ToolConfig")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_TOOLS")
    def test_get_enabled_tools_default_disabled(self, mock_tools, mock_tc, mock_ai):
        mock_app_integration = Mock()
        mock_app_integration.integration.provider = "github"
        mock_app_integration.integration_type = "version_control"
        mock_ai.objects.filter.return_value.select_related.return_value = [mock_app_integration]

        mock_tools.get.return_value = {
            "list_commits": {
                "id": "list_commits",
                "title": "List Commits",
                "schema": {"type": "function", "function": {"name": "list_commits"}}
            }
        }

        def filter_side_effect(*args, **kwargs):
            return []

        mock_tc.objects.filter.side_effect = filter_side_effect

        result = get_enabled_tools_for_app("app-uuid-123")

        assert len(result) == 0


@pytest.mark.unit
class TestExecuteToolCall:
    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_HANDLERS")
    def test_execute_tool_call_success(self, mock_handlers, mock_ai):
        mock_app_integration = Mock()
        mock_app_integration.integration.provider = "github"
        mock_app_integration.integration_type = "version_control"
        mock_ai.objects.filter.return_value.select_related.return_value = [mock_app_integration]

        mock_handler = Mock(return_value={"result": "success"})
        mock_handlers.get.return_value = {"list_commits": mock_handler}

        result = execute_tool_call("app-uuid-123", "list_commits", sha="main")

        assert result == {"result": "success"}
        mock_handler.assert_called_once_with(mock_app_integration, sha="main")

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_HANDLERS")
    def test_execute_tool_call_no_handler_found(self, mock_handlers, mock_ai):
        mock_app_integration = Mock()
        mock_app_integration.integration.provider = "github"
        mock_app_integration.integration_type = "version_control"
        mock_ai.objects.filter.return_value.select_related.return_value = [mock_app_integration]

        mock_handlers.get.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            execute_tool_call("app-uuid-123", "unknown_tool")

        assert "No handler found for tool 'unknown_tool'" in str(exc_info.value)

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_HANDLERS")
    def test_execute_tool_call_no_integrations(self, mock_handlers, mock_ai):
        mock_ai.objects.filter.return_value.select_related.return_value = []

        with pytest.raises(ValueError) as exc_info:
            execute_tool_call("app-uuid-123", "list_commits")

        assert "No handler found for tool 'list_commits'" in str(exc_info.value)

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_HANDLERS")
    def test_execute_tool_call_multiple_integrations(self, mock_handlers, mock_ai):
        mock_integration1 = Mock()
        mock_integration1.integration.provider = "github"
        mock_integration1.integration_type = "version_control"

        mock_integration2 = Mock()
        mock_integration2.integration.provider = "github"
        mock_integration2.integration_type = "project_management"

        mock_ai.objects.filter.return_value.select_related.return_value = [mock_integration1, mock_integration2]

        mock_handler = Mock(return_value={"result": "success"})
        mock_handlers.get.side_effect = lambda key, default=None: {
            "github_version_control": {"list_commits": mock_handler},
            "github_project_management": {"list_tickets": Mock()}
        }.get(key, default or {})

        result = execute_tool_call("app-uuid-123", "list_commits", sha="main")

        assert result == {"result": "success"}
        mock_handler.assert_called_once_with(mock_integration1, sha="main")

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_HANDLERS")
    def test_execute_tool_call_with_arguments(self, mock_handlers, mock_ai):
        mock_app_integration = Mock()
        mock_app_integration.integration.provider = "github"
        mock_app_integration.integration_type = "version_control"
        mock_ai.objects.filter.return_value.select_related.return_value = [mock_app_integration]

        mock_handler = Mock(return_value={"result": "success"})
        mock_handlers.get.return_value = {"list_commits": mock_handler}

        result = execute_tool_call(
            "app-uuid-123",
            "list_commits",
            sha="main",
            path="src/",
            author="john",
            per_page=10
        )

        assert result == {"result": "success"}
        mock_handler.assert_called_once_with(
            mock_app_integration,
            sha="main",
            path="src/",
            author="john",
            per_page=10
        )

    @patch("core.integrations.integration_dispatcher.AppIntegration")
    @patch("core.integrations.integration_dispatcher.INTEGRATION_HANDLERS")
    def test_execute_tool_call_inactive_integration(self, mock_handlers, mock_ai):
        mock_ai.objects.filter.return_value.select_related.return_value = []

        with pytest.raises(ValueError) as exc_info:
            execute_tool_call("app-uuid-123", "list_commits")

        assert "No handler found for tool 'list_commits'" in str(exc_info.value)
        mock_ai.objects.filter.assert_called_once_with(application__uuid="app-uuid-123", is_active=True)
