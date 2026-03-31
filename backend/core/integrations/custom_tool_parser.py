import json
import logging
import re

logger = logging.getLogger(__name__)

_TYPE_MAP = {
    str: "string",
    int: "number",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "string",
}


def _derive_name(title: str) -> str:
    name = title.lower()
    name = name.replace(" ", "_")
    name = re.sub(r"[^a-z0-9_]", "", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "custom_tool"


def _minimal_schema(name: str, description: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }


def _infer_type(value) -> str:
    return _TYPE_MAP.get(type(value), "string")


def parse_url_schema(title: str, description: str, url_schema: str) -> dict:
    name = _derive_name(title)
    try:
        pattern = r"""(?:--data|-d)\s+(?:'([^']*)'|"((?:[^"\\]|\\.)*)"|(\{.*\}))"""
        match = re.search(pattern, url_schema, re.DOTALL)
        if not match:
            return _minimal_schema(name, description)

        raw_json = match.group(1) or match.group(2) or match.group(3)
        if raw_json is None:
            return _minimal_schema(name, description)

        body = json.loads(raw_json)
        if not isinstance(body, dict):
            return _minimal_schema(name, description)

        properties = {}
        for key, value in body.items():
            json_type = _infer_type(value)
            prop: dict = {"type": json_type, "description": key}
            if json_type == "array":
                prop["items"] = {}
            properties[key] = prop

        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": [],
                },
            },
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("parse_url_schema failed for title=%r: %s", title, exc)
        return _minimal_schema(name, description)


_EXAMPLE_VALUES = {
    "string": "example",
    "number": 0,
    "integer": 0,
    "boolean": True,
    "array": [],
    "object": {},
}


def pretty_print_schema(schema: dict) -> str:
    try:
        func = schema.get("function", {})
        name = func.get("name", "tool")
        parameters = func.get("parameters", {})
        properties = parameters.get("properties", {}) if isinstance(parameters, dict) else {}

        if not properties:
            return f'curl -X GET https://api.example.com/{name}'

        body = {}
        for key, prop in properties.items():
            prop_type = prop.get("type", "string") if isinstance(prop, dict) else "string"
            body[key] = _EXAMPLE_VALUES.get(prop_type, "example")

        json_body = json.dumps(body)
        return (
            f"curl -X POST https://api.example.com/{name}"
            f' -H "Content-Type: application/json"'
            f" -d '{json_body}'"
        )
    except Exception as exc:
        logger.warning("pretty_print_schema failed: %s", exc)
        return "curl -X GET https://api.example.com/tool"
