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

    async def _require_client(self) -> httpx.AsyncClient:
        if self.client is None:
            await self.initialize()
        if self.client is None:
            raise RuntimeError("Express API client initialization failed")
        return self.client

    async def search_rooms(self, check_in: str, check_out: str, guests: int) -> List[Dict[str, Any]]:
        client = await self._require_client()

        response = await client.get(
            f"{self.base_url}/rooms/search",
            params={"checkIn": check_in, "checkOut": check_out, "guests": guests},
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("rooms", []) if isinstance(payload, dict) else payload

    async def get_room(self, room_id: str) -> Dict[str, Any]:
        client = await self._require_client()

        response = await client.get(f"{self.base_url}/rooms/{room_id}")
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
        client = await self._require_client()

        response = await client.post(
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

    async def get_booking(self, booking_id: str, token: str) -> Dict[str, Any]:
        client = await self._require_client()

        response = await client.get(
            f"{self.base_url}/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        return response.json()

    async def list_user_bookings(self, token: str) -> List[Dict[str, Any]]:
        client = await self._require_client()

        response = await client.get(
            f"{self.base_url}/bookings/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, list) else payload.get("bookings", [])

    async def cancel_booking(self, booking_id: str, token: str, reason: Optional[str] = None) -> Dict[str, Any]:
        client = await self._require_client()

        response = await client.request(
            "DELETE",
            f"{self.base_url}/bookings/{booking_id}",
            json={"reason": reason or "Cancelled via LangGraph assistant"},
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    async def reschedule_booking(
        self,
        booking_id: str,
        new_check_in: str,
        new_check_out: str,
        token: str,
        new_guests: Optional[int] = None,
        new_guest_name: Optional[str] = None,
        new_guest_email: Optional[str] = None,
        new_guest_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        client = await self._require_client()

        payload: Dict[str, Any] = {
            "checkIn": new_check_in,
            "checkOut": new_check_out,
        }
        if new_guests is not None:
            payload["guests"] = new_guests
        if new_guest_name:
            payload["guestName"] = new_guest_name
        if new_guest_email:
            payload["guestEmail"] = new_guest_email
        if new_guest_phone:
            payload["guestPhone"] = new_guest_phone

        response = await client.put(
            f"{self.base_url}/bookings/{booking_id}",
            json=payload,
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
