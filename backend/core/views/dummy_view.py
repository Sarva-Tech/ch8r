from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.access_control import token_has_access
from core.api_auth import APIKeyAuthentication
from core.models import Application


class DummyView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, application_uuid):
        try:
            app = Application.objects.get(uuid=application_uuid)
        except Application.DoesNotExist:
            raise NotFound("Application not found.")

        token = request.auth

        if not token_has_access(token, app, action="read"):
            raise PermissionDenied("You do not have permission to read this application.")

        return Response({
            "message": f"Token {token.name} is authorized to read app '{app.name}'!"
        })