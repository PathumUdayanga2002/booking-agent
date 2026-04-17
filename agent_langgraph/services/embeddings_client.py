from typing import Any, List, Optional

from config import get_logger, settings

logger = get_logger(__name__)

_model: Optional[Any] = None


async def init_embeddings() -> Any:
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:
            raise RuntimeError(
                "sentence-transformers is required for knowledge retrieval. Install requirements.txt in agent_langgraph."
            ) from exc

        _model = SentenceTransformer(settings.EMBEDDINGS_MODEL)
        logger.info("Embeddings model loaded: %s", settings.EMBEDDINGS_MODEL)
    return _model


def get_embeddings_model() -> Any:
    if _model is None:
        raise RuntimeError("Embeddings model not initialized. Call init_embeddings() first.")
    return _model


def embed_text(text: str) -> List[float]:
    model = get_embeddings_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()
