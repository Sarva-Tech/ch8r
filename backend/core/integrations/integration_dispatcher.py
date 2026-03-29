from core.models import AppIntegration
from core.integrations.registry import INTEGRATION_TOOLS, TOOL_HANDLERS


def get_app_integrations(application_id):
    app_integrations = AppIntegration.objects.filter(
        application_id=application_id, is_active=True
    ).select_related('integration')

    tools = {}
    for app_integration in app_integrations:
        key = f"{app_integration.integration.provider}_{app_integration.integration_type}"
        if key in INTEGRATION_TOOLS:
            tools.update(INTEGRATION_TOOLS[key])

    return list(tools.values())


def execute_tool_call(application_id, tool_name, **arguments):
    app_integration = AppIntegration.objects.filter(
        application_id=application_id,
        integration_type='project_management',
        is_active=True,
    ).select_related('integration').first()

    if not app_integration:
        raise ValueError(
            f"No project_management integration configured for application {application_id}"
        )

    handler = TOOL_HANDLERS.get(tool_name)

    if not handler:
        raise ValueError(f"No handler for tool {tool_name}")

    return handler(app_integration, **arguments)
