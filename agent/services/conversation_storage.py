"""Service for persisting conversation history to backend MongoDB."""
import httpx
import json
from typing import List, Dict, Optional
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

class ConversationStorageService:
    """Handle conversation persistence via backend API."""
    
    def __init__(self):
        self.backend_url = settings.EXPRESS_BACKEND_URL
        self.api_base = f"{self.backend_url}/api"
        self.timeout = 10
    
    async def save_message(
        self,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Save message to backend conversation history.
        
        Args:
            user_id: User ID from JWT
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata (tool calls, etc.)
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            payload = {
                "userId": user_id,
                "role": role,
                "content": content,
                "metadata": metadata or {}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/conversations/save",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200 or response.status_code == 201:
                    logger.info(f"✓ Message saved for {user_id} ({role})")
                    return True
                else:
                    logger.warning(f"✗ Failed to save message: {response.status_code}")
                    return False
                    
        except httpx.TimeoutException:
            logger.error("✗ Timeout saving message to backend")
            return False
        except Exception as e:
            logger.error(f"✗ Error saving message: {str(e)}")
            # Don't raise - allow chat to continue even if saving fails
            return False
    
    async def get_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Retrieve conversation history for a user.
        
        Args:
            user_id: User ID from JWT
            limit: Max messages to retrieve
            
        Returns:
            List of messages [{role, content, createdAt, ...}, ...]
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/conversations/history/{user_id}",
                    params={"limit": limit},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data if isinstance(data, list) else data.get("messages", [])
                    logger.info(f"✓ Retrieved {len(messages)} messages for {user_id}")
                    return messages
                else:
                    logger.warning(f"✗ Failed to retrieve history: {response.status_code}")
                    return []
                    
        except httpx.TimeoutException:
            logger.error("✗ Timeout retrieving history from backend")
            return []
        except Exception as e:
            logger.error(f"✗ Error retrieving history: {str(e)}")
            # Don't raise - allow chat to start with empty history
            return []
    
    async def clear_history(self, user_id: str) -> bool:
        """Clear all conversation history for a user.
        
        Args:
            user_id: User ID from JWT
            
        Returns:
            True if cleared successfully
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.api_base}/conversations/history/{user_id}",
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"✓ History cleared for {user_id}")
                    return True
                else:
                    logger.warning(f"✗ Failed to clear history: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"✗ Error clearing history: {str(e)}")
            return False


# Singleton instance
_storage_service: Optional[ConversationStorageService] = None


def get_storage_service() -> ConversationStorageService:
    """Get or create conversation storage service."""
    global _storage_service
    if _storage_service is None:
        _storage_service = ConversationStorageService()
    return _storage_service
