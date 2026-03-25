from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Application
from core.permissions import HasAPIKeyPermission


class DummyView(APIView):
    permission_classes = [IsAuthenticated | HasAPIKeyPermission]
    def get(self, request, application_uuid):
        return Response({
            "message": f"Authorized to read app!"
        })