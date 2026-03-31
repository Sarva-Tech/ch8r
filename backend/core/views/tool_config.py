import uuid as uuid_lib
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from core.models import Application, AppIntegration
from core.models.tool_config import ToolConfig
from core.integrations.registry import INTEGRATION_TOOLS


def get_app_integration(app_uuid, integration_uuid, user):
    application = get_object_or_404(Application, uuid=app_uuid, owner=user)
    return get_object_or_404(AppIntegration, uuid=integration_uuid, application=application)


def _serialize(tc, registry_tool=None):
    if tc.is_builtin:
        title = registry_tool["title"] if registry_tool else tc.tool_id
        description = registry_tool["description"] if registry_tool else ""
    else:
        title = tc.title
        description = tc.description
    return {
        "uuid": str(tc.uuid),
        "tool_id": tc.tool_id,
        "title": title,
        "description": description,
        "is_enabled": tc.is_enabled,
        "is_builtin": tc.is_builtin,
        "url_schema": tc.url_schema if not tc.is_builtin else None,
    }


class ToolConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, app_uuid, integration_uuid):
        ai = get_app_integration(app_uuid, integration_uuid, request.user)
        integration_key = f"{ai.integration.provider}_{ai.integration_type}"
        registry_tools = INTEGRATION_TOOLS.get(integration_key, {})

        existing = {tc.tool_id: tc for tc in ToolConfig.objects.filter(app_integration=ai)}

        result = []

        for tool in registry_tools.values():
            tool_id = f"{integration_key}:{tool['id']}"
            tc = existing.get(tool_id)
            if tc:
                result.append(_serialize(tc, tool))
            else:
                result.append({
                    "uuid": None,
                    "tool_id": tool_id,
                    "title": tool["title"],
                    "description": tool["description"],
                    "is_enabled": False,
                    "is_builtin": True,
                    "url_schema": None,
                })

        for tc in existing.values():
            if not tc.is_builtin:
                result.append(_serialize(tc))

        return Response(result)

    def post(self, request, app_uuid, integration_uuid):
        ai = get_app_integration(app_uuid, integration_uuid, request.user)

        title = str(request.data.get("title", "")).strip()
        description = str(request.data.get("description", "")).strip()
        url_schema = str(request.data.get("url_schema", "")).strip()

        errors = {}
        if not title:
            errors["title"] = "Required."
        if not description:
            errors["description"] = "Required."
        if not url_schema:
            errors["url_schema"] = "Required."
        if errors:
            return Response({"error": errors}, status=status.HTTP_400_BAD_REQUEST)

        tool_id = f"custom:{uuid_lib.uuid4().hex[:12]}"
        tc = ToolConfig.objects.create(
            app_integration=ai,
            tool_id=tool_id,
            is_builtin=False,
            title=title,
            description=description,
            url_schema=url_schema,
        )
        return Response(_serialize(tc), status=status.HTTP_201_CREATED)

    def patch(self, request, app_uuid, integration_uuid, tool_uuid):
        ai = get_app_integration(app_uuid, integration_uuid, request.user)
        tc = get_object_or_404(ToolConfig, uuid=tool_uuid, app_integration=ai)
        integration_key = f"{ai.integration.provider}_{ai.integration_type}"
        registry_tools = INTEGRATION_TOOLS.get(integration_key, {})

        if tc.is_builtin:
            is_enabled = request.data.get("is_enabled")
            if not isinstance(is_enabled, bool):
                return Response({"error": "'is_enabled' must be a boolean"}, status=status.HTTP_400_BAD_REQUEST)
            tc.is_enabled = is_enabled
            tc.save()
            tool_name = tc.tool_id.split(":", 1)[-1]
            registry_tool = registry_tools.get(tool_name)
            return Response(_serialize(tc, registry_tool))
        else:
            errors = {}
            for field in ("title", "description", "url_schema"):
                if field in request.data:
                    val = str(request.data[field]).strip()
                    if not val:
                        errors[field] = "Must not be blank."
                    else:
                        setattr(tc, field, val)
            if "is_enabled" in request.data:
                tc.is_enabled = bool(request.data["is_enabled"])
            if errors:
                return Response({"error": errors}, status=status.HTTP_400_BAD_REQUEST)
            tc.save()
            return Response(_serialize(tc))

    def delete(self, request, app_uuid, integration_uuid, tool_uuid):
        ai = get_app_integration(app_uuid, integration_uuid, request.user)
        tc = get_object_or_404(ToolConfig, uuid=tool_uuid, app_integration=ai)
        if tc.is_builtin:
            return Response({"error": "Cannot delete built-in tools."}, status=status.HTTP_400_BAD_REQUEST)
        tc.delete()
        return Response({"detail": "deleted"})
