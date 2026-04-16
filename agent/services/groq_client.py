"""Groq LLM client wrapper."""
from groq import Groq
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_groq_client: Groq = None


def init_groq():
    """Initialize Groq client."""
    global _groq_client
    try:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("✓ Groq LLM client initialized")
        return _groq_client
    except Exception as e:
        logger.error(f"✗ Groq initialization failed: {e}")
        raise


def get_groq_client() -> Groq:
    """Get the Groq client instance."""
    if _groq_client is None:
        raise RuntimeError("Groq not initialized. Call init_groq() first.")
    return _groq_client
