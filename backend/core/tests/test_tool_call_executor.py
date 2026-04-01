"""
Property and unit tests for ToolCallExecutor.

# Feature: intelligent-chat-pipeline, Property 7: Tool_Call_Records contain all required fields
Validates: Requirements 4.1, 4.2, 4.3
"""
import pytest
from unittest.mock import patch, MagicMock

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from core.services.tool_call_executor import ToolCallExecutor

settings.register_profile("ci", max_examples=100)
settings.load_profile("ci")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {"name", "input_parameters", "url", "raw_arguments", "raw_result", "timestamp", "duration_ms"}


def _make_tool_call(name: str, args: dict, call_id: str = "tc_1") -> dict:
    return {"name": name, "args": args, "id": call_id}


def _fake_execute(app_uuid, tool_name, **kwargs):
    return {"ok": True, "tool": tool_name}


# ---------------------------------------------------------------------------
# Property 7: Tool_Call_Records contain all required fields
# ---------------------------------------------------------------------------

@given(
    tool_name=st.text(min_size=1, max_size=64, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="_")),
    args=st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_")),
        values=st.one_of(st.text(max_size=50), st.integers(), st.booleans()),
        max_size=5,
    ),
    call_id=st.text(min_size=1, max_size=32),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property7_all_required_fields_present_on_success(tool_name, args, call_id):
    """
    # Feature: intelligent-chat-pipeline, Property 7: Tool_Call_Records contain all required fields
    Validates: Requirements 4.1, 4.2, 4.3

    For any tool call that succeeds, the resulting Tool_Call_Record must contain
    all required fields: name, input_parameters, url, raw_arguments, raw_result,
    timestamp (ISO 8601), and duration_ms.
    """
    executor = ToolCallExecutor()
    tool_calls = [_make_tool_call(tool_name, args, call_id)]

    with patch("core.services.tool_call_executor.execute_tool_call", side_effect=_fake_execute), \
         patch("core.services.tool_call_executor._get_tool_url", return_value=""):
        records, messages = executor.execute_all("app-uuid", tool_calls)

    assert len(records) == 1
    record = records[0]

    # All required fields must be present
    for field in REQUIRED_FIELDS:
        assert field in record, f"Missing required field: {field}"

    # Validate field values
    assert record["name"] == tool_name
    assert record["input_parameters"] == args
    assert record["raw_arguments"] == args
    assert isinstance(record["timestamp"], str)
    assert "T" in record["timestamp"]  # ISO 8601 contains 'T'
    assert isinstance(record["duration_ms"], int)
    assert record["duration_ms"] >= 0


@given(
    tool_name=st.text(min_size=1, max_size=64, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="_")),
    args=st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_")),
        values=st.one_of(st.text(max_size=50), st.integers()),
        max_size=5,
    ),
    error_msg=st.text(min_size=1, max_size=100),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property7_error_field_present_on_exception(tool_name, args, error_msg):
    """
    # Feature: intelligent-chat-pipeline, Property 7: Tool_Call_Records contain all required fields
    Validates: Requirements 4.1, 4.2, 4.3

    When a tool call raises an exception, the record must still contain all required
    fields PLUS an 'error' key with the exception message and stack trace.
    """
    executor = ToolCallExecutor()
    tool_calls = [_make_tool_call(tool_name, args)]

    def _raise(*a, **kw):
        raise RuntimeError(error_msg)

    with patch("core.services.tool_call_executor.execute_tool_call", side_effect=_raise), \
         patch("core.services.tool_call_executor._get_tool_url", return_value=""):
        records, messages = executor.execute_all("app-uuid", tool_calls)

    assert len(records) == 1
    record = records[0]

    # All base required fields must still be present
    for field in REQUIRED_FIELDS:
        assert field in record, f"Missing required field after exception: {field}"

    # Error key must be present with message and traceback
    assert "error" in record
    assert "message" in record["error"]
    assert "traceback" in record["error"]
    assert error_msg in record["error"]["message"]
    assert isinstance(record["error"]["traceback"], str)
    assert len(record["error"]["traceback"]) > 0


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestToolCallExecutorUnit:
    def test_returns_tuple_of_two_lists(self):
        executor = ToolCallExecutor()
        with patch("core.services.tool_call_executor.execute_tool_call", return_value={"ok": True}), \
             patch("core.services.tool_call_executor._get_tool_url", return_value=""):
            result = executor.execute_all("app-uuid", [_make_tool_call("my_tool", {})])
        assert isinstance(result, tuple)
        assert len(result) == 2
        records, messages = result
        assert isinstance(records, list)
        assert isinstance(messages, list)

    def test_empty_tool_calls_returns_empty_lists(self):
        executor = ToolCallExecutor()
        records, messages = executor.execute_all("app-uuid", [])
        assert records == []
        assert messages == []

    def test_tool_result_message_format(self):
        executor = ToolCallExecutor()
        tool_call = _make_tool_call("search_tool", {"query": "hello"}, call_id="call_abc")
        with patch("core.services.tool_call_executor.execute_tool_call", return_value={"results": []}), \
             patch("core.services.tool_call_executor._get_tool_url", return_value=""):
            _, messages = executor.execute_all("app-uuid", [tool_call])

        assert len(messages) == 1
        msg = messages[0]
        assert msg["role"] == "tool"
        assert msg["tool_call_id"] == "call_abc"
        assert msg["name"] == "search_tool"
        assert "content" in msg

    def test_continues_after_failed_tool_call(self):
        """Requirement 6.4: continue processing remaining tool calls when one fails."""
        executor = ToolCallExecutor()
        tool_calls = [
            _make_tool_call("failing_tool", {}, "id_1"),
            _make_tool_call("ok_tool", {}, "id_2"),
        ]

        call_count = 0

        def _side_effect(app_uuid, tool_name, **kwargs):
            nonlocal call_count
            call_count += 1
            if tool_name == "failing_tool":
                raise ValueError("tool failed")
            return {"success": True}

        with patch("core.services.tool_call_executor.execute_tool_call", side_effect=_side_effect), \
             patch("core.services.tool_call_executor._get_tool_url", return_value=""):
            records, messages = executor.execute_all("app-uuid", tool_calls)

        assert call_count == 2, "Both tools should have been attempted"
        assert len(records) == 2
        assert len(messages) == 2

        # First record has error
        assert "error" in records[0]
        # Second record has no error
        assert "error" not in records[1]
        assert records[1]["raw_result"] == {"success": True}

    def test_timestamp_is_iso8601(self):
        from datetime import datetime
        executor = ToolCallExecutor()
        with patch("core.services.tool_call_executor.execute_tool_call", return_value={}), \
             patch("core.services.tool_call_executor._get_tool_url", return_value=""):
            records, _ = executor.execute_all("app-uuid", [_make_tool_call("t", {})])

        ts = records[0]["timestamp"]
        # Should parse as ISO 8601 datetime
        parsed = datetime.fromisoformat(ts)
        assert parsed is not None

    def test_duration_ms_is_non_negative_integer(self):
        executor = ToolCallExecutor()
        with patch("core.services.tool_call_executor.execute_tool_call", return_value={}), \
             patch("core.services.tool_call_executor._get_tool_url", return_value=""):
            records, _ = executor.execute_all("app-uuid", [_make_tool_call("t", {})])

        assert isinstance(records[0]["duration_ms"], int)
        assert records[0]["duration_ms"] >= 0

    def test_error_content_in_tool_result_message(self):
        executor = ToolCallExecutor()
        with patch("core.services.tool_call_executor.execute_tool_call", side_effect=RuntimeError("boom")), \
             patch("core.services.tool_call_executor._get_tool_url", return_value=""):
            _, messages = executor.execute_all("app-uuid", [_make_tool_call("t", {}, "id_x")])

        assert "Error:" in messages[0]["content"]
        assert "boom" in messages[0]["content"]

    def test_multiple_tool_calls_all_recorded(self):
        executor = ToolCallExecutor()
        tool_calls = [_make_tool_call(f"tool_{i}", {"n": i}, f"id_{i}") for i in range(5)]
        with patch("core.services.tool_call_executor.execute_tool_call", return_value={"ok": True}), \
             patch("core.services.tool_call_executor._get_tool_url", return_value=""):
            records, messages = executor.execute_all("app-uuid", tool_calls)

        assert len(records) == 5
        assert len(messages) == 5
        for i, record in enumerate(records):
            assert record["name"] == f"tool_{i}"
