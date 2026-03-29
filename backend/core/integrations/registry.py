from core.integrations.pms_github import PMS_GITHUB_TOOLS, PMS_GITHUB_HANDLERS

INTEGRATION_TOOLS = {
    "github_project_management": {
        **PMS_GITHUB_TOOLS,
    }
}

TOOL_HANDLERS = {
    **PMS_GITHUB_HANDLERS,
}
