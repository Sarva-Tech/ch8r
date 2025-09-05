from fastembed import SparseTextEmbedding
from qdrant_client.http.exceptions import UnexpectedResponse
import logging

from core.llm_client import LLMClient
from core.models import IngestedChunk, LLMModel
from core.qdrant import qdrant, COLLECTION_NAME
from qdrant_client.http.models import PointIdsList, PointStruct
from qdrant_client.models import Filter as ModelsFilter, FieldCondition as ModelsFieldCondition, \
    MatchValue as ModelsMatchValue
from qdrant_client.models import Prefetch, SparseVector
import uuid

logger = logging.getLogger(__name__)

sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")


def embed_text(text_chunks: list[str], app) -> list[list[float]]:
    embedding_model = app.get_model_by_type(LLMModel.ModelType.EMBEDDING)
    try:
        client = LLMClient(
            base_url=embedding_model.base_url,
            api_key=embedding_model.config,
        )
        response = client.embed(text_chunks, embedding_model.model_name)

        if not response:
            return [[] for _ in text_chunks]

        if isinstance(response[0], float):
            return [response]
        return response
    except Exception as e:
        logger.error(f"[embed_text] Embedding failed: {e}")
        return [[] for _ in text_chunks]

def embed_sparse(text_chunks: list[str]) -> list:
    sparse_embeddings = list(sparse_model.embed(text_chunks))
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
        sparse_embeddings = list(sparse_model.embed([query_text]))[0]
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

    if not content:
        return

    chunks = chunk_text(content)

    dense_embeddings = embed_text(text_chunks=chunks, app=app)

    sparse_embeddings = embed_sparse(chunks)

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

    for i, (chunk, dense_vector, sparse_vector) in enumerate(zip(chunks, dense_embeddings, sparse_embeddings)):
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