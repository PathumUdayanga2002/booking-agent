"""Qdrant Vector Store Operations."""
from typing import List, Dict, Any, Optional
from qdrant_client.models import Distance, VectorParams, PointStruct
from datetime import datetime
from utils.logger import get_logger
from config.qdrant import qdrant_client
from services.embeddings_client import embed_text, get_embeddings_model

logger = get_logger(__name__)

# Collection names
KNOWLEDGE_BASE_COLLECTION = "hotel_knowledge"
CONVERSATION_COLLECTION = "conversations"


class VectorStoreService:
    """Service for Qdrant vector operations."""
    
    @staticmethod
    async def ensure_collection(
        collection_name: str,
        vector_size: int = 384,  # all-MiniLM-L6-v2 dimension
    ):
        """Ensure collection exists in Qdrant."""
        try:
            collections = qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_name not in collection_names:
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )
                logger.info(f"✓ Created Qdrant collection: {collection_name}")
            else:
                logger.info(f"✓ Collection already exists: {collection_name}")
        except Exception as e:
            logger.error(f"✗ Failed to ensure collection {collection_name}: {e}")
            raise
    
    @staticmethod
    async def add_document(
        collection_name: str,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add document to vector store."""
        try:
            vector = embed_text(text)
            
            payload = {
                "text": text,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
            }
            
            point = PointStruct(
                id=hash(doc_id) % (10**10),  # Convert to positive int
                vector=vector,
                payload=payload,
            )
            
            qdrant_client.upsert(
                collection_name=collection_name,
                points=[point],
            )
            logger.info(f"✓ Added document to {collection_name}: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"✗ Failed to add document to {collection_name}: {e}")
            raise
    
    @staticmethod
    async def search(
        collection_name: str,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """Search documents in vector store."""
        try:
            query_vector = embed_text(query)

            # Support both older and newer qdrant-client APIs.
            search_fn = getattr(qdrant_client, "search", None)
            if callable(search_fn):
                raw_results = search_fn(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                )
            else:
                query_points_fn = getattr(qdrant_client, "query_points", None)
                if not callable(query_points_fn):
                    raise RuntimeError("Qdrant client has neither search nor query_points API")

                query_response = query_points_fn(
                    collection_name=collection_name,
                    query=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                )

                query_response_any: Any = query_response
                if hasattr(query_response_any, "points"):
                    raw_results = query_response_any.points
                elif isinstance(query_response_any, tuple) and len(query_response_any) > 0:
                    raw_results = query_response_any[0]
                else:
                    raw_results = query_response_any

            if raw_results is None:
                results = []
            elif isinstance(raw_results, list):
                results = raw_results
            else:
                try:
                    raw_results_any: Any = raw_results
                    results = list(raw_results_any)
                except TypeError:
                    results = [raw_results]
            
            docs = []
            for result in results:
                item = result
                if isinstance(item, tuple) and len(item) > 0:
                    # Some client responses are tuples; first element is point-like.
                    item = item[0]

                payload = getattr(item, "payload", {}) or {}
                point_id = getattr(item, "id", None)
                score = getattr(item, "score", None)

                doc = {
                    "id": point_id,
                    "score": score,
                    "text": payload.get("text", ""),
                    "metadata": payload.get("metadata", {}),
                }
                docs.append(doc)
            
            logger.info(f"✓ Found {len(docs)} documents in {collection_name}")
            return docs
        except Exception as e:
            logger.error(f"✗ Search failed in {collection_name}: {e}")
            raise
    
    @staticmethod
    async def delete_document(
        collection_name: str,
        doc_id: str,
    ):
        """Delete document from vector store."""
        try:
            point_id = hash(doc_id) % (10**10)
            qdrant_client.delete(
                collection_name=collection_name,
                points_selector=[point_id],
            )
            logger.info(f"✓ Deleted document from {collection_name}: {doc_id}")
        except Exception as e:
            logger.error(f"✗ Failed to delete document from {collection_name}: {e}")
            raise
    
    @staticmethod
    async def get_collection_info(collection_name: str) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            logger.info(f"🔍 Getting collection info for: {collection_name}")
            collection_info = qdrant_client.get_collection(collection_name)
            logger.info(f"📊 Collection info retrieved: {collection_info}")
            
            info = {
                "name": collection_name,
                "points_count": collection_info.points_count if hasattr(collection_info, 'points_count') else 0,
                "vectors_count": getattr(collection_info, "vectors_count", 0),
            }
            logger.info(f"✓ Retrieved collection info: {info}")
            return info
        except Exception as e:
            logger.error(f"✗ Failed to get collection info: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_all_documents(collection_name: str, limit: int = 100) -> list:
        """Get all documents from collection."""
        try:
            logger.info(f"📚 Retrieving all documents from {collection_name}")
            
            documents = {}  # Use dict to group by source file
            scroll_result = qdrant_client.scroll(
                collection_name=collection_name,
                limit=limit
            )
            
            points = scroll_result[0]  # First element is list of points
            logger.info(f"📊 Retrieved {len(points)} points from collection")
            
            for point in points:
                payload = getattr(point, "payload", {}) or {}
                metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
                source = metadata.get("source", "unknown")
                doc_type = metadata.get("doc_type", "knowledge")
                
                # Group by source file
                if source not in documents:
                    documents[source] = {
                        "id": source.replace(".pdf", ""),
                        "filename": source,
                        "sourceType": doc_type,
                        "chunks": 0,
                        "createdAt": metadata.get("uploaded_at", ""),
                        "uploadedBy": metadata.get("uploaded_by", "admin"),
                    }
                
                # Increment chunk count
                documents[source]["chunks"] += 1
            
            # Remove duplicates and convert to list
            unique_docs = list(documents.values())
            logger.info(f"✓ Retrieved {len(unique_docs)} unique documents with {len(points)} total chunks")
            return unique_docs
        except Exception as e:
            logger.error(f"✗ Failed to get all documents: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def clear_collection(collection_name: str):
        """Clear all documents from collection."""
        try:
            # Compatibility-safe clear: recreate collection.
            qdrant_client.delete_collection(collection_name=collection_name)
            await VectorStoreService.ensure_collection(collection_name)
            logger.info(f"✓ Cleared collection: {collection_name}")
        except Exception as e:
            logger.error(f"✗ Failed to clear collection {collection_name}: {e}")
            raise


# Initialization
async def init_vector_store():
    """Initialize vector store collections."""
    try:
        await VectorStoreService.ensure_collection(KNOWLEDGE_BASE_COLLECTION)
        await VectorStoreService.ensure_collection(CONVERSATION_COLLECTION)
        logger.info("✓ Vector store initialized")
    except Exception as e:
        logger.error(f"✗ Vector store initialization failed: {e}")
        raise
