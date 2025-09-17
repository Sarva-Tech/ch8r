import os

from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from core.models import Application, ApplicationWidgetToken
from core.permissions import HasAPIKeyPermission

WIDGET_BASE_URL = os.environ.get("WIDGET_BASE_URL", "https://widget.ch8r.com")

class WidgetView(APIView):
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]

    def post(self, request, application_uuid):
        app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)

        token_obj = ApplicationWidgetToken.objects.filter(application=app).first()
        if token_obj:
            token_obj.delete()
            return Response({
                "status": "disabled",
                "token": None,
                "widget_url": None
            })
        else:
            new_token = ApplicationWidgetToken.objects.create(application=app)
            return Response({
                "status": "enabled",
                "token": new_token.key,
                "widget_url": f"{WIDGET_BASE_URL}/widget.html?token={new_token.key}&app_uuid={app.uuid}"
            })

    def get(self, request, application_uuid):
        app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)

        token_obj = app.widget_tokens.filter(is_active=True).order_by('-created_at').first()

        if not token_obj:
            return Response({
                "status": "inactive",
                "message": "No active widget token found."
            }, status=404)

        return Response({
            "status": "active" if token_obj.is_active else "inactive",
            "token": token_obj.key,
            "widget_url": f"{WIDGET_BASE_URL}/widget.html?token={token_obj.key}&app_uuid={app.uuid}"
        })