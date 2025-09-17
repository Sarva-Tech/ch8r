from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from core.models import Application, LLMModel

from core.permissions import HasAPIKeyPermission
from core.serializers import ApplicationRateLimitSerializer

class AppRateLimitView(APIView):
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]

    def post(self, request, application_uuid):
        app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        app.custom_model_rate_limit_per_minute = request.data.get("rate_per_minute")
        app.save()
        return Response(ApplicationRateLimitSerializer(app).data, status=status.HTTP_200_OK)
