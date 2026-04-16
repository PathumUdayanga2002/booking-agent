"""Services module."""
from .mongo_db import init_db, close_db, get_db, get_collection
from .qdrant_client import init_qdrant, get_qdrant_client
from .groq_client import init_groq, get_groq_client
from .embeddings_client import init_embeddings, get_embeddings_model, embed_text, embed_texts
from .express_api import get_express_client, ExpressAPIClient
from .vector_store import VectorStoreService, init_vector_store, KNOWLEDGE_BASE_COLLECTION

__all__ = [
    "init_db",
    "close_db",
    "get_db",
    "get_collection",
    "init_qdrant",
    "get_qdrant_client",
    "init_groq",
    "get_groq_client",
    "init_embeddings",
    "get_embeddings_model",
    "embed_text",
    "embed_texts",
    "get_express_client",
    "ExpressAPIClient",
    "VectorStoreService",
    "init_vector_store",
    "KNOWLEDGE_BASE_COLLECTION",
]
