from typing import Any, Dict, List, Optional
import httpx

from config import get_logger, settings

logger = get_logger(__name__)


class ExpressAPIClient:
    def __init__(self):
        self.base_url = f"{settings.EXPRESS_BACKEND_URL}/api"
        self.client: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS)
            logger.info("Express API client initialized: %s", self.base_url)

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def search_rooms(self, check_in: str, check_out: str, guests: int) -> List[Dict[str, Any]]:
        if not self.client:
            await self.initialize()

        response = await self.client.get(
            f"{self.base_url}/rooms/search",
            params={"checkIn": check_in, "checkOut": check_out, "guests": guests},
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("rooms", []) if isinstance(payload, dict) else payload

    async def get_room(self, room_id: str) -> Dict[str, Any]:
        if not self.client:
            await self.initialize()

        response = await self.client.get(f"{self.base_url}/rooms/{room_id}")
        response.raise_for_status()
        return response.json()

    async def create_booking(
        self,
        token: str,
        room_id: str,
        check_in: str,
        check_out: str,
        guests: int,
        total_price: float,
        guest_name: str,
        guest_email: str,
        guest_phone: str,
    ) -> Dict[str, Any]:
        if not self.client:
            await self.initialize()

        response = await self.client.post(
            f"{self.base_url}/bookings",
            json={
                "roomId": room_id,
                "checkIn": check_in,
                "checkOut": check_out,
                "guests": guests,
                "totalPrice": total_price,
                "guestName": guest_name,
                "guestEmail": guest_email,
                "guestPhone": guest_phone,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()


_express_client: Optional[ExpressAPIClient] = None


async def get_express_client() -> ExpressAPIClient:
    global _express_client
    if _express_client is None:
        _express_client = ExpressAPIClient()
        await _express_client.initialize()
    return _express_client
