from core.integrations.pms_github import PMS_GITHUB_TOOLS, PMS_GITHUB_HANDLERS

PROVIDER_TOOLS = {
    "pms_github": {
        **PMS_GITHUB_TOOLS,
    }
}

TOOL_HANDLERS = {
    **PMS_GITHUB_HANDLERS,
}