import logging
import re
import traceback
from datetime import datetime, timezone

from core.integrations.integration_dispatcher import execute_tool_call

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(r"https?://[^\s'\"]+")


def _extract_url_from_schema(url_schema: str) -> str:
    if not url_schema:
        return ""
    match = _URL_PATTERN.search(url_schema)
    return match.group(0) if match else ""


def _get_tool_url(app_uuid: str, tool_name: str) -> str:
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
    def execute_all(
        self,
        app_uuid: str,
        tool_calls: list[dict],
    ) -> tuple[list[dict], list[dict]]:
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


def _monotonic_ns() -> int:
    import time
    return time.monotonic_ns()


def _elapsed_ms(start_ns: int) -> int:
    import time
    return int((time.monotonic_ns() - start_ns) / 1_000_000)
