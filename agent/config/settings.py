"""
Configuration management for the FastAPI agent.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings from environment variables."""
    
    # FastAPI Configuration
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", 8000))
    FASTAPI_ENV: str = os.getenv("FASTAPI_ENV", "development")
    
    # Groq API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # MongoDB Configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "hotel_booking")
    MONGO_COLLECTION_CONVERSATIONS: str = os.getenv(
        "MONGO_COLLECTION_CONVERSATIONS", "agent_conversations"
    )
    
    # Qdrant Vector Database Configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION_NAME: str = os.getenv(
        "QDRANT_COLLECTION_NAME", "hotel_knowledge"
    )
    EMBEDDINGS_MODEL: str = os.getenv(
        "EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDINGS_DIMENSION: int = 384  # all-MiniLM-L6-v2 output dimension
    
    # Express Backend Configuration
    EXPRESS_HOST: str = os.getenv("EXPRESS_HOST", "localhost")
    EXPRESS_PORT: int = int(os.getenv("EXPRESS_PORT", 5000))
    EXPRESS_BACKEND_URL: str = os.getenv(
        "EXPRESS_BACKEND_URL", f"http://{EXPRESS_HOST}:{EXPRESS_PORT}"
    )
    EXPRESS_ADMIN_TOKEN: str = os.getenv("EXPRESS_ADMIN_TOKEN", "")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Document Processing Configuration
    CHUNK_SIZE: int = 300  # Token count per chunk
    CHUNK_OVERLAP: int = 50  # Token overlap between chunks
    
    # WebSocket Configuration
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
    
    def __repr__(self) -> str:
        return (
            f"<Settings "
            f"env={self.FASTAPI_ENV} "
            f"mongo={self.MONGO_DB_NAME} "
            f"qdrant={self.QDRANT_URL} "
            f"express={self.EXPRESS_BACKEND_URL}>"
        )


# Global settings instance
settings = Settings()
