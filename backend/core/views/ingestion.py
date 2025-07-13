from qdrant_client.http.exceptions import UnexpectedResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from core.models import IngestedChunk
from core.models import Application
from core.qdrant import qdrant, COLLECTION_NAME
import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text_chunks: list[str]) -> list[list[float]]:
    return model.encode(text_chunks).tolist()

def chunk_text(text: str, chunk_size=300, overlap=50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def get_context_chunks(query_text, app_uuid, top_k=5):
    query_vector = model.encode(query_text).tolist()

    try:
        search_result = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
            query_filter=Filter(
                must=[FieldCondition(key="app_id", match=MatchValue(value=str(app_uuid)))]
            ),
            with_payload=True
        )
    except UnexpectedResponse as e:
        print("Qdrant query failed:", str(e))
        return "No context available."


    chunk_uuids = [point.id for point in search_result.points if point.score >= 0.5]

    chunks = IngestedChunk.objects.filter(uuid__in=chunk_uuids).order_by('chunk_index')
    context = "\n\n".join([chunk.content for chunk in chunks])

    return context

class IngestApplicationKBView(APIView):
    def post(self, request, application_uuid):
        app = get_object_or_404(Application, uuid=application_uuid, owner=request.user)
        kbs = app.knowledge_bases.filter(source_type='text')

        for kb in kbs:
            content = kb.metadata.get('content', '')
            if not content:
                continue

            chunks = chunk_text(content)
            embeddings = embed_text(chunks)

            for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
                chunk_uuid = uuid.uuid4()
                IngestedChunk.objects.create(
                    uuid=chunk_uuid,
                    knowledge_base=kb,
                    content=chunk,
                    chunk_index=i,
                )

                qdrant.upsert(
                    collection_name=COLLECTION_NAME,
                    points=[{
                        "id": str(chunk_uuid),
                        "vector": vector,
                        "payload": {
                            "kb_id": str(kb.uuid),
                            "app_id": str(app.uuid),
                            "chunk_index": i
                        }
                    }]
                )

        return Response({"message": "Ingestion complete."})
