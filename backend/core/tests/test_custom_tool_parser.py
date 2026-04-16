import pytest

from core.integrations.custom_tool_parser import (
    _derive_name,
    _infer_type,
    _minimal_schema,
    parse_url_schema,
    pretty_print_schema,
)


@pytest.mark.unit
class TestDeriveName:
    def test_derive_name_simple(self):
        result = _derive_name("Get Weather")
        assert result == "get_weather"

    def test_derive_name_multiple_spaces(self):
        result = _derive_name("Get   User   Profile")
        assert result == "get_user_profile"

    def test_derive_name_special_characters(self):
        result = _derive_name("Get User@Profile!")
        assert result == "get_userprofile"

    def test_derive_name_numbers(self):
        result = _derive_name("API v2 Request")
        assert result == "api_v2_request"

    def test_derive_name_empty_string(self):
        result = _derive_name("")
        assert result == "custom_tool"

    def test_derive_name_only_special_chars(self):
        result = _derive_name("@#$%^&*()")
        assert result == "custom_tool"

    def test_derive_name_leading_trailing_spaces(self):
        result = _derive_name("  Get Weather  ")
        assert result == "get_weather"

    def test_derive_name_underscores_in_title(self):
        result = _derive_name("Get_User_Profile")
        assert result == "get_user_profile"

    def test_derive_name_multiple_underscores(self):
        result = _derive_name("Get___User___Profile")
        assert result == "get_user_profile"


@pytest.mark.unit
class TestInferType:
    def test_infer_type_string(self):
        """Test inferring type from string."""
        result = _infer_type("hello")
        assert result == "string"

    def test_infer_type_int(self):
        result = _infer_type(42)
        assert result == "number"

    def test_infer_type_float(self):
        result = _infer_type(3.14)
        assert result == "number"

    def test_infer_type_bool(self):
        result = _infer_type(True)
        assert result == "boolean"

    def test_infer_type_list(self):
        result = _infer_type([1, 2, 3])
        assert result == "array"

    def test_infer_type_dict(self):
        result = _infer_type({"key": "value"})
        assert result == "object"

    def test_infer_type_none(self):
        result = _infer_type(None)
        assert result == "string"

    def test_infer_type_unknown_type(self):
        class CustomType:
            pass
        result = _infer_type(CustomType())
        assert result == "string"


@pytest.mark.unit
class TestMinimalSchema:
    def test_minimal_schema_basic(self):
        result = _minimal_schema("get_weather", "Get current weather")
        assert result == {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }

    def test_minimal_schema_empty_description(self):
        result = _minimal_schema("tool_name", "")
        assert result["function"]["description"] == ""

    def test_minimal_schema_special_chars_in_name(self):
        result = _minimal_schema("tool-name", "description")
        assert result["function"]["name"] == "tool-name"


@pytest.mark.unit
class TestParseUrlSchema:
    def test_parse_url_schema_with_single_quotes(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '{"name": "John", "age": 30}'"""
        result = parse_url_schema("Get User", "Get user information", url_schema)

        assert result["type"] == "function"
        assert result["function"]["name"] == "get_user"
        assert result["function"]["description"] == "Get user information"
        assert "name" in result["function"]["parameters"]["properties"]
        assert "age" in result["function"]["parameters"]["properties"]
        assert result["function"]["parameters"]["properties"]["name"]["type"] == "string"
        assert result["function"]["parameters"]["properties"]["age"]["type"] == "number"

    def test_parse_url_schema_with_double_quotes(self):
        url_schema = '''curl -X POST https://api.example.com/endpoint --data "{\"city\": \"NYC\", \"temp\": 72.5}"'''
        result = parse_url_schema("Get Weather", "Get weather data", url_schema)

        assert result["function"]["name"] == "get_weather"
        assert result["function"]["description"] == "Get weather data"

    def test_parse_url_schema_with_unquoted_braces(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data {"product": "widget", "quantity": 10}"""
        result = parse_url_schema("Create Order", "Create a new order", url_schema)

        assert result["function"]["name"] == "create_order"
        assert "product" in result["function"]["parameters"]["properties"]
        assert "quantity" in result["function"]["parameters"]["properties"]

    def test_parse_url_schema_with_array_value(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '{"tags": ["tag1", "tag2"]}'"""
        result = parse_url_schema("Add Tags", "Add tags to item", url_schema)

        assert result["function"]["parameters"]["properties"]["tags"]["type"] == "array"
        assert "items" in result["function"]["parameters"]["properties"]["tags"]

    def test_parse_url_schema_with_object_value(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '{"metadata": {"key": "value"}}'"""
        result = parse_url_schema("Set Metadata", "Set item metadata", url_schema)

        assert result["function"]["parameters"]["properties"]["metadata"]["type"] == "object"

    def test_parse_url_schema_with_boolean_value(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '{"active": true, "deleted": false}'"""
        result = parse_url_schema("Update Status", "Update item status", url_schema)

        assert result["function"]["parameters"]["properties"]["active"]["type"] == "boolean"
        assert result["function"]["parameters"]["properties"]["deleted"]["type"] == "boolean"

    def test_parse_url_schema_with_null_value(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '{"optional": null}'"""
        result = parse_url_schema("Optional Field", "Test optional field", url_schema)

        assert result["function"]["parameters"]["properties"]["optional"]["type"] == "string"

    def test_parse_url_schema_no_data_flag(self):
        url_schema = """curl -X POST https://api.example.com/endpoint"""
        result = parse_url_schema("Simple Tool", "A simple tool", url_schema)

        assert result["function"]["name"] == "simple_tool"
        assert result["function"]["parameters"]["properties"] == {}

    def test_parse_url_schema_invalid_json(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '{invalid json}'"""
        result = parse_url_schema("Invalid Tool", "Tool with invalid JSON", url_schema)

        assert result["function"]["name"] == "invalid_tool"
        assert result["function"]["parameters"]["properties"] == {}

    def test_parse_url_schema_json_not_dict(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '["item1", "item2"]'"""
        result = parse_url_schema("Array Tool", "Tool with array", url_schema)

        assert result["function"]["name"] == "array_tool"
        assert result["function"]["parameters"]["properties"] == {}

    def test_parse_url_schema_multiline_json(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '{
            "name": "John",
            "age": 30
        }'"""
        result = parse_url_schema("Multiline Tool", "Tool with multiline JSON", url_schema)

        assert result["function"]["name"] == "multiline_tool"
        assert "name" in result["function"]["parameters"]["properties"]
        assert "age" in result["function"]["parameters"]["properties"]

    def test_parse_url_schema_escaped_quotes(self):
        url_schema = r"""curl -X POST https://api.example.com/endpoint --data '{"message": "Hello \"World\""}'"""
        result = parse_url_schema("Escaped Tool", "Tool with escaped quotes", url_schema)

        assert result["function"]["name"] == "escaped_tool"
        assert "message" in result["function"]["parameters"]["properties"]

    def test_parse_url_schema_empty_body(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '{}'"""
        result = parse_url_schema("Empty Tool", "Tool with empty body", url_schema)

        assert result["function"]["name"] == "empty_tool"
        assert result["function"]["parameters"]["properties"] == {}

    def test_parse_url_schema_complex_nested_structure(self):
        url_schema = """curl -X POST https://api.example.com/endpoint --data '{"user": {"name": "John", "roles": ["admin", "user"]}, "active": true}'"""
        result = parse_url_schema("Complex Tool", "Tool with complex structure", url_schema)

        assert result["function"]["name"] == "complex_tool"
        assert "user" in result["function"]["parameters"]["properties"]
        assert result["function"]["parameters"]["properties"]["user"]["type"] == "object"
        assert "active" in result["function"]["parameters"]["properties"]
        assert result["function"]["parameters"]["properties"]["active"]["type"] == "boolean"


@pytest.mark.unit
class TestPrettyPrintSchema:
    def test_pretty_print_schema_no_properties(self):
        schema = {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather data",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
        result = pretty_print_schema(schema)
        assert result == "curl -X GET https://api.example.com/get_weather"

    def test_pretty_print_schema_with_string_property(self):
        schema = {
            "type": "function",
            "function": {
                "name": "create_user",
                "description": "Create a user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "User name"},
                    },
                    "required": [],
                },
            },
        }
        result = pretty_print_schema(schema)
        assert "curl -X POST https://api.example.com/create_user" in result
        assert '"Content-Type: application/json"' in result
        assert "-d" in result
        assert '"name": "example"' in result

    def test_pretty_print_schema_with_number_property(self):
        schema = {
            "type": "function",
            "function": {
                "name": "set_age",
                "description": "Set user age",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "number", "description": "User age"},
                    },
                    "required": [],
                },
            },
        }
        result = pretty_print_schema(schema)
        assert '"age": 0' in result

    def test_pretty_print_schema_with_boolean_property(self):
        schema = {
            "type": "function",
            "function": {
                "name": "toggle_active",
                "description": "Toggle active status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "active": {"type": "boolean", "description": "Active status"},
                    },
                    "required": [],
                },
            },
        }
        result = pretty_print_schema(schema)
        assert '"active": true' in result

    def test_pretty_print_schema_with_array_property(self):
        schema = {
            "type": "function",
            "function": {
                "name": "add_tags",
                "description": "Add tags",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tags": {"type": "array", "description": "Tags list"},
                    },
                    "required": [],
                },
            },
        }
        result = pretty_print_schema(schema)
        assert '"tags": []' in result

    def test_pretty_print_schema_with_object_property(self):
        schema = {
            "type": "function",
            "function": {
                "name": "set_metadata",
                "description": "Set metadata",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metadata": {"type": "object", "description": "Metadata object"},
                    },
                    "required": [],
                },
            },
        }
        result = pretty_print_schema(schema)
        assert '"metadata": {}' in result

    def test_pretty_print_schema_multiple_properties(self):
        schema = {
            "type": "function",
            "function": {
                "name": "create_item",
                "description": "Create an item",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Item name"},
                        "count": {"type": "number", "description": "Item count"},
                        "active": {"type": "boolean", "description": "Active status"},
                    },
                    "required": [],
                },
            },
        }
        result = pretty_print_schema(schema)
        assert '"name": "example"' in result
        assert '"count": 0' in result
        assert '"active": true' in result

    def test_pretty_print_schema_missing_function_key(self):
        schema = {
            "type": "function",
        }
        result = pretty_print_schema(schema)
        assert result == "curl -X GET https://api.example.com/tool"

    def test_pretty_print_schema_missing_name(self):
        schema = {
            "type": "function",
            "function": {
                "description": "A tool",
            },
        }
        result = pretty_print_schema(schema)
        assert result == "curl -X GET https://api.example.com/tool"

    def test_pretty_print_schema_missing_parameters(self):
        schema = {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "My tool",
            },
        }
        result = pretty_print_schema(schema)
        assert result == "curl -X GET https://api.example.com/my_tool"

    def test_pretty_print_schema_parameters_not_dict(self):
        schema = {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "My tool",
                "parameters": "invalid",
            },
        }
        result = pretty_print_schema(schema)
        assert result == "curl -X GET https://api.example.com/my_tool"

    def test_pretty_print_schema_property_not_dict(self):
        schema = {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "My tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "field": "not a dict",
                    },
                    "required": [],
                },
            },
        }
        result = pretty_print_schema(schema)
        assert '"field": "example"' in result

    def test_pretty_print_schema_unknown_type(self):
        schema = {
            "type": "function",
            "function": {
                "name": "my_tool",
                "description": "My tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "unknown_type", "description": "A field"},
                    },
                    "required": [],
                },
            },
        }
        result = pretty_print_schema(schema)
        assert '"field": "example"' in result
