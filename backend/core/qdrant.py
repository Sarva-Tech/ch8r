import os
import time

from dotenv import load_dotenv
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams
from qdrant_client.http.models import PayloadSchemaType

logger = logging.getLogger(__name__)
load_dotenv()

connect_to_local = os.getenv("CONNECT_TO_LOCAL_VECTOR_DB", "false").lower() == "true"

if connect_to_local:
    print('Connecting to local vector db')
    qdrant = QdrantClient(
        host=os.getenv("QDRANT_LOCAL_HOST", "localhost"),
        port=int(os.getenv("QDRANT_LOCAL_PORT", "6333")),
        prefer_grpc=True,
    )
else:
    print('Connecting to remote vector db')

    cloud_host = os.getenv("QDRANT_CLOUD_HOST")
    cloud_port = os.getenv("QDRANT_CLOUD_PORT", "6333")
    api_key = os.getenv("QDRANT_CLOUD_API_KEY")

    full_url = f"{cloud_host}:{cloud_port}"

    qdrant = QdrantClient(
        url=full_url,
        api_key=api_key,
        prefer_grpc=False,
    )

COLLECTION_NAME = "advq"

def init_qdrant(retries=3, delay=2):
    for attempt in range(retries):
        try:
            if not qdrant.collection_exists(COLLECTION_NAME):
                qdrant.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config={
                        "dense": VectorParams(size=3072, distance=Distance.COSINE),
                    },
                    sparse_vectors_config={
                        "sparse": SparseVectorParams()
                    }
                )
                ensure_payload_indexes()
            return
        except Exception as e:
            logger.error(f"[init_qdrant] Failed to initialize collection: {e}")
            time.sleep(delay)
    raise RuntimeError(f"Failed to initialize Qdrant collection after {retries} attempts")

def ensure_payload_indexes():
    for field in ["app_id", "kb_id"]:
        try:
            qdrant.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=PayloadSchemaType.KEYWORD
            )
        except Exception as e:
            print(f"Payload index for '{field}' may already exist or failed:", e)