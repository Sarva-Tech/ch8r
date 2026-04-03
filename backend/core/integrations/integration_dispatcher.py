import logging

from core.models import AppIntegration, ToolConfig
from core.integrations.registry import INTEGRATION_TOOLS, INTEGRATION_HANDLERS
from core.integrations.custom_tool_parser import parse_url_schema

logger = logging.getLogger(__name__)


def get_enabled_tools_for_app(application_id: str) -> list[dict]:
    try:
        app_integrations = AppIntegration.objects.filter(
            application__uuid=application_id, is_active=True
        ).select_related('integration')

        result = []

        for ai in app_integrations:
            integration_key = f"{ai.integration.provider}_{ai.integration_type}"
            tools = INTEGRATION_TOOLS.get(integration_key, {})

            configs = {
                tc.tool_id: tc.is_enabled
                for tc in ToolConfig.objects.filter(app_integration=ai, is_builtin=True)
            }

            enabled_titles = []
            for tool in tools.values():
                scoped_tool_id = f"{integration_key}:{tool['id']}"
                is_enabled = configs.get(scoped_tool_id, False)
                if is_enabled:
                    result.append(tool['schema'])
                    enabled_titles.append(tool['title'])

            for tc in ToolConfig.objects.filter(app_integration=ai, is_builtin=False, is_enabled=True):
                schema = parse_url_schema(tc.title, tc.description, tc.url_schema)
                result.append(schema)
                enabled_titles.append(tc.title)

            logger.info(
                "available %s tools: %s",
                integration_key,
                ', '.join(enabled_titles),
            )

        return result

    except Exception as exc:
        logger.error("get_enabled_tools_for_app failed for application_id=%s: %s", application_id, exc)
        return []


def execute_tool_call(application_id, tool_name, **arguments):
    app_integrations = AppIntegration.objects.filter(
        application__uuid=application_id, is_active=True
    ).select_related('integration')

    for ai in app_integrations:
        integration_key = f"{ai.integration.provider}_{ai.integration_type}"
        handlers = INTEGRATION_HANDLERS.get(integration_key, {})
        if tool_name in handlers:
            return handlers[tool_name](ai, **arguments)

    raise ValueError(f"No handler found for tool '{tool_name}' in application {application_id}")
