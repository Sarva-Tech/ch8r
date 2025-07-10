from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Application


class DummyView(APIView):
#     # authentication_classes = [APIKeyAuthentication]
#     permission_classes = [HasAPIAccessPermission]
#     api_action = 'widget_chat'
#
    def get(self, request, application_uuid):
        return Response({
            "message": f"Authorized to read app!"
        })