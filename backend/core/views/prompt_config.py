from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models.application import Application
from core.serializers.prompt_config import PromptConfigSerializer


class PromptConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, app_uuid):
        app = get_object_or_404(Application, uuid=app_uuid, owner=request.user)
        return Response(app.get_prompt_config())

    def patch(self, request, app_uuid):
        app = get_object_or_404(Application, uuid=app_uuid, owner=request.user)
        serializer = PromptConfigSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        app.prompt_config = {**app.get_prompt_config(), **serializer.validated_data}
        app.save()
        return Response(app.get_prompt_config())
