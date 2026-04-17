from typing import Any, Dict, List, Optional
import httpx

from config import get_logger, settings

logger = get_logger(__name__)


class ConversationStorageService:
    def __init__(self):
        self.api_base = f"{settings.EXPRESS_BACKEND_URL}/api"
        self.timeout = settings.HTTP_TIMEOUT_SECONDS

    async def save_message(self, user_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/conversations/save",
                    json={
                        "userId": user_id,
                        "role": role,
                        "content": content,
                        "metadata": metadata or {},
                    },
                )
                return response.status_code in (200, 201)
        except Exception as exc:
            logger.warning("Conversation save failed for user %s: %s", user_id, exc)
            return False

    async def get_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_base}/conversations/history/{user_id}",
                    params={"limit": limit},
                )
                if response.status_code != 200:
                    return []
                payload = response.json()
                if isinstance(payload, list):
                    return payload
                return payload.get("data") or payload.get("messages") or []
        except Exception as exc:
            logger.warning("Conversation history load failed for user %s: %s", user_id, exc)
            return []


_storage_service: Optional[ConversationStorageService] = None


def get_storage_service() -> ConversationStorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = ConversationStorageService()
    return _storage_service
