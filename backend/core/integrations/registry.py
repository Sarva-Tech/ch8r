from core.integrations.pms_github import PMS_GITHUB_TOOLS, PMS_GITHUB_HANDLERS

INTEGRATION_TOOLS = {
    "pms_github": {
        **PMS_GITHUB_TOOLS,
    }
}

TOOL_HANDLERS = {
    **PMS_GITHUB_HANDLERS,
}

SUPPORTED_INTEGRATIONS = ["pms"]
SUPPORTED_PROVIDERS = {
    "pms": ["github"],
    "crm": [],
}
