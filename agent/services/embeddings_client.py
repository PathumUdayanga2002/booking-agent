"""HuggingFace embeddings client."""
from sentence_transformers import SentenceTransformer
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_embeddings_model: SentenceTransformer = None


async def init_embeddings():
    """Initialize HuggingFace embeddings model."""
    global _embeddings_model
    try:
        _embeddings_model = SentenceTransformer(settings.EMBEDDINGS_MODEL)
        logger.info(f"✓ Embeddings model loaded: {settings.EMBEDDINGS_MODEL}")
        return _embeddings_model
    except Exception as e:
        logger.error(f"✗ Embeddings model loading failed: {e}")
        raise


def get_embeddings_model() -> SentenceTransformer:
    """Get the embeddings model instance."""
    if _embeddings_model is None:
        raise RuntimeError(
            "Embeddings model not initialized. Call init_embeddings() first."
        )
    return _embeddings_model


def embed_text(text: str) -> list:
    """Embed a single text string."""
    model = get_embeddings_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()


def embed_texts(texts: list) -> list:
    """Embed multiple text strings."""
    model = get_embeddings_model()
    embeddings = model.encode(texts, convert_to_tensor=False)
    return [e.tolist() for e in embeddings]
