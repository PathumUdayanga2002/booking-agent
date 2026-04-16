"""Express Backend API Client."""
import httpx
from typing import Dict, List, Optional, Any
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


class ExpressAPIClient:
    """Client for making requests to Express backend."""
    
    def __init__(self):
        self.base_url = f"http://{settings.EXPRESS_HOST}:{settings.EXPRESS_PORT}/api"
        self.client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self):
        """Initialize async HTTP client."""
        self.client = httpx.AsyncClient(timeout=10.0)
        logger.info(f"✓ Express API Client initialized: {self.base_url}")
    
    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            logger.info("✓ Express API Client closed")
    
    async def search_rooms(
        self,
        check_in: str,
        check_out: str,
        guests: int,
        room_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search available rooms.
        
        Args:
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            room_type: Optional room type filter
            
        Returns:
            List of available rooms with availability info
        """
        try:
            params = {
                "checkIn": check_in,
                "checkOut": check_out,
                "guests": guests,
            }
            if room_type:
                params["roomType"] = room_type
            
            logger.info(f"🔍 Searching rooms: {params}")
            
            response = await self.client.get(
                f"{self.base_url}/rooms/search",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract rooms array from response
            rooms = data.get("rooms", []) if isinstance(data, dict) else data
            logger.info(f"✓ Rooms search successful: Found {len(rooms)} available rooms")
            
            # Log room details for debugging
            for room in rooms:
                logger.info(f"  - {room.get('name', 'Unknown')} (Type: {room.get('type', 'N/A')}, Available: {room.get('availableUnits', 0)}/{room.get('totalUnits', 0)})")
            
            return rooms
        except Exception as e:
            logger.error(f"✗ Room search failed: {e}", exc_info=True)
            raise
    
    async def get_room(self, room_id: str) -> Dict[str, Any]:
        """Get room details."""
        try:
            response = await self.client.get(f"{self.base_url}/rooms/{room_id}")
            response.raise_for_status()
            logger.info(f"✓ Retrieved room {room_id}")
            return response.json()
        except Exception as e:
            logger.error(f"✗ Failed to get room {room_id}: {e}")
            raise
    
    async def create_booking(
        self,
        user_id: str,
        room_id: str,
        check_in: str,
        check_out: str,
        guests: int,
        total_price: float,
        token: str,
        guest_name: Optional[str] = None,
        guest_email: Optional[str] = None,
        guest_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new booking.
        
        Args:
            user_id: User ID
            room_id: Room ID to book
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            total_price: Total booking price
            token: JWT authentication token
            guest_name: Guest full name
            guest_email: Guest email address
            guest_phone: Guest phone number
            
        Returns:
            Created booking details
        """
        try:
            payload = {
                "roomId": room_id,
                "checkIn": check_in,
                "checkOut": check_out,
                "guests": guests,
                "totalPrice": total_price,
            }
            
            # Add guest details if provided
            if guest_name:
                payload["guestName"] = guest_name
            if guest_email:
                payload["guestEmail"] = guest_email
            if guest_phone:
                payload["guestPhone"] = guest_phone
            
            headers = {"Authorization": f"Bearer {token}"}
            
            logger.info(f"📝 Creating booking with payload: {payload}")
            
            response = await self.client.post(
                f"{self.base_url}/bookings",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            booking = response.json()
            logger.info(f"✓ Booking created: {booking.get('_id')}")
            return booking
        except Exception as e:
            logger.error(f"✗ Failed to create booking: {e}", exc_info=True)
            raise
    
    async def get_booking(
        self,
        booking_id: str,
        token: str,
    ) -> Dict[str, Any]:
        """Get booking details."""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get(
                f"{self.base_url}/bookings/{booking_id}",
                headers=headers,
            )
            response.raise_for_status()
            logger.info(f"✓ Retrieved booking {booking_id}")
            return response.json()
        except Exception as e:
            logger.error(f"✗ Failed to get booking {booking_id}: {e}")
            raise
    
    async def list_user_bookings(self, token: str) -> List[Dict[str, Any]]:
        """List user's bookings."""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.get(
                f"{self.base_url}/bookings/me",
                headers=headers,
            )
            response.raise_for_status()
            bookings = response.json()
            logger.info(f"✓ Retrieved {len(bookings)} user bookings")
            return bookings
        except Exception as e:
            logger.error(f"✗ Failed to list user bookings: {e}")
            raise
    
    async def cancel_booking(
        self,
        booking_id: str,
        token: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cancel a booking with verification."""
        try:
            payload = {"reason": reason or "User cancelled"}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"\n=== CANCEL_BOOKING API CLIENT ===")
            logger.info(f"🔗 URL: DELETE {self.base_url}/bookings/{booking_id}")
            logger.info(f"📦 Payload: {payload}")
            logger.info(f"🔐 Token present: {bool(token)}")
            
            # NOTE: httpx AsyncClient.delete() does not accept request body args
            # (data/json/content). Use .request("DELETE", ...) when sending JSON.
            response = await self.client.request(
                "DELETE",
                f"{self.base_url}/bookings/{booking_id}",
                json=payload,
                headers=headers,
            )
            
            logger.info(f"📥 Response status: {response.status_code}")
            logger.info(f"📥 Response body: {response.text[:500]}")
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✓ Cancel response: {result}")
            
            # Verify cancellation
            if result.get("success") and result.get("booking", {}).get("status") == "cancelled":
                logger.info(f"✓ Booking cancelled successfully: {booking_id}")
                logger.info(f"=== CANCEL_BOOKING API CLIENT - SUCCESS ===\n")
                return result
            else:
                logger.error(f"⚠️ Backend returned success but status not cancelled: {result}")
                return result
                
        except Exception as e:
            logger.error(f"✗ Failed to cancel booking {booking_id}: {type(e).__name__}: {str(e)}", exc_info=True)
            logger.error(f"=== CANCEL_BOOKING API CLIENT - FAILED ===\n")
            raise
    
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
        """Reschedule a booking."""
        try:
            payload: Dict[str, Any] = {
                # Express validator expects checkIn/checkOut keys.
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
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await self.client.put(
                f"{self.base_url}/bookings/{booking_id}",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            logger.info(f"✓ Booking rescheduled: {booking_id}")
            return response.json()
        except Exception as e:
            logger.error(f"✗ Failed to reschedule booking {booking_id}: {e}")
            raise
    
    async def get_available_dates(
        self,
        room_id: str,
        month: int,
        year: int,
    ) -> Dict[str, List[str]]:
        """Get available dates for a room."""
        try:
            response = await self.client.get(
                f"{self.base_url}/rooms/{room_id}/availability",
                params={"month": month, "year": year},
            )
            response.raise_for_status()
            logger.info(f"✓ Retrieved availability for room {room_id}")
            return response.json()
        except Exception as e:
            logger.error(f"✗ Failed to get availability: {e}")
            raise


# Global client instance
express_client: Optional[ExpressAPIClient] = None


async def get_express_client() -> ExpressAPIClient:
    """Get or create Express API client."""
    global express_client
    if express_client is None:
        express_client = ExpressAPIClient()
        await express_client.initialize()
    return express_client
