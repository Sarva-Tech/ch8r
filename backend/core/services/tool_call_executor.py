"""
ToolCallExecutor service.

Encapsulates tool execution and Tool_Call_Record construction for the
intelligent chat pipeline.

Requirements: 4.1, 4.2, 4.3, 6.4
"""
import logging
import re
import traceback
from datetime import datetime, timezone

from core.integrations.integration_dispatcher import execute_tool_call

logger = logging.getLogger(__name__)

# Regex to extract the URL from a curl-style url_schema string.
# Matches the first http(s) URL that appears before any flags like -H, -d, --data.
_URL_PATTERN = re.compile(r"https?://[^\s'\"]+")


def _extract_url_from_schema(url_schema: str) -> str:
    """Return the first URL found in a curl url_schema string, or empty string."""
    if not url_schema:
        return ""
    match = _URL_PATTERN.search(url_schema)
    return match.group(0) if match else ""


def _get_tool_url(app_uuid: str, tool_name: str) -> str:
    """
    Best-effort URL extraction for a tool.

    For custom (non-builtin) tools the URL is stored in ToolConfig.url_schema.
    For built-in integration tools the URL is constructed dynamically inside the
    handler, so we return an empty string rather than guessing.
    """
    try:
        from core.models import AppIntegration, ToolConfig  # local import to avoid circular deps

        for ai in AppIntegration.objects.filter(
            application__uuid=app_uuid, is_active=True
        ).select_related("integration"):
            tc = ToolConfig.objects.filter(
                app_integration=ai,
                is_builtin=False,
                is_enabled=True,
            ).first()
            if tc and tc.url_schema:
                # Derive the tool name the same way parse_url_schema does.
                from core.integrations.custom_tool_parser import _derive_name
                if _derive_name(tc.title) == tool_name:
                    return _extract_url_from_schema(tc.url_schema)
    except Exception as exc:  # noqa: BLE001
        logger.debug("_get_tool_url: could not resolve URL for tool=%r: %s", tool_name, exc)
    return ""


class ToolCallExecutor:
    """
    Executes a batch of tool calls and returns structured records plus
    role=tool messages ready to append to the LLM conversation.
    """

    def execute_all(
        self,
        app_uuid: str,
        tool_calls: list[dict],
    ) -> tuple[list[dict], list[dict]]:
        """
        Execute every tool call in *tool_calls* and return:

        - ``tool_call_records``: list of Tool_Call_Record dicts for metadata storage.
        - ``tool_result_messages``: list of ``{"role": "tool", ...}`` dicts to append
          to the LLM conversation.

        Each element of *tool_calls* must have the shape::

            {"name": str, "args": dict, "id": str}

        Processing continues even when an individual tool call raises an exception;
        the error is captured in the record and the loop moves on (Requirement 6.4).
        """
        tool_call_records: list[dict] = []
        tool_result_messages: list[dict] = []

        for tool_call in tool_calls:
            name = tool_call.get("name", "")
            args = tool_call.get("args") or {}
            call_id = tool_call.get("id", "")

            timestamp = datetime.now(tz=timezone.utc).isoformat()
            start_ns = _monotonic_ns()

            record: dict = {
                "name": name,
                "input_parameters": args,
                "url": _get_tool_url(app_uuid, name),
                "raw_arguments": args,
                "raw_result": None,
                "timestamp": timestamp,
                "duration_ms": 0,
            }

            try:
                result = execute_tool_call(app_uuid, name, **args)
                duration_ms = _elapsed_ms(start_ns)

                record["raw_result"] = result
                record["duration_ms"] = duration_ms

                logger.info(
                    "[ToolCallExecutor] Tool executed | name=%s duration_ms=%d",
                    name, duration_ms,
                )

                content = str(result)

            except Exception as exc:  # noqa: BLE001
                duration_ms = _elapsed_ms(start_ns)
                tb = traceback.format_exc()

                record["duration_ms"] = duration_ms
                record["error"] = {
                    "message": str(exc),
                    "traceback": tb,
                }

                logger.error(
                    "[ToolCallExecutor] Tool call failed | name=%s error=%s",
                    name, exc, exc_info=False,
                )

                content = f"Error: {exc}"

            tool_call_records.append(record)
            tool_result_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": name,
                    "content": content,
                }
            )

        return tool_call_records, tool_result_messages


# ---------------------------------------------------------------------------
# Timing helpers
# ---------------------------------------------------------------------------

def _monotonic_ns() -> int:
    """Return current monotonic time in nanoseconds."""
    import time
    return time.monotonic_ns()


def _elapsed_ms(start_ns: int) -> int:
    """Return elapsed milliseconds since *start_ns*."""
    import time
    return int((time.monotonic_ns() - start_ns) / 1_000_000)
