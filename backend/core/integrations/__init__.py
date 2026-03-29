from .integration_dispatcher import get_app_integrations, execute_tool_call
from .registry import INTEGRATION_TOOLS, TOOL_HANDLERS
from core.consts import SUPPORTED_INTEGRATIONS

# SUPPORTED_PROVIDERS is kept for backward compatibility with configure_app view
SUPPORTED_PROVIDERS = [entry['id'] for entry in SUPPORTED_INTEGRATIONS]