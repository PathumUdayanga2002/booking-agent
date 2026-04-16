"""Pydantic models for request/response validation."""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """A single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(BaseModel):
    """Conversation history stored in MongoDB."""
    user_id: str
    messages: List[ConversationMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None


class DocumentChunk(BaseModel):
    """A chunk of a document with metadata."""
    id: Optional[str] = None  # UUID for Qdrant
    text: str
    source: str  # Document source (filename, URL, etc.)
    chunk_index: int  # Order of chunk in document
    vector: Optional[List[float]] = None  # Embedding vector


class DocumentUploadRequest(BaseModel):
    """Request for uploading a document."""
    filename: str
    content: str  # File content as string (for TXT/MD) or base64 (for PDF)
    file_type: str = "txt"  # txt, md, pdf


class ChatRequest(BaseModel):
    """Request for chat interaction."""
    user_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    user_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ToolCall(BaseModel):
    """Groq function calling schema."""
    name: str
    arguments: dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "0.1.0"
