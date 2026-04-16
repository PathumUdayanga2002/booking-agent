"""FastAPI main application."""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from config import settings
from services import (
    init_db,
    close_db,
    init_qdrant,
    init_groq,
    init_embeddings,
)
from services.express_api import get_express_client, ExpressAPIClient
from services.vector_store import init_vector_store
from routers import health, chat, documents
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 FastAPI Agent Starting Up")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.FASTAPI_ENV}")
    logger.info(f"Server: {settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
    
    try:
        # Initialize all services
        logger.info("📡 Initializing services...")
        await init_db()
        await init_qdrant()
        init_groq()
        await init_embeddings()
        await get_express_client()
        await init_vector_store()
        logger.info("✓ All services initialized successfully")
    except Exception as e:
        logger.error(f"✗ Service initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("🛑 FastAPI Agent Shutting Down")
    logger.info("=" * 60)
    try:
        await close_db()
        # Close Express API client
        express_client = ExpressAPIClient()
        await express_client.close()
        logger.info("✓ Graceful shutdown completed")
    except Exception as e:
        logger.error(f"✗ Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="Hotel Booking Agent API",
    description="AI-powered hotel booking assistant with LangChain, Groq, and Qdrant",
    version="0.1.0",
    lifespan=lifespan,
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"📥 [{request.method}] {request.url.path}")
    if request.query_params:
        logger.info(f"   Query: {dict(request.query_params)}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"📤 [{request.method}] {request.url.path} -> {response.status_code} ({process_time:.3f}s)")
    
    return response


# Register routers
app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")

# Log registered routes
logger.info("=" * 60)
logger.info("📋 Registered API Routes:")
logger.info("=" * 60)
for route in app.routes:
    if hasattr(route, "path") and hasattr(route, "methods"):
        methods = ", ".join(sorted(route.methods)) if route.methods else "ANY"
        logger.info(f"  {methods:10s} {route.path}")
    if hasattr(route, "path") and "websocket" in str(route.__class__).lower():
        logger.info(f"  {'WS':10s} {route.path}")
logger.info("=" * 60)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Hotel Booking Agent API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )