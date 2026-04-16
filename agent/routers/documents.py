"""Document upload and knowledge base management router."""
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query, Header
from typing import Optional
import PyPDF2
import io
import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger import get_logger
from services.vector_store import VectorStoreService, KNOWLEDGE_BASE_COLLECTION, init_vector_store
from services.embeddings_client import embed_text
from config.settings import settings
from config.qdrant import qdrant_client
import jwt
from datetime import datetime

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

# Create uploads directory
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
logger.info(f"📁 Upload directory: {UPLOADS_DIR}")


def verify_admin_token(token: Optional[str] = None, authorization: Optional[str] = None) -> dict:
    """Verify JWT token and check admin role.
    
    Args:
        token: JWT token string from query
        authorization: Authorization header value
        
    Returns:
        Decoded token data
        
    Raises:
        HTTPException: If token is invalid or user not admin
    """
    # Extract token from Authorization header or query param
    if authorization:
        logger.info(f"🔐 Auth header received: {authorization[:20]}...")
        # Extract token from "Bearer <token>"
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
    
    if not token:
        logger.error("🔐 No token provided in header or query")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )
    
    logger.info(f"🔐 Verifying token: {token[:20]}...")
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        logger.info(f"🔐 Token decoded successfully. User: {payload.get('userId')}, Role: {payload.get('role')}")
        
        # Check admin role
        user_role = payload.get("role")
        if user_role != "admin":
            logger.error(f"🔐 User role is '{user_role}', not 'admin' - ACCESS DENIED")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Admin access required. Current role: {user_role}"
            )
        
        logger.info(f"✓ Admin token verified for user {payload.get('userId')}")
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.error(f"🔐 Token expired: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"🔐 Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Query("knowledge", description="Type: knowledge or policy"),
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """Upload and process PDF document to knowledge base.
    
    Args:
        file: PDF file to upload
        doc_type: Type of document (knowledge or policy)
        token: Admin JWT token (query param or header)
        authorization: Authorization header
        
    Returns:
        Upload result with document info
    """
    try:
        logger.info(f"📤 Upload request received for file: {file.filename}")
        logger.info(f"📤 Token param: {token[:20] if token else 'None'}...")
        logger.info(f"📤 Auth header: {authorization[:20] if authorization else 'None'}...")
        
        # Verify admin token
        payload = verify_admin_token(token, authorization)
        admin_id = payload.get("userId")
        
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are supported"
            )
        
        logger.info(f"📤 Processing PDF: {file.filename}")
        
        # Read PDF content
        pdf_content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        
        # Extract text from all pages
        full_text = ""
        for page_num, page in enumerate(pdf_reader.pages):
            text = page.extract_text()
            full_text += f"\n--- Page {page_num + 1} ---\n{text}"
        
        if not full_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF contains no readable text"
            )
        
        logger.info(f"✓ Extracted {len(full_text)} characters from PDF")
        
        # Save uploaded file to local storage
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = UPLOADS_DIR / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(pdf_content)
        logger.info(f"💾 Saved file to: {file_path}")
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_text(full_text)
        logger.info(f"✓ Split into {len(chunks)} chunks")
        
        # Ensure vector store collection exists
        await VectorStoreService.ensure_collection(KNOWLEDGE_BASE_COLLECTION)
        
        # Add chunks to vector store
        doc_id = file.filename.replace(".pdf", "")
        added_count = 0
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            metadata = {
                "doc_type": doc_type,
                "source": file.filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "uploaded_by": admin_id,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
            try:
                await VectorStoreService.add_document(
                    KNOWLEDGE_BASE_COLLECTION,
                    chunk_id,
                    chunk,
                    metadata
                )
                added_count += 1
            except Exception as e:
                logger.error(f"✗ Failed to add chunk {chunk_id}: {e}")
                continue
        
        logger.info(f"✓ Added {added_count}/{len(chunks)} chunks to vector store")
        
        return {
            "status": "success",
            "document": {
                "filename": file.filename,
                "doc_type": doc_type,
                "size_bytes": len(pdf_content),
                "pages": len(pdf_reader.pages),
                "chunks_created": len(chunks),
                "chunks_added": added_count
            },
            "message": f"Successfully processed {file.filename} with {added_count} chunks"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@router.get("/documents/list")
async def list_documents(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """List all uploaded documents (admin only).
    
    Args:
        token: Admin JWT token (query param or header)
        authorization: Authorization header
        
    Returns:
        List of documents
    """
    try:
        logger.info(f"📋 List documents request")
        
        # Verify admin token
        verify_admin_token(token, authorization)
        logger.info(f"✓ Admin verified")
        
        # Get all documents from collection
        try:
            documents = await VectorStoreService.get_all_documents(KNOWLEDGE_BASE_COLLECTION)
            logger.info(f"✓ Retrieved {len(documents)} documents")
        except Exception as collection_error:
            logger.error(f"✗ Error getting documents: {str(collection_error)}")
            raise
        
        # Get collection info for stats
        try:
            info = await VectorStoreService.get_collection_info(KNOWLEDGE_BASE_COLLECTION)
        except Exception as e:
            logger.warning(f"⚠ Could not get collection info: {str(e)}")
            info = {"points_count": len(documents)}
        
        logger.info(f"✓ Retrieved documents list - total documents: {len(documents)}, total vectors: {info.get('points_count', 0)}")
        
        return {
            "status": "success",
            "documents": documents,
            "total": info.get("points_count", 0),
            "collection": KNOWLEDGE_BASE_COLLECTION
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Failed to list documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents list: {str(e)}"
        )


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """Delete a document from knowledge base (admin only).
    
    Deletes:
    1. All vector chunks from Qdrant
    2. Local PDF file from uploads folder
    
    Args:
        doc_id: Document ID to delete (filename without .pdf)
        token: Admin JWT token (query param or header)
        authorization: Authorization header
        
    Returns:
        Deletion confirmation
    """
    try:
        logger.info(f"🗑️ Delete document request for: {doc_id}")
        
        # Verify admin token
        verify_admin_token(token, authorization)
        logger.info(f"✓ Admin verified")
        
        # Find and delete all vectors for this document from Qdrant
        try:
            # Search for all points with this document ID in metadata
            search_results = qdrant_client.scroll(
                collection_name=KNOWLEDGE_BASE_COLLECTION,
                limit=10000
            )
            
            points_to_delete = []
            for point in search_results[0]:
                source = point.payload.get("metadata", {}).get("source", "")
                # Match by filename or doc_id
                if doc_id.lower() in source.lower() or source.replace(".pdf", "").lower() == doc_id.lower():
                    points_to_delete.append(point.id)
            
            if points_to_delete:
                for point_id in points_to_delete:
                    qdrant_client.delete(
                        collection_name=KNOWLEDGE_BASE_COLLECTION,
                        points_selector=[point_id]
                    )
                logger.info(f"✓ Deleted {len(points_to_delete)} vectors from Qdrant")
            else:
                logger.warning(f"⚠ No vectors found for document: {doc_id}")
        
        except Exception as e:
            logger.error(f"✗ Error deleting from Qdrant: {str(e)}")
            raise
        
        # Delete local PDF file from uploads folder
        try:
            # Find the file in uploads directory
            upload_files = list(UPLOADS_DIR.glob(f"*{doc_id}*.pdf"))
            if upload_files:
                for file_path in upload_files:
                    file_path.unlink()  # Delete file
                    logger.info(f"✓ Deleted local file: {file_path}")
            else:
                logger.warning(f"⚠ No local file found for document: {doc_id}")
        
        except Exception as e:
            logger.error(f"✗ Error deleting local file: {str(e)}")
            # Don't raise - Qdrant deletion was successful
        
        logger.info(f"✓ Document deleted successfully: {doc_id}")
        
        return {
            "status": "success",
            "message": f"Document '{doc_id}' and all associated vectors deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Failed to delete document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.get("/documents/knowledge-base")
async def get_knowledge_base_info(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """Get knowledge base statistics.
    
    Args:
        token: Admin JWT token (query param or header)
        authorization: Authorization header
        
    Returns:
        Knowledge base info
    """
    try:
        # Verify admin token
        verify_admin_token(token, authorization)
        
        # Get collection info
        info = await VectorStoreService.get_collection_info(KNOWLEDGE_BASE_COLLECTION)
        
        logger.info(f"✓ Retrieved knowledge base info")
        
        return {
            "status": "success",
            "collection": KNOWLEDGE_BASE_COLLECTION,
            "info": info
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Failed to get knowledge base info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge base info"
        )


@router.delete("/documents/clear-knowledge-base")
async def clear_knowledge_base(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """Clear all documents from knowledge base (admin only).
    
    Args:
        token: Admin JWT token (query param or header)
        authorization: Authorization header
        
    Returns:
        Confirmation
    """
    try:
        # Verify admin token
        verify_admin_token(token, authorization)
        
        # Clear collection
        await VectorStoreService.clear_collection(KNOWLEDGE_BASE_COLLECTION)
        
        logger.info(f"✓ Cleared knowledge base")
        
        return {
            "status": "success",
            "message": "Knowledge base cleared successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Failed to clear knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear knowledge base"
        )


@router.post("/documents/init-vector-store")
async def initialize_vector_store(
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """Initialize vector store collections (admin only).
    
    Args:
        token: Admin JWT token (query param or header)
        authorization: Authorization header
        
    Returns:
        Initialization status
    """
    try:
        # Verify admin token
        verify_admin_token(token, authorization)
        
        # Initialize collections
        await init_vector_store()
        
        logger.info(f"✓ Vector store initialized")
        
        return {
            "status": "success",
            "message": "Vector store initialized successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Failed to initialize vector store: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize vector store"
        )
