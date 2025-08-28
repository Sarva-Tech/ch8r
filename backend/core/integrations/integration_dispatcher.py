from core.models import AppIntegration
from core.integrations.registry import PROVIDER_TOOLS, TOOL_HANDLERS


def get_app_integrations(application_id):
    app_integrations = AppIntegration.objects.filter(application_id=application_id)
    tools = {}

    for ai in app_integrations.select_related("integration"):
        integration_type = ai.integration.type
        integration_provider = ai.integration.provider
        key = f"{integration_type}_{integration_provider}"
        if integration_type in PROVIDER_TOOLS:
            tools.update(PROVIDER_TOOLS[key])

    return list(tools.values())


def execute_tool_call(application_id, tool_name, **arguments):
    ai = AppIntegration.objects.filter(
        application_id=application_id,
    ).select_related("integration").first()

    if not ai:
        raise ValueError(f"No integration found for tool {tool_name}")

    integration = ai.integration
    handler = TOOL_HANDLERS.get(tool_name)

    if not handler:
        raise ValueError(f"No handler for tool {tool_name}")

    return handler(integration, **arguments)