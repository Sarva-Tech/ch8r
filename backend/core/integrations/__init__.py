from .integration_dispatcher import get_enabled_tools_for_app, execute_tool_call
from .registry import INTEGRATION_TOOLS
from core.consts import SUPPORTED_INTEGRATIONS

# SUPPORTED_PROVIDERS is kept for backward compatibility with configure_app view
SUPPORTED_PROVIDERS = [entry['id'] for entry in SUPPORTED_INTEGRATIONS]
