"""Groq LLM client initialization."""
from groq import Groq
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize Groq client
try:
    groq_client = Groq(api_key=settings.GROQ_API_KEY)
    logger.info("✓ Groq LLM client initialized")
except Exception as e:
    logger.error(f"✗ Failed to initialize Groq client: {e}")
    raise
