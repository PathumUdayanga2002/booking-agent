from config import get_logger, settings

logger = get_logger(__name__)

qdrant_client = None


try:
    from qdrant_client import QdrantClient

    if settings.QDRANT_API_KEY:
        qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    else:
        qdrant_client = QdrantClient(url=settings.QDRANT_URL)
    logger.info("Qdrant client initialized: %s", settings.QDRANT_URL)
except Exception as exc:
    logger.warning("Qdrant client unavailable: %s", exc)
