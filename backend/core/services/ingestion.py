from qdrant_client.http.exceptions import UnexpectedResponse
import logging
from core.models import IngestedChunk
from sentence_transformers import SentenceTransformer
from core.qdrant import qdrant, COLLECTION_NAME
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, PointIdsList
import uuid

logger = logging.getLogger(__name__)
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

def get_chunks(query_text, app_uuid, top_k=5):
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
    context = "\n".join([chunk.content for chunk in chunks])

    return context

def ingest_kb(kb, app):
    content = kb.metadata.get('content', '')

    if not content:
        return

    chunks = chunk_text(content)
    embeddings = embed_text(chunks)

    existing_chunks = IngestedChunk.objects.filter(knowledge_base=kb)
    qdrant_ids = [str(chunk.uuid) for chunk in existing_chunks]
    existing_chunks.delete()

    try:
        if qdrant_ids:
            qdrant.delete(
                collection_name=COLLECTION_NAME,
                points=qdrant_ids
            )
    except Exception as e:
        logger.warning(f"Failed to delete vectors from Qdrant: {e}")

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

def delete_vectors_from_qdrant(ids):
    if not ids:
        return

    try:
        qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=PointIdsList(points=ids)
        )
    except Exception as e:
        logger.warning(f"Failed to delete vectors from Qdrant: {e}")
