from datetime import datetime
from typing import Any, Dict, List

try:
    from qdrant_client.models import Distance, VectorParams
except Exception:
    Distance = None
    VectorParams = None

from config import get_logger, settings
from config.qdrant import qdrant_client
from services.embeddings_client import embed_text, init_embeddings

logger = get_logger(__name__)

KNOWLEDGE_BASE_COLLECTION = settings.QDRANT_COLLECTION_NAME


class VectorStoreService:
    @staticmethod
    async def ensure_collection(collection_name: str, vector_size: int = settings.EMBEDDINGS_DIMENSION):
        if qdrant_client is None or Distance is None or VectorParams is None:
            raise RuntimeError("Qdrant dependencies are not available")
        collections = qdrant_client.get_collections()
        names = [c.name for c in collections.collections]
        if collection_name not in names:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection: %s", collection_name)

    @staticmethod
    async def search(
        collection_name: str,
        query: str,
        limit: int = 8,
        score_threshold: float = 0.15,
    ) -> List[Dict[str, Any]]:
        if qdrant_client is None:
            raise RuntimeError("Qdrant client is not initialized")
        query_vector = embed_text(query)

        search_fn = getattr(qdrant_client, "search", None)
        if callable(search_fn):
            raw_results = search_fn(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
        else:
            query_points_fn = getattr(qdrant_client, "query_points", None)
            if not callable(query_points_fn):
                raise RuntimeError("Qdrant client has neither search nor query_points API")

            query_response = query_points_fn(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
            if hasattr(query_response, "points"):
                raw_results = query_response.points
            elif isinstance(query_response, tuple) and len(query_response) > 0:
                raw_results = query_response[0]
            else:
                raw_results = query_response

        if raw_results is None:
            results = []
        elif isinstance(raw_results, list):
            results = raw_results
        else:
            try:
                results = list(raw_results)
            except TypeError:
                results = [raw_results]

        docs: List[Dict[str, Any]] = []
        for item in results:
            point = item[0] if isinstance(item, tuple) and len(item) > 0 else item
            payload = getattr(point, "payload", {}) or {}
            docs.append(
                {
                    "id": getattr(point, "id", None),
                    "score": getattr(point, "score", None),
                    "text": payload.get("text", ""),
                    "metadata": payload.get("metadata", {}),
                    "created_at": payload.get("created_at", datetime.utcnow().isoformat()),
                }
            )
        return docs


async def init_vector_store() -> None:
    await init_embeddings()
    await VectorStoreService.ensure_collection(KNOWLEDGE_BASE_COLLECTION)
