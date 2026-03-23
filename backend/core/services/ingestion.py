from fastembed import SparseTextEmbedding
from qdrant_client.http.exceptions import UnexpectedResponse
import logging

from core.models import IngestedChunk
from core.models.llm_model import LLMModel
from core.llm_client import LLMClient
from core.qdrant import qdrant, COLLECTION_NAME
from qdrant_client.http.models import PointIdsList, PointStruct
from qdrant_client.models import Filter as ModelsFilter, FieldCondition as ModelsFieldCondition, \
    MatchValue as ModelsMatchValue
from qdrant_client.models import Prefetch, SparseVector
from core.services.ai_client_service import AIClientService
import uuid

logger = logging.getLogger(__name__)

_sparse_model = None

def _get_sparse_model():
    global _sparse_model
    if _sparse_model is None:
        logger.info("[ingestion] Loading sparse embedding model (Qdrant/bm25)...")
        _sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        logger.info("[ingestion] Sparse embedding model loaded.")
    return _sparse_model


def embed_text(text_chunks: list[str], app) -> list[list[float]]:
    ai_client_service = AIClientService()
    provider, model = ai_client_service.get_client_and_model(
        app=app,
        context='response',
        capability='embedding'
    )

    if not provider or not model:
        logger.error("[embed_text] No embedding provider available")
        return [[] for _ in text_chunks]

    try:
        return provider.embed(model, text_chunks)
    except Exception as e:
        logger.error(f"[embed_text] Embedding failed: {e}")
        return [[] for _ in text_chunks]

def embed_sparse(text_chunks: list[str]) -> list:
    sparse_embeddings = list(_get_sparse_model().embed(text_chunks))
    return [
        SparseVector(
            indices=embedding.indices.tolist(),
            values=embedding.values.tolist()
        ) for embedding in sparse_embeddings
    ]

def chunk_text(text: str, chunk_size=300, overlap=50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def get_chunks(query_text, app, top_k=5):
    dense_embeddings = embed_text(text_chunks=[query_text], app=app)
    if not dense_embeddings or not dense_embeddings[0]:
        print("[get_chunks] Warning: dense embedding empty, returning no context")
        return "No context available."

    dense_query = dense_embeddings[0]

    try:
        sparse_embeddings = list(_get_sparse_model().embed([query_text]))[0]
        sparse_query = SparseVector(
            indices=sparse_embeddings.indices.tolist(),
            values=sparse_embeddings.values.tolist()
        )
    except Exception as e:
        print(f"[get_chunks] Sparse embedding failed: {e}")
        sparse_query = None

    try:
        prefetch_list = [
            Prefetch(
                query=dense_query,
                using="dense",
                limit=top_k * 2,
                filter=ModelsFilter(
                    must=[ModelsFieldCondition(key="app_id", match=ModelsMatchValue(value=str(app.uuid)))]
                )
            )
        ]
        if sparse_query:
            prefetch_list.append(
                Prefetch(
                    query=sparse_query,
                    using="sparse",
                    limit=top_k * 2,
                    filter=ModelsFilter(
                        must=[ModelsFieldCondition(key="app_id", match=ModelsMatchValue(value=str(app.uuid)))]
                    )
                )
            )

        search_result = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            prefetch=prefetch_list,
            query=dense_query,
            using="dense",
            limit=top_k,
            with_payload=True
        )
    except UnexpectedResponse as e:
        print("[get_chunks] Qdrant query failed:", e)
        return "No context available."

    chunk_uuids = [point.id for point in search_result.points if point.score >= 0.3]

    if not chunk_uuids:
        return "No context available."

    chunks = IngestedChunk.objects.filter(uuid__in=chunk_uuids).order_by('chunk_index')
    context = "\n".join([chunk.content for chunk in chunks])
    return context

def ingest_kb(kb, app):
    content = kb.metadata.get('content', '')
    logger.info(f"[ingest_kb] Starting for kb={kb.uuid}, source_type={kb.source_type}, content_length={len(content)}")

    if not content:
        logger.warning(f"[ingest_kb] No content found for kb={kb.uuid}, skipping")
        return

    kb.status = 'processing'
    kb.save(update_fields=['status'])

    chunks = chunk_text(content)
    logger.info(f"[ingest_kb] Created {len(chunks)} chunks for kb={kb.uuid}")

    dense_embeddings = embed_text(text_chunks=chunks, app=app)
    non_empty = sum(1 for v in dense_embeddings if v)
    logger.info(f"[ingest_kb] Dense embeddings: {non_empty}/{len(chunks)} non-empty for kb={kb.uuid}")

    sparse_embeddings = embed_sparse(chunks)

    existing_chunks = IngestedChunk.objects.filter(knowledge_base=kb)
    qdrant_ids = [str(chunk.uuid) for chunk in existing_chunks]
    existing_chunks.delete()
    logger.info(f"[ingest_kb] Deleted {len(qdrant_ids)} existing chunks for kb={kb.uuid}")

    try:
        if qdrant_ids:
            qdrant.delete(
                collection_name=COLLECTION_NAME,
                points_selector=qdrant_ids
            )
    except Exception as e:
        logger.warning(f"Failed to delete vectors from Qdrant: {e}")

    upserted = 0
    for i, (chunk, dense_vector, sparse_vector) in enumerate(zip(chunks, dense_embeddings, sparse_embeddings)):
        if not dense_vector:
            logger.warning(f"[ingest_kb] Skipping chunk {i} for kb {kb.uuid}: empty dense embedding")
            continue

        chunk_uuid = uuid.uuid4()
        IngestedChunk.objects.create(
            uuid=chunk_uuid,
            knowledge_base=kb,
            content=chunk,
            chunk_index=i,
        )

        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=str(chunk_uuid),
                    vector={
                        "dense": dense_vector,
                        "sparse": SparseVector(
                            indices=list(sparse_vector.indices),
                            values=list(sparse_vector.values),
                        ),
                    },
                    payload={
                        "kb_id": str(kb.uuid),
                        "app_id": str(app.uuid),
                        "chunk_index": i,
                    }
                )
            ]
        )
        upserted += 1

    logger.info(f"[ingest_kb] Upserted {upserted}/{len(chunks)} chunks to Qdrant for kb={kb.uuid}")
    kb.status = 'completed'
    kb.save(update_fields=['status'])
    logger.info(f"[ingest_kb] Finished for kb={kb.uuid}, status=completed")

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
