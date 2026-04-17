import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api import health_router, chat_router
from config import get_logger, settings
from services.vector_store import init_vector_store

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("LangGraph Agent API starting")
    logger.info("env=%s host=%s port=%s", settings.FASTAPI_ENV, settings.FASTAPI_HOST, settings.FASTAPI_PORT)
    try:
        await init_vector_store()
        logger.info("Vector store initialized")
    except Exception as exc:
        logger.warning("Vector store init failed; knowledge retrieval will be unavailable: %s", exc)
    logger.info("=" * 60)
    yield
    logger.info("LangGraph Agent API shutting down")


app = FastAPI(
    title="LangGraph Booking Agent API",
    description="LangGraph-powered booking assistant service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.time()
    response = await call_next(request)
    duration = time.time() - started
    logger.info("[%s] %s -> %s (%.3fs)", request.method, request.url.path, response.status_code, duration)
    return response


app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {
        "message": "LangGraph Booking Agent API",
        "status": "ready",
        "health": "/api/health",
        "chat_ws": "/api/chat/ws/{user_id}",
    }
