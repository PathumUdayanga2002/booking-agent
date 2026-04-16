"""Qdrant vector database client."""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_qdrant_client: QdrantClient = None


async def init_qdrant():
    """Initialize Qdrant client and ensure collection exists."""
    global _qdrant_client
    try:
        # Initialize with API key if provided
        if settings.QDRANT_API_KEY:
            _qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
            logger.info(f"✓ Qdrant client initialized with API key")
        else:
            _qdrant_client = QdrantClient(settings.QDRANT_URL)
            logger.info(f"✓ Qdrant client initialized without API key")
        
        # Check if collection exists, if not create it
        try:
            _qdrant_client.get_collection(settings.QDRANT_COLLECTION_NAME)
            logger.info(
                f"✓ Qdrant collection exists: {settings.QDRANT_COLLECTION_NAME}"
            )
        except Exception:
            # Collection doesn't exist, create it
            _qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.EMBEDDINGS_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(
                f"✓ Qdrant collection created: {settings.QDRANT_COLLECTION_NAME}"
            )
        
        logger.info(f"✓ Qdrant connected: {settings.QDRANT_URL}")
        return _qdrant_client
    except Exception as e:
        logger.error(f"✗ Qdrant connection failed: {e}")
        raise


def get_qdrant_client() -> QdrantClient:
    """Get the Qdrant client instance."""
    if _qdrant_client is None:
        raise RuntimeError("Qdrant not initialized. Call init_qdrant() first.")
    return _qdrant_client
