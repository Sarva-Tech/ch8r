from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from core.models import Application
from sentence_transformers import SentenceTransformer

from core.services import ingest_kb

model = SentenceTransformer("all-MiniLM-L6-v2")

class IngestApplicationKBView(APIView):
    def post(self, request, application_uuid):
        app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        kbs = app.knowledge_bases.filter(status='pending')

        for kb in kbs:
            ingest_kb(kb, app)

        return Response({"message": "Ingestion completed."})
