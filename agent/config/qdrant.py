"""Qdrant client initialization and configuration."""
from qdrant_client import QdrantClient
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Qdrant client
try:
    # Initialize with API key if provided
    if settings.QDRANT_API_KEY:
        qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        logger.info(f"✓ Qdrant client initialized with API key: {settings.QDRANT_URL}")
    else:
        qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        logger.info(f"✓ Qdrant client initialized: {settings.QDRANT_URL}")
except Exception as e:
    logger.error(f"✗ Failed to initialize Qdrant client: {e}")
    raise
