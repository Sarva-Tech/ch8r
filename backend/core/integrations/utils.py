from google.genai import types

from core.integrations.providers.project_management.registry import PM_REGISTRY

INTEGRATION_PROVIDERS = {
    **PM_REGISTRY,
}

def get_toolkit_for_instance(integration):
    provider = INTEGRATION_PROVIDERS.get(integration.provider)
    if not provider:
        raise ValueError(f"Unknown provider slug: {integration.provider}")
    return provider["toolkit"](integration.config)

def convert_function_declaration_to_type(func_decl_dict):
    return types.FunctionDeclaration(
        name=func_decl_dict["name"],
        description=func_decl_dict.get("description", ""),
        parameters=func_decl_dict.get("parameters", {}),
    )

def build_tool_for_integration(integration):
    toolkit = get_toolkit_for_instance(integration)
    func_decl_dicts = toolkit.get_function_declarations()
    func_decls = [convert_function_declaration_to_type(f) for f in func_decl_dicts]
    tool = types.Tool(function_declarations=func_decls)
    return tool

def get_tools_for_app(app):
    integrations = app.integrations.filter(category="project_management")
    return [build_tool_for_integration(integration) for integration in integrations]


def execute_tool_call(app, function_call):
    integrations = app.integrations.filter(category="project_management")
    for integration in integrations:
        toolkit = get_toolkit_for_instance(integration)
        func_declarations = toolkit.get_function_declarations()

        if any(d['name'] == function_call.name for d in func_declarations):
            return toolkit.run_tool(function_call.name, function_call.args)

    raise ValueError(f"Tool with name '{function_call.name}' not found for this app.")