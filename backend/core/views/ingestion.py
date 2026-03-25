from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from core.models import Application, LLMModel

from core.permissions import HasAPIKeyPermission
from core.tasks import process_kb

class IngestApplicationKBView(APIView):
    permission_classes = [permissions.IsAuthenticated | HasAPIKeyPermission]
    def post(self, request, application_uuid):
        app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        kbs = app.knowledge_bases.filter(status='pending')
        
        process_kb.delay([kb.id for kb in kbs])

        return Response({"message": "Ingestion completed."})
