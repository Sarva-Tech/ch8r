from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from core.models import CustomToolRecord
from core.views.tool_config import get_app_integration


def _serialize_tool(tool):
    return {
        "uuid": str(tool.uuid),
        "title": tool.title,
        "description": tool.description,
        "url_schema": tool.url_schema,
        "is_enabled": tool.is_enabled,
    }


class CustomToolListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, app_uuid, integration_uuid):
        ai = get_app_integration(app_uuid, integration_uuid, request.user)
        tools = CustomToolRecord.objects.filter(app_integration=ai)
        return Response([_serialize_tool(t) for t in tools])

    def post(self, request, app_uuid, integration_uuid):
        ai = get_app_integration(app_uuid, integration_uuid, request.user)

        title = request.data.get("title", "")
        description = request.data.get("description", "")
        url_schema = request.data.get("url_schema", "")

        errors = {}
        if not title or not str(title).strip():
            errors["title"] = "This field is required and must not be blank."
        if not description or not str(description).strip():
            errors["description"] = "This field is required and must not be blank."
        if not url_schema or not str(url_schema).strip():
            errors["url_schema"] = "This field is required and must not be blank."

        if errors:
            return Response({"error": errors}, status=status.HTTP_400_BAD_REQUEST)

        tool = CustomToolRecord.objects.create(
            app_integration=ai,
            title=title,
            description=description,
            url_schema=url_schema,
        )
        return Response(_serialize_tool(tool), status=status.HTTP_201_CREATED)


class CustomToolDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, app_uuid, integration_uuid, uuid):
        ai = get_app_integration(app_uuid, integration_uuid, request.user)
        tool = get_object_or_404(CustomToolRecord, uuid=uuid, app_integration=ai)

        errors = {}
        updatable = ("title", "description", "url_schema", "is_enabled")

        for field in updatable:
            if field not in request.data:
                continue
            value = request.data[field]
            if field == "is_enabled":
                setattr(tool, field, value)
            else:
                if not value or not str(value).strip():
                    errors[field] = "This field must not be blank."
                else:
                    setattr(tool, field, value)

        if errors:
            return Response({"error": errors}, status=status.HTTP_400_BAD_REQUEST)

        tool.save()
        return Response(_serialize_tool(tool))

    def delete(self, request, app_uuid, integration_uuid, uuid):
        ai = get_app_integration(app_uuid, integration_uuid, request.user)
        tool = get_object_or_404(CustomToolRecord, uuid=uuid, app_integration=ai)
        tool.delete()
        return Response({"detail": "deleted"})
