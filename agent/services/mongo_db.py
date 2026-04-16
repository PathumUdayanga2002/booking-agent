"""MongoDB database connection and utilities."""
import asyncio
from typing import Any
from pymongo import AsyncMongoClient
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_db_client: Any = None
_db: Any = None


async def init_db():
    """Initialize MongoDB connection."""
    global _db_client, _db
    try:
        _db_client = AsyncMongoClient(settings.MONGO_URI)
        _db = _db_client[settings.MONGO_DB_NAME]
        
        # Test connection
        await _db_client.admin.command("ping")
        logger.info(f"✓ MongoDB connected: {settings.MONGO_URI}")
        return _db
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {e}")
        raise


async def close_db():
    """Close MongoDB connection."""
    global _db_client
    if _db_client:
        _db_client.close()
        logger.info("✓ MongoDB connection closed")


def get_db() -> Any:
    """Get the database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


async def get_collection(collection_name: str):
    """Get a specific collection."""
    db = get_db()
    return db[collection_name]
