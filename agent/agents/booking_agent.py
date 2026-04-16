"""LangChain Booking Agent with Groq LLM and LangGraph."""
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from langgraph.checkpoint.memory import MemorySaver
from utils.logger import get_logger
from config.groq import groq_client
from config.settings import settings
from services.express_api import get_express_client
from services.vector_store import VectorStoreService, KNOWLEDGE_BASE_COLLECTION
from services.conversation_storage import get_storage_service
from agents.tools import GROQ_TOOLS

logger = get_logger(__name__)


class BookingAgent:
    """AI Agent for hotel booking automation using Groq LLM and LangGraph."""
    
    def __init__(self, user_id: str, token: str):
        """Initialize booking agent for a user.
        
        Args:
            user_id: User ID from JWT token
            token: JWT authentication token
        """
        self.user_id = user_id
        self.token = token
        self.memory = MemorySaver()  # LangGraph memory checkpointer
        self.conversation_history: List[Dict[str, Any]] = []
        self.storage_service = get_storage_service()  # For persisting conversations
        self.flow_state: Dict[str, Any] = {
            "intent": None,
            "stage": None,
            "slots": {},
        }

    
    async def initialize(self):
        """Initialize agent with LangGraph memory and load conversation history."""
        try:
            # LangGraph memory checkpointer is already initialized in __init__
            # Load previous conversation history from MongoDB
            history_messages = await self.storage_service.get_history(
                user_id=self.user_id,
                limit=50
            )
            
            # Reconstruct conversation history (as list of dicts with role and content)
            if history_messages:
                for msg in history_messages:
                    self.conversation_history.append({
                        "role": msg.get("role"),
                        "content": msg.get("content")
                    })
                logger.info(f"✓ Loaded {len(history_messages)} previous messages for user: {self.user_id}")
            else:
                logger.info(f"✓ No previous conversation history for user: {self.user_id}")
            
            logger.info(f"✓ Agent initialized for user: {self.user_id}")
        except Exception as e:
            logger.error(f"✗ Agent initialization failed: {e}", exc_info=True)
            # Don't raise - allow agent to continue with empty history
            pass
    
    async def process_message(self, user_message: str) -> str:
        """Process user message and generate response with tool calling.
        
        Args:
            user_message: User's input message
            
        Returns:
            Agent's response string
        """
        try:
            # Normalize user input to help Groq understand better
            normalized_message = self._normalize_user_input(user_message)
            if normalized_message != user_message:
                logger.info(f"📝 Normalized input: '{user_message}' → '{normalized_message}'")
            
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": normalized_message
            })
            
            # Save user message to backend
            await self.storage_service.save_message(
                user_id=self.user_id,
                role="user",
                content=user_message  # Save original, not normalized
            )

            # Handle critical booking workflows deterministically to avoid hallucinations.
            structured_response = await self._handle_structured_flow(normalized_message)
            if structured_response is not None:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": structured_response
                })
                await self.storage_service.save_message(
                    user_id=self.user_id,
                    role="assistant",
                    content=structured_response
                )
                logger.info(
                    f"✓ Structured flow handled for user {self.user_id}: {user_message[:50]}... -> {structured_response[:50]}..."
                )
                return structured_response
            
            # Get agent response with tool handling
            response = await self._get_agent_response()
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Save assistant response to backend
            await self.storage_service.save_message(
                user_id=self.user_id,
                role="assistant",
                content=response
            )
            
            logger.info(f"✓ Message processed and saved for user {self.user_id}: {user_message[:50]}... -> {response[:50]}...")
            return response
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"✗ Message processing failed: {e}", exc_info=True)
            
            # Provide context-aware error messages based on user intent
            user_message_lower = user_message.lower()
            
            # Check if user is trying to cancel/reschedule
            if any(word in user_message_lower for word in ["cancel", "reschedule", "change", "modify", "update"]):
                return "To cancel or reschedule your booking, I need your booking ID. It's in the format like 'BKG-PATHUM-ABC123'. Do you have your booking ID?"
            
            # Check if user is trying to book
            elif any(word in user_message_lower for word in ["book", "search", "find", "available", "room"]):
                return "I need to clarify some information. Could you please provide:\n- Your check-in date (format: YYYY-MM-DD like 2026-04-10)\n- Your check-out date (format: YYYY-MM-DD like 2026-04-15)\n- Number of guests\n\nFor example: 'I want to book for 2 guests from April 10 to April 15'"
            
            # Generic fallback
            else:
                return "I encountered an issue. Could you please clarify what you'd like to do? Options:\n1. Book a new room (provide dates and number of guests)\n2. Cancel or reschedule (provide your booking ID)\n3. Check booking status (provide booking ID)"
    
    def _normalize_user_input(self, message: str) -> str:
        """Normalize ambiguous user input to help Groq parse it better.
        
        This helps with common patterns like:
        - "4-12 to 4-15" → "April 12 to April 15"
        - "3 guest" → "3 guests"
        - "4 peoples" → "4 people"
        
        Args:
            message: Raw user input
            
        Returns:
            Normalized message
        """
        import re
        
        normalized = message
        
        # Normalize guest count variations: "3 guest" → "3 guests", "guest" → "guests"
        normalized = re.sub(r'(\d+)\s+guest(?!s)', r'\1 guests', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'(\d+)\s+people(?!s)', r'\1 people', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'(\d+)\s+person\b', r'\1 people', normalized, flags=re.IGNORECASE)
        
        # Handle date patterns like "12-4" to be more explicit (ambiguous - could be day-month or month-day)
        # If user says "4-12 to 4-15" in context of current date April 2026, help interpret dates
        # Pattern: "M-D to M-D" or "MM-DD to MM-DD"
        date_pattern = r'(\d{1,2})-(\d{1,2})\s+to\s+(\d{1,2})-(\d{1,2})'
        match = re.search(date_pattern, normalized)
        if match:
            m1, d1, m2, d2 = map(int, match.groups())
            # If first part is less than 13 and second part is less than 32, likely month-day format
            if m1 < 13 and d1 < 32 and m2 < 13 and d2 < 32:
                # Convert to more verbose format to help Groq
                months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                if m1 <= 12 and m2 <= 12:
                    month1_name = months[m1]
                    month2_name = months[m2]
                    normalized = re.sub(date_pattern, f'{month1_name} {d1} to {month2_name} {d2}', normalized)
                    logger.info(f"📅 Converted dates: {m1}-{d1} to {m2}-{d2} → {month1_name} {d1} to {month2_name} {d2}")
        
        return normalized

    def _reset_flow(self):
        """Reset deterministic workflow state."""
        self.flow_state = {
            "intent": None,
            "stage": None,
            "slots": {},
        }

    def _extract_guest_count(self, text: str) -> Optional[int]:
        """Extract guest count from natural language text."""
        patterns = [
            r"(\d{1,2})\s*(?:guests?|people|persons?)",
            r"(?:for|with)\s*(\d{1,2})",
            r"^\s*(\d{1,2})\s*$",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if 1 <= value <= 20:
                    return value
        return None

    def _extract_booking_id(self, text: str) -> Optional[str]:
        """Extract booking ID from text."""
        match = re.search(r"\b(BKG-[A-Za-z0-9-]{6,}|[a-fA-F0-9]{24})\b", text)
        return match.group(1) if match else None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        match = re.search(r"(?:\+?\d[\d\s\-()]{6,}\d)", text)
        if not match:
            return None
        phone = match.group(0).strip()
        digits = re.sub(r"\D", "", phone)
        return phone if len(digits) >= 7 else None

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract likely guest name from text."""
        lowered = text.lower().strip()

        # Prefer explicit name labels first.
        explicit = re.search(
            r"(?:my\s+name\s+is|name\s+is|i\s+am|i'm)\s+([a-z][a-z\s.'-]{1,60})",
            lowered,
        )
        if explicit:
            candidate = explicit.group(1)
            # Stop at separators if user also included other fields.
            candidate = re.split(r"[,;]|\b(?:email|phone|mobile)\b", candidate, maxsplit=1)[0]
            candidate = re.sub(r"\s+", " ", candidate).strip(" .,-")
            if re.fullmatch(r"[a-zA-Z][a-zA-Z\s.'-]{1,60}", candidate):
                return candidate.title()

        # Remove email/phone so remaining text can be interpreted as a name fragment.
        cleaned = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", " ", text)
        cleaned = re.sub(r"(?:\+?\d[\d\s\-()]{6,}\d)", " ", cleaned)

        # Prefer the first comma-separated segment (e.g., "kamal sri, ...").
        first_segment = cleaned.split(",", 1)[0].strip()
        first_segment = re.sub(
            r"\b(?:here\s+is\s+the\s+details|here\s+is\s+my\s+booking\s+details|details|booking\s+details|contact\s+details|guest\s+details)\b",
            " ",
            first_segment,
            flags=re.IGNORECASE,
        )
        first_segment = re.sub(r"\s+", " ", first_segment).strip(" .,-")
        if re.fullmatch(r"[a-zA-Z][a-zA-Z\s.'-]{1,60}", first_segment):
            words = [w for w in first_segment.split() if len(w) > 1]
            if 1 <= len(words) <= 4:
                return " ".join(words).title()

        # Fallback: if full message is mostly a name only.
        plain = re.sub(r"\s+", " ", text).strip()
        if re.fullmatch(r"[a-zA-Z][a-zA-Z\s.'-]{1,60}", plain):
            words = [w for w in plain.split() if len(w) > 1]
            if 1 <= len(words) <= 4:
                return " ".join(words).title()

        return None

    def _extract_iso_dates(self, text: str) -> List[str]:
        """Extract YYYY-MM-DD dates from text."""
        return re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)

    def _extract_month_dates(self, text: str) -> List[date]:
        """Extract month-name dates (e.g., April 20) from text."""
        month_map = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        results: List[date] = []
        for month_text, day_text in re.findall(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})\b",
            text,
            flags=re.IGNORECASE,
        ):
            month = month_map.get(month_text.lower())
            day = int(day_text)
            if not month:
                continue
            try:
                results.append(date(datetime.now().year, month, day))
            except ValueError:
                continue
        return results

    def _extract_checkin_checkout(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract check-in/check-out dates and return ISO strings."""
        iso_dates = self._extract_iso_dates(text)
        if len(iso_dates) >= 2:
            return iso_dates[0], iso_dates[1]

        month_dates = self._extract_month_dates(text)
        if len(month_dates) >= 2:
            return month_dates[0].isoformat(), month_dates[1].isoformat()

        numeric = re.findall(r"\b(\d{1,2})[/-](\d{1,2})\b", text)
        if len(numeric) >= 2:
            try:
                first = date(datetime.now().year, int(numeric[0][0]), int(numeric[0][1]))
                second = date(datetime.now().year, int(numeric[1][0]), int(numeric[1][1]))
                return first.isoformat(), second.isoformat()
            except ValueError:
                return None, None

        return None, None

    def _is_negative_confirmation(self, text: str) -> bool:
        """Detect explicit negative confirmation."""
        lowered = text.lower().strip()
        tokens = set(re.findall(r"[a-z]+", lowered))
        negatives = {"no", "not", "cancel", "stop", "wrong"}
        return len(tokens) <= 4 and any(word in tokens for word in negatives)

    def _select_room_from_message(self, message: str, rooms: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select a room by ID or name from user message."""
        lowered = message.lower()
        for room in rooms:
            room_id = str(room.get("_id", ""))
            room_name = str(room.get("name", "")).lower()
            if room_id and room_id.lower() in lowered:
                return room
            if room_name and room_name in lowered:
                return room
        return None

    async def _handle_structured_flow(self, user_message: str) -> Optional[str]:
        """Handle booking/cancel/reschedule flows deterministically using backend data."""
        lowered = user_message.lower()
        current_intent = self.flow_state.get("intent")
        slots = self.flow_state.setdefault("slots", {})

        # Deterministic RAG handling for hotel information questions.
        if current_intent is None and self._is_knowledge_query(lowered):
            docs = await VectorStoreService.search(
                KNOWLEDGE_BASE_COLLECTION,
                user_message,
                limit=8,
                score_threshold=0.15,
            )
            return self._format_knowledge_response(user_message, docs)

        if current_intent is None:
            if any(word in lowered for word in ["cancel", "cancell"]):
                self.flow_state["intent"] = "cancel"
                self.flow_state["stage"] = "need_booking_id"
            elif any(word in lowered for word in ["reschedule", "reshedule", "change booking", "modify booking"]):
                self.flow_state["intent"] = "reschedule"
                self.flow_state["stage"] = "need_booking_id"
            elif any(word in lowered for word in ["book", "booking", "reserve", "make booking"]):
                self.flow_state["intent"] = "book"
                self.flow_state["stage"] = "collect_search"
            else:
                return None

        intent = self.flow_state.get("intent")
        stage = self.flow_state.get("stage")
        express_client = await get_express_client()

        if intent == "book":
            check_in, check_out = self._extract_checkin_checkout(user_message)
            guests = self._extract_guest_count(user_message)
            if check_in:
                slots["check_in"] = check_in
            if check_out:
                slots["check_out"] = check_out
            if guests is not None:
                slots["guests"] = guests

            if stage == "collect_search":
                missing = []
                if not slots.get("check_in"):
                    missing.append("check-in date")
                if not slots.get("check_out"):
                    missing.append("check-out date")
                if not slots.get("guests"):
                    missing.append("number of guests")
                if missing:
                    return (
                        "Sure, I can help with your booking. "
                        f"Please share your {', '.join(missing)}. "
                        "Example: 2026-04-20 to 2026-04-28 for 3 guests."
                    )

                rooms = await express_client.search_rooms(
                    check_in=slots["check_in"],
                    check_out=slots["check_out"],
                    guests=int(slots["guests"]),
                )
                slots["rooms"] = rooms
                self.flow_state["stage"] = "select_room"
                return self._format_search_rooms_response(
                    {
                        "check_in": slots["check_in"],
                        "check_out": slots["check_out"],
                        "guests": slots["guests"],
                    },
                    rooms,
                )

            if stage == "select_room":
                selected = self._select_room_from_message(user_message, slots.get("rooms", []))
                if not selected:
                    return "Please choose a room from the list by room name or room ID."

                slots["selected_room"] = selected
                self.flow_state["stage"] = "collect_guest_details"

                # Accept details in same message if user provided them.
                email = self._extract_email(user_message)
                phone = self._extract_phone(user_message)
                name = self._extract_name(user_message)
                if name:
                    slots["guest_name"] = name
                if email:
                    slots["guest_email"] = email
                if phone:
                    slots["guest_phone"] = phone

                missing = [
                    field for field in ["guest_name", "guest_email", "guest_phone"]
                    if not slots.get(field)
                ]
                if missing:
                    return (
                        f"Great choice: {selected.get('name')} (ID: {selected.get('_id')}). "
                        "Please share guest details: full name, email, and phone number."
                    )

            if self.flow_state.get("stage") == "collect_guest_details":
                email = self._extract_email(user_message)
                phone = self._extract_phone(user_message)
                name = self._extract_name(user_message)
                if name:
                    slots["guest_name"] = name
                if email:
                    slots["guest_email"] = email
                if phone:
                    slots["guest_phone"] = phone

                missing = [
                    field for field in ["guest_name", "guest_email", "guest_phone"]
                    if not slots.get(field)
                ]
                if missing:
                    return "I still need your full name, email, and phone number to continue the booking."

                selected_room = slots.get("selected_room", {})
                total_price = self._calculate_total_price(
                    slots["check_in"],
                    slots["check_out"],
                    float(selected_room.get("pricePerNight", 0)),
                )
                slots["total_price"] = total_price
                self.flow_state["stage"] = "confirm_booking"
                return (
                    "Please confirm your booking details:\n"
                    f"- Room: {selected_room.get('name')} ({selected_room.get('_id')})\n"
                    f"- Dates: {slots['check_in']} to {slots['check_out']}\n"
                    f"- Guests: {slots['guests']}\n"
                    f"- Total: ${total_price}\n"
                    f"- Name: {slots['guest_name']}\n"
                    f"- Email: {slots['guest_email']}\n"
                    f"- Phone: {slots['guest_phone']}\n"
                    "Is this correct?"
                )

            if stage == "confirm_booking":
                if self._is_negative_confirmation(user_message):
                    self._reset_flow()
                    return "No problem. I have stopped this booking flow. Tell me your updated details when you are ready."
                if not self._is_explicit_confirmation(user_message):
                    return "Please reply with 'yes' to confirm this booking, or 'no' to cancel this booking flow."

                selected_room = slots.get("selected_room", {})
                create_result = await express_client.create_booking(
                    user_id=self.user_id,
                    token=self.token,
                    room_id=str(selected_room.get("_id")),
                    check_in=slots["check_in"],
                    check_out=slots["check_out"],
                    guests=int(slots["guests"]),
                    total_price=float(slots["total_price"]),
                    guest_name=slots["guest_name"],
                    guest_email=slots["guest_email"],
                    guest_phone=slots["guest_phone"],
                )
                booking_data = create_result.get("booking", create_result) if isinstance(create_result, dict) else {}
                booking_ref = booking_data.get("bookingId") or booking_data.get("_id") or "N/A"
                self._reset_flow()
                return (
                    f"Your booking is confirmed. Booking ID: {booking_ref}. "
                    f"Stay: {slots['check_in']} to {slots['check_out']} for {slots['guests']} guest(s)."
                )

        if intent == "cancel":
            if stage == "need_booking_id":
                booking_id = self._extract_booking_id(user_message) or user_message.strip()
                if not self._is_valid_booking_identifier(booking_id):
                    return "Please share your booking ID (example: BKG-ABC123 or a 24-char booking ID)."
                slots["booking_id"] = booking_id
                booking = await express_client.get_booking(booking_id, self.token)
                slots["booking"] = booking
                self.flow_state["stage"] = "confirm_cancel"
                formatted = self._format_booking_status_response(booking, booking_id)
                return f"{formatted}\n\nDo you want me to cancel this booking now?"

            if stage == "confirm_cancel":
                if self._is_negative_confirmation(user_message):
                    self._reset_flow()
                    return "Understood. I will keep your booking unchanged."
                if not self._is_explicit_confirmation(user_message):
                    return "Please reply with 'yes' to confirm cancellation, or 'no' to keep this booking."

                result = await express_client.cancel_booking(
                    booking_id=slots["booking_id"],
                    token=self.token,
                    reason="Cancelled via booking assistant",
                )
                booking_ref = (
                    result.get("booking", {}).get("bookingId")
                    or result.get("booking", {}).get("id")
                    or slots["booking_id"]
                )
                self._reset_flow()
                return f"Your booking {booking_ref} has been cancelled successfully."

        if intent == "reschedule":
            if stage == "need_booking_id":
                booking_id = self._extract_booking_id(user_message) or user_message.strip()
                if not self._is_valid_booking_identifier(booking_id):
                    return "Please share your booking ID first (example: BKG-ABC123)."
                slots["booking_id"] = booking_id
                booking = await express_client.get_booking(booking_id, self.token)
                slots["booking"] = booking
                self.flow_state["stage"] = "collect_reschedule_changes"
                formatted = self._format_booking_status_response(booking, booking_id)
                return (
                    f"{formatted}\n\n"
                    "Please provide the new check-in and check-out dates. "
                    "If you also want to update guest count/name/email/phone, include them in the same message."
                )

            if stage == "collect_reschedule_changes":
                new_check_in, new_check_out = self._extract_checkin_checkout(user_message)
                if new_check_in:
                    slots["new_check_in"] = new_check_in
                if new_check_out:
                    slots["new_check_out"] = new_check_out
                guest_count = self._extract_guest_count(user_message)
                if guest_count is not None:
                    slots["new_guests"] = guest_count
                email = self._extract_email(user_message)
                phone = self._extract_phone(user_message)
                name = self._extract_name(user_message)
                if name:
                    slots["new_guest_name"] = name
                if email:
                    slots["new_guest_email"] = email
                if phone:
                    slots["new_guest_phone"] = phone

                if not slots.get("new_check_in") or not slots.get("new_check_out"):
                    return "Please provide the new check-in and check-out dates in YYYY-MM-DD format."

                self.flow_state["stage"] = "confirm_reschedule"
                optional_lines = []
                if slots.get("new_guests") is not None:
                    optional_lines.append(f"- New guests: {slots['new_guests']}")
                if slots.get("new_guest_name"):
                    optional_lines.append(f"- New guest name: {slots['new_guest_name']}")
                if slots.get("new_guest_email"):
                    optional_lines.append(f"- New guest email: {slots['new_guest_email']}")
                if slots.get("new_guest_phone"):
                    optional_lines.append(f"- New guest phone: {slots['new_guest_phone']}")
                optional_text = "\n".join(optional_lines)
                if optional_text:
                    optional_text = f"\n{optional_text}"
                return (
                    "Please confirm your reschedule request:\n"
                    f"- Booking ID: {slots['booking_id']}\n"
                    f"- New check-in: {slots['new_check_in']}\n"
                    f"- New check-out: {slots['new_check_out']}"
                    f"{optional_text}\n"
                    "Reply 'yes' to confirm or 'no' to cancel this update."
                )

            if stage == "confirm_reschedule":
                if self._is_negative_confirmation(user_message):
                    self._reset_flow()
                    return "No changes were made. Your booking remains unchanged."
                if not self._is_explicit_confirmation(user_message):
                    return "Please reply with 'yes' to confirm reschedule, or 'no' to cancel."

                result = await express_client.reschedule_booking(
                    booking_id=slots["booking_id"],
                    new_check_in=slots["new_check_in"],
                    new_check_out=slots["new_check_out"],
                    token=self.token,
                    new_guests=slots.get("new_guests"),
                    new_guest_name=slots.get("new_guest_name"),
                    new_guest_email=slots.get("new_guest_email"),
                    new_guest_phone=slots.get("new_guest_phone"),
                )
                response = self._format_reschedule_response(
                    result,
                    {
                        "booking_id": slots["booking_id"],
                        "new_check_in": slots["new_check_in"],
                        "new_check_out": slots["new_check_out"],
                    },
                )
                self._reset_flow()
                return response

        return None

    
    def _is_valid_booking_identifier(self, booking_id: str) -> bool:
        """Validate booking ID format (BKG-...) or Mongo ObjectId."""
        import re

        if not isinstance(booking_id, str):
            return False

        normalized = booking_id.strip()
        if not normalized:
            return False

        # Reject known placeholder-style values from LLM generations.
        placeholder_markers = [
            "<id",
            "most recent",
            "just got cancelled",
            "cancelled booking",
            "booking that",
            "placeholder",
        ]
        lowered = normalized.lower()
        if any(marker in lowered for marker in placeholder_markers):
            return False

        if re.fullmatch(r"(?i)bkg-[a-z0-9-]{6,}", normalized):
            return True
        if re.fullmatch(r"[a-fA-F0-9]{24}", normalized):
            return True
        return False

    def _is_explicit_confirmation(self, text: str) -> bool:
        """Return True only for short explicit confirmation replies."""
        import re

        if not isinstance(text, str):
            return False

        normalized = text.strip().lower()
        if not normalized:
            return False

        # Prevent accidental matches such as "booking" containing "ok".
        confirmation_words = {"yes", "confirm", "confirmed", "correct", "true", "ok", "okay", "sure"}
        tokens = set(re.findall(r"[a-z]+", normalized))
        if not tokens:
            return False

        # Short replies like "yes", "ok", "yes please" count as confirmation.
        if len(tokens) <= 3 and any(word in tokens for word in confirmation_words):
            return True

        return False
    
    async def _get_agent_response(self) -> str:
        """Get response from Groq LLM with tool calling.
        
        Returns:
            Final response string
        """
        system_prompt = self._get_system_prompt()
        
        # Call Groq with tools
        logger.info(f"\n📞 Calling Groq with 8 tools available")
        logger.info(f"📋 Last 2 messages in history:")
        for i, msg in enumerate(self.conversation_history[-2:]):
            logger.info(f"  [{i}] {msg.get('role')}: {msg.get('content', '')[:100]}...")
        
        # Determine tool usage and force a specific safe tool when intent is clear.
        last_user_msg = ""
        for msg in reversed(self.conversation_history):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "").lower()
                break
        
        # Check conversation history for context (e.g., did user ask to reschedule earlier?)
        full_context = " ".join([msg.get("content", "").lower() for msg in self.conversation_history if msg.get("role") == "user"])
        
        has_booking_id = self._looks_like_booking_id(last_user_msg)
        has_dates = self._has_date_pair(last_user_msg)
        has_guest_count = self._extract_guest_count(last_user_msg) is not None
        latest_intent = self._detect_latest_intent(last_user_msg)
        has_reschedule_context = any(word in full_context for word in ["reschedule", "change", "modify", "move"])
        has_cancel_context = any(word in full_context for word in ["cancel"])

        # If latest message is just booking ID, inherit the active flow from prior context.
        if latest_intent == "unknown":
            if has_reschedule_context and not has_cancel_context:
                latest_intent = "reschedule"
            elif has_cancel_context and not has_reschedule_context:
                latest_intent = "cancel"

        required_tool_name: Optional[str] = None
        if latest_intent == "book" and has_dates and has_guest_count:
            required_tool_name = "search_rooms"
        if has_booking_id and latest_intent == "reschedule":
            # Always show current details first in reschedule flow.
            required_tool_name = "get_booking_status"
        elif has_booking_id and latest_intent == "cancel":
            # Always fetch details first; cancellation requires explicit confirmation.
            required_tool_name = "get_booking_status"
        elif has_booking_id and latest_intent == "unknown":
            # Safe default for booking-id-only messages.
            required_tool_name = "get_booking_status"
        elif has_booking_id and has_dates and latest_intent == "reschedule":
            required_tool_name = "get_booking_status"

        if required_tool_name:
            tool_choice: Any = {"type": "function", "function": {"name": required_tool_name}}
        else:
            tool_choice = "auto"
        logger.info(f"🔧 Tool choice: {tool_choice}")
        logger.info(f"  - has_booking_id: {has_booking_id}")
        logger.info(f"  - has_dates: {has_dates}")
        logger.info(f"  - has_guest_count: {has_guest_count}")
        logger.info(f"  - latest_intent: {latest_intent}")
        logger.info(f"  - has_reschedule_context: {has_reschedule_context}")
        logger.info(f"  - has_cancel_context: {has_cancel_context}")
        logger.info(f"  - required_tool_name: {required_tool_name}")
        logger.info(f"  - Message: '{last_user_msg[:60]}...'" if len(last_user_msg) > 60 else f"  - Message: '{last_user_msg}'")
        
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                *self.conversation_history
            ],
            tools=GROQ_TOOLS,
            tool_choice=tool_choice,
            max_tokens=2048,
        )
        
        logger.info(f"📞 Groq response received:")
        logger.info(f"  - Has tool_calls: {bool(response.choices[0].message.tool_calls)}")
        logger.info(f"  - Tool calls count: {len(response.choices[0].message.tool_calls) if response.choices[0].message.tool_calls else 0}")
        if response.choices[0].message.tool_calls:
            for tc in response.choices[0].message.tool_calls:
                logger.info(f"    - Tool: {tc.function.name}")
        logger.info(f"  - Text content: {response.choices[0].message.content[:100] if response.choices[0].message.content else 'None'}...")
        
        # Handle tool calls if present
        if response.choices[0].message.tool_calls:
            logger.info(f"✓ Tool calls detected, handling them...")
            return await self._handle_tool_calls(response.choices[0].message.tool_calls)
        else:
            logger.warning(f"⚠️ No tool calls from Groq, agent will ask for details")
            content = response.choices[0].message.content or ""

            # Fallback: Groq may return pseudo function-call text instead of actual tool_calls.
            kb_match = re.search(
                r"search_knowledge_base\s*>?\s*\{\s*\"query\"\s*:\s*\"([^\"]+)\"\s*\}",
                content,
                flags=re.IGNORECASE,
            )
            if kb_match:
                parsed_query = kb_match.group(1).strip() or last_user_msg or "hotel information"
                docs = await VectorStoreService.search(
                    KNOWLEDGE_BASE_COLLECTION,
                    parsed_query,
                    limit=8,
                    score_threshold=0.15,
                )
                logger.info("✓ Parsed pseudo tool-call text and executed deterministic KB search")
                return self._format_knowledge_response(parsed_query, docs)

            # Safety check: never return responses that include function definitions or schema JSON
            if '"name":"' in content and '"description":"' in content and '"parameters"' in content:
                logger.error(f"⚠️ Response contains function schema JSON, returning generic message instead")
                return "I'm here to help with your booking. How can I assist you today?"
            return content
    
    def _coerce_tool_parameters(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce tool parameters to correct types.
        
        Groq sometimes sends numeric values as strings, this converts them to proper types.
        
        Args:
            function_name: Name of the tool/function
            arguments: Raw arguments from Groq
            
        Returns:
            Coerced arguments with correct types
        """
        coerced = arguments.copy()
        
        # Convert string numbers to integers for specific fields
        integer_fields = {
            "search_rooms": ["guests"],
            "create_booking": ["guests"],
        }
        
        if function_name in integer_fields:
            for field in integer_fields[function_name]:
                if field in coerced and isinstance(coerced[field], str):
                    try:
                        coerced[field] = int(coerced[field])
                        logger.info(f"✓ Coerced {field} from string to integer: {coerced[field]}")
                    except (ValueError, TypeError) as e:
                        logger.error(f"✗ Failed to coerce {field}: {e}")
        
        # Convert string floats to floats for price fields
        float_fields = {
            "create_booking": ["total_price"]
        }
        
        if function_name in float_fields:
            for field in float_fields[function_name]:
                if field in coerced and isinstance(coerced[field], str):
                    try:
                        coerced[field] = float(coerced[field])
                        logger.info(f"✓ Coerced {field} from string to float: {coerced[field]}")
                    except (ValueError, TypeError) as e:
                        logger.error(f"✗ Failed to coerce {field}: {e}")
        
        return coerced
    
    def _validate_search_rooms_params(self, arguments: Dict[str, Any]) -> tuple[bool, str]:
        """Validate search_rooms has all required parameters.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ["check_in", "check_out", "guests"]
        missing = []
        
        for field in required_fields:
            if field not in arguments or arguments[field] is None or arguments[field] == "":
                missing.append(field)
        
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"
        
        return True, ""
    
    def _validate_create_booking_params(self, arguments: Dict[str, Any]) -> tuple[bool, str]:
        """Validate create_booking has all required parameters with REAL values.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ["room_id", "check_in", "check_out", "guests", "total_price", "guest_name", "guest_email", "guest_phone"]
        missing = []
        invalid = []
        
        for field in required_fields:
            if field not in arguments or arguments[field] is None or arguments[field] == "":
                missing.append(field)
            
            # Check for placeholder values
            if field == "room_id":
                room_id = arguments.get("room_id", "")
                if isinstance(room_id, str) and ("insert" in room_id.lower() or "needed" in room_id.lower() or room_id.startswith("_")):
                    invalid.append(f"{field} contains placeholder text: {room_id}")
            
            if field == "total_price":
                price = arguments.get("total_price")
                if isinstance(price, str) and ("insert" in price.lower() or "calculate" in price.lower()):
                    invalid.append(f"{field} contains placeholder text: {price}")
        
        if missing:
            return False, f"Missing required booking details: {', '.join(missing)}"
        
        if invalid:
            return False, f"Invalid booking details: {'. '.join(invalid)}. Please provide actual values, not placeholders."
        
        return True, ""

    def _calculate_total_price(
        self,
        check_in: str,
        check_out: str,
        price_per_night: float,
    ) -> float:
        """Calculate total price from nights x price per night."""
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
        nights = (check_out_date - check_in_date).days
        if nights <= 0:
            raise ValueError("Check-out date must be after check-in date")
        return round(float(price_per_night) * nights, 2)

    def _format_search_rooms_response(self, arguments: Dict[str, Any], rooms: List[Dict[str, Any]]) -> str:
        """Create deterministic room search response from DB results only."""
        check_in = arguments.get("check_in")
        check_out = arguments.get("check_out")
        guests = arguments.get("guests")

        if not rooms:
            return (
                f"I checked availability for {guests} guest(s) from {check_in} to {check_out}, "
                "but no rooms are available for those dates. Please try different dates."
            )

        lines = [
            f"I've searched available rooms for {guests} guest(s) from {check_in} to {check_out}.",
            "Here are the exact rooms currently in our database:",
        ]

        for room in rooms:
            room_name = room.get("name", "Unknown Room")
            room_id = room.get("_id", "N/A")
            price = room.get("pricePerNight", "N/A")
            available_units = room.get("availableUnits", 0)
            total_units = room.get("totalUnits", 0)
            lines.append(
                f"- {room_name} (ID: {room_id}) - ${price}/night "
                f"(available {available_units}/{total_units})"
            )

        lines.append("Which room would you like to book? Please reply with the room name or ID from this list.")
        return "\n".join(lines)

    def _format_booking_status_response(self, result: Dict[str, Any], requested_booking_id: str) -> str:
        """Format deterministic booking-status response for reschedule/cancel workflows."""
        if not isinstance(result, dict):
            return (
                f"I retrieved booking `{requested_booking_id}`, but the details were not in the expected format. "
                "Please try again."
            )

        booking = result.get("booking", result)
        if not isinstance(booking, dict):
            return (
                f"I couldn't read details for booking `{requested_booking_id}`. "
                "Please confirm the booking ID and try again."
            )

        booking_ref = booking.get("bookingId") or booking.get("_id") or requested_booking_id
        check_in = booking.get("checkIn") or booking.get("check_in") or "N/A"
        check_out = booking.get("checkOut") or booking.get("check_out") or "N/A"
        guests = booking.get("guests", "N/A")
        status = booking.get("status", "N/A")
        room = booking.get("roomId", {})
        room_name = booking.get("roomNameSnapshot")
        room_rate = None
        if isinstance(room, dict):
            room_name = room_name or room.get("name")
            room_rate = room.get("pricePerNight")
        room_name = room_name or "N/A"

        lines = [
            f"I found booking `{booking_ref}`. Here are the current details:",
            f"✓ Current Check-in: {check_in}",
            f"✓ Current Check-out: {check_out}",
            f"✓ Current Room: {room_name}",
            f"✓ Current Guests: {guests}",
            f"✓ Current Status: {status}",
        ]
        if room_rate is not None:
            lines.append(f"✓ Room Rate: ${room_rate}/night")

        lines.extend(
            [
                "",
                "What would you like to change?",
                "- New check-in and check-out dates",
                "- Guest count (if needed)",
                "- Room details (if needed)",
                "Tell me only the fields you want to update.",
            ]
        )
        return "\n".join(lines)

    def _format_reschedule_response(self, result: Dict[str, Any], arguments: Dict[str, Any]) -> str:
        """Create deterministic reschedule response from backend result only."""
        booking_id = arguments.get("booking_id", "N/A")
        new_check_in = arguments.get("new_check_in", "N/A")
        new_check_out = arguments.get("new_check_out", "N/A")

        if not isinstance(result, dict):
            return (
                f"I couldn't confirm the reschedule for booking `{booking_id}` because the server response was invalid. "
                "Please check your booking status and try again."
            )

        if result.get("success") is not True:
            error_message = result.get("message") or result.get("error") or "Unknown error"
            return (
                f"I couldn't reschedule booking `{booking_id}`. "
                f"Reason: {error_message}. Please verify the dates/booking ID and try again."
            )

        booking = result.get("booking", {})
        if not isinstance(booking, dict):
            booking = {}
        old_check_in = booking.get("oldCheckIn") or booking.get("previousCheckIn")
        old_check_out = booking.get("oldCheckOut") or booking.get("previousCheckOut")
        updated_check_in = booking.get("checkIn") or booking.get("check_in") or new_check_in
        updated_check_out = booking.get("checkOut") or booking.get("check_out") or new_check_out
        updated_booking_ref = booking.get("bookingId") or booking.get("_id") or booking_id

        old_range = f"{old_check_in} to {old_check_out}" if old_check_in and old_check_out else "previous dates"
        return (
            f"✓ Your booking `{updated_booking_ref}` has been successfully rescheduled.\n"
            f"- Previous dates: {old_range}\n"
            f"- New dates: {updated_check_in} to {updated_check_out}\n"
            "The booking record has been updated in the system."
        )

    def _is_knowledge_query(self, text: str) -> bool:
        """Detect user questions that should be answered from knowledge base."""
        normalized = (text or "").lower()
        if not normalized:
            return False

        booking_intent_words = [
            "book",
            "booking",
            "reserve",
            "reschedule",
            "cancel",
            "check-in",
            "check in",
            "check-out",
            "check out",
        ]
        if any(word in normalized for word in booking_intent_words):
            return False

        kb_words = [
            "hotel name",
            "hotel",
            "room categories",
            "room type",
            "amenities",
            "facility",
            "spa",
            "pool",
            "beach",
            "wifi",
            "restaurant",
            "policy",
            "pet",
            "smoking",
            "transfer",
            "location",
            "contact",
            "check in time",
            "check out time",
            "do you have",
            "what is",
            "what are",
            "tell me about",
        ]
        return any(word in normalized for word in kb_words)

    def _format_knowledge_response(self, query: str, docs: List[Dict[str, Any]]) -> str:
        """Create grounded, user-friendly response from vector search results only."""
        if not docs:
            return (
                "I couldn't find that detail in the current hotel knowledge base. "
                "Please rephrase your question (for example: hotel name, room categories, check-in time, spa, or policies)."
            )

        def _normalize_text(raw: str) -> str:
            text = raw or ""
            text = re.sub(r"---\s*Page\s*\d+\s*---", " ", text, flags=re.IGNORECASE)
            text = re.sub(r"={5,}", " ", text)
            text = text.replace("\r", "\n")
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r"[ \t]{2,}", " ", text)
            return text.strip()

        def _extract_contact_details(text: str) -> List[str]:
            patterns = [
                ("Front desk", r"front\s*desk\s*:\s*([^\n]+)"),
                ("Reservations", r"reservations\s*(?:direct)?\s*:\s*([^\n]+)"),
                ("WhatsApp", r"whatsapp\s*(?:business)?\s*:\s*([^\n]+)"),
                ("Website", r"website\s*:\s*([^\n]+)"),
                ("Emergency", r"emergency\s*(?:after-hours)?\s*:\s*([^\n]+)"),
                ("Lost & found", r"lost\s*&\s*found\s*:\s*([^\n]+)"),
            ]

            details: List[str] = []
            for label, pattern in patterns:
                matches = re.findall(pattern, text, flags=re.IGNORECASE)
                if not matches:
                    continue

                normalized_matches = [re.sub(r"\s+", " ", m).strip(" .") for m in matches]

                def _score(candidate: str) -> int:
                    score = 0
                    if re.search(r"\+?\d", candidate):
                        score += 2
                    if "@" in candidate:
                        score += 2
                    if "www." in candidate.lower() or "http" in candidate.lower():
                        score += 2
                    if "24/7" in candidate:
                        score += 1
                    if len(candidate) > 10:
                        score += 1
                    return score

                best_value = max(normalized_matches, key=_score)
                details.append(f"- {label}: {best_value}")
            return details

        def _extract_room_categories(text: str) -> List[str]:
            category_names = [
                "NEBULA SUITE",
                "AETHER DELUXE",
                "LUMINA FAMILY",
                "STARLIGHT PENTHOUSE",
            ]
            found: List[str] = []

            for name in category_names:
                pattern = rf"(?:\d+\.\s*)?{re.escape(name)}(.*?)(?=(?:\n\s*\d+\.\s*[A-Z][A-Z\s]+)|\n\s*\[|$)"
                match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
                if not match:
                    continue

                block = f"{name} {match.group(1)}"
                size = re.search(r"size\s*:\s*([^\n]+)", block, flags=re.IGNORECASE)
                occupancy = re.search(r"max\s*occupancy\s*:\s*([^\n]+)", block, flags=re.IGNORECASE)
                view = re.search(r"view\s*:\s*([^\n]+)", block, flags=re.IGNORECASE)
                price = re.search(r"price\s*range\s*:\s*([^\n]+)", block, flags=re.IGNORECASE)

                parts = [f"- {name.title()}"]
                if occupancy:
                    parts.append(f"max {occupancy.group(1).strip(' .')}")
                if view:
                    view_text = view.group(1).strip(' .')
                    if "view" not in view_text.lower():
                        view_text = f"{view_text} view"
                    parts.append(view_text)
                if price:
                    parts.append(f"{price.group(1).strip(' .')}")
                if size:
                    parts.append(f"{size.group(1).strip(' .')}")

                found.append(" | ".join(parts))

            return found

        cleaned_texts = [
            _normalize_text(str(doc.get("text", "")))
            for doc in docs
            if str(doc.get("text", "")).strip()
        ]
        combined_text = "\n\n".join(cleaned_texts)
        lowered_query = (query or "").lower()

        if any(key in lowered_query for key in ["room categories", "room category", "room types", "room type"]):
            room_lines = _extract_room_categories(combined_text)
            if room_lines:
                return "\n".join(
                    [
                        "We currently have these room categories:",
                        *room_lines,
                        "",
                        "I can also give full details for any one room type you choose.",
                    ]
                )

        if any(key in lowered_query for key in ["contact", "phone", "email", "whatsapp", "reservation"]):
            contact_lines = _extract_contact_details(combined_text)
            if contact_lines:
                return "\n".join(
                    [
                        "Here are the hotel contact details:",
                        *contact_lines,
                    ]
                )

        query_terms = [
            term
            for term in re.findall(r"[a-zA-Z]{3,}", lowered_query)
            if term not in {"what", "which", "where", "when", "this", "that", "hotel", "details", "about", "tell", "give"}
        ]
        candidate_lines: List[str] = []
        for line in re.split(r"\n+", combined_text):
            clean_line = line.strip(" -•\t")
            if len(clean_line) < 18:
                continue
            if len(clean_line) > 220:
                continue
            if query_terms and not any(term in clean_line.lower() for term in query_terms):
                continue
            candidate_lines.append(clean_line)
            if len(candidate_lines) >= 5:
                break

        if candidate_lines:
            return "\n".join(
                [
                    "Here is what I found from our hotel knowledge base:",
                    *[f"- {line}" for line in candidate_lines],
                    "",
                    "If you want, I can summarize this into a quick recommendation.",
                ]
            )

        fallback = re.sub(r"\s+", " ", combined_text).strip()
        if fallback:
            return (
                "I found related information, but it is not in a clean format for this question. "
                "Please ask a more specific question like 'room categories', 'contact details', 'check-in time', or 'spa hours'."
            )

        return (
            "I found related entries, but they were empty. "
            "Please try asking with a little more detail."
        )

    def _looks_like_booking_id(self, text: str) -> bool:
        """Detect booking references like BKG-XXXXX or Mongo ObjectId."""
        return self._is_valid_booking_identifier(text)
    
    def _has_date_pair(self, text: str) -> bool:
        """Check if text contains check-in and check-out dates for rescheduling.
        
        Detects patterns like:
        - April 12 to April 15
        - 2026-04-12 to 2026-04-15
        - 4/12 to 4/15
        """
        import re
        text_lower = text.lower()
        
        # Pattern 1: Month names with days (April 12 to April 15)
        month_pattern = r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}'
        month_matches = len(re.findall(month_pattern, text_lower))
        
        # Pattern 2: YYYY-MM-DD format (2026-04-12)
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        date_matches = len(re.findall(date_pattern, text))
        
        # Pattern 3: MM/DD format (4/12 or 12/4)
        slash_pattern = r'\d{1,2}/\d{1,2}'
        slash_matches = len(re.findall(slash_pattern, text))
        
        # Need at least 2 dates (check-in and check-out) OR the word "to"/"through" between dates
        has_date_separator = " to " in text_lower or " through " in text_lower or "-" in text
        total_dates = month_matches + date_matches + (slash_matches // 2)
        
        # If we have "to"/"through" and at least 2 distinct date markers, we likely have a date pair
        return total_dates >= 2 or (has_date_separator and (month_matches + date_matches + slash_matches) >= 2)

    def _detect_latest_intent(self, text: str) -> str:
        """Detect latest user intent from message text."""
        normalized = (text or "").lower()
        if any(word in normalized for word in ["reschedule", "change", "modify", "move"]):
            return "reschedule"
        if "cancel" in normalized:
            return "cancel"
        if any(word in normalized for word in ["book", "reserve", "new booking"]):
            return "book"
        return "unknown"

    async def _handle_tool_calls(self, tool_calls: List[Any]) -> str:
        """Handle tool function calls from Groq.
        
        Args:
            tool_calls: List of tool calls from Groq
            
        Returns:
            Response after executing tools
        """
        express_client = await get_express_client()
        tool_results = []
        deterministic_search_response: Optional[str] = None
        deterministic_booking_response: Optional[str] = None
        deterministic_cancel_response: Optional[str] = None
        deterministic_status_response: Optional[str] = None
        deterministic_reschedule_response: Optional[str] = None
        deterministic_kb_response: Optional[str] = None
        latest_user_message = ""
        for msg in reversed(self.conversation_history):
            if msg.get("role") == "user":
                latest_user_message = msg.get("content", "")
                break
        latest_intent = self._detect_latest_intent(latest_user_message)
        has_reschedule_context = any(
            any(word in m.get("content", "").lower() for word in ["reschedule", "change", "modify", "move"])
            for m in self.conversation_history
            if m.get("role") == "user"
        )
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            # Fix parameter types (Groq sometimes sends numbers as strings)
            arguments = self._coerce_tool_parameters(function_name, arguments)
            
            logger.info(f"🔧 Executing tool: {function_name} with coerced args: {arguments}")
            
            try:
                if function_name == "search_rooms":
                    # Validate required parameters
                    is_valid, error_msg = self._validate_search_rooms_params(arguments)
                    if not is_valid:
                        logger.warning(f"⚠️  search_rooms validation failed: {error_msg}")
                        result = {
                            "status": "missing_parameters",
                            "error": error_msg,
                            "message": "I need more information to search for rooms. Please provide: check-in date, check-out date, and number of guests."
                        }
                    else:
                        result = await express_client.search_rooms(**arguments)
                        logger.info(f"🔍 Search rooms result: {json.dumps(result, indent=2)[:500]}...")
                        if isinstance(result, list):
                            deterministic_search_response = self._format_search_rooms_response(arguments, result)
                        
                        # Check if result is empty and provide helpful feedback
                        if isinstance(result, list) and len(result) == 0:
                            logger.warning(f"⚠️  No rooms found for: {arguments}")
                            result = {
                                "status": "no_rooms_found",
                                "query": arguments,
                                "message": f"Sorry, no rooms available for {arguments.get('guests')} guest(s) from {arguments.get('check_in')} to {arguments.get('check_out')}. Please try different dates or reduce the number of guests."
                            }
                    
                elif function_name == "create_booking":
                    # Validate required parameters
                    is_valid, error_msg = self._validate_create_booking_params(arguments)
                    if not is_valid:
                        logger.warning(f"⚠️  create_booking validation failed: {error_msg}")
                        result = {
                            "status": "missing_parameters",
                            "error": error_msg,
                            "message": f"I cannot complete the booking yet. {error_msg}. Please ensure you've selected a specific room and provided all required details (name, email, phone number)."
                        }
                    else:
                        # Always enforce price from room rate and selected date range.
                        # Do not trust LLM-calculated totals because they can drift.
                        room_response = await express_client.get_room(arguments["room_id"])
                        room_details = room_response.get("room", room_response) if isinstance(room_response, dict) else {}
                        price_per_night = room_details.get("pricePerNight")
                        if price_per_night is None:
                            raise ValueError("Room pricePerNight is missing from room details")

                        calculated_total = self._calculate_total_price(
                            check_in=arguments["check_in"],
                            check_out=arguments["check_out"],
                            price_per_night=price_per_night,
                        )

                        provided_total = arguments.get("total_price")
                        if provided_total != calculated_total:
                            logger.warning(
                                f"⚠️ Overriding total_price from {provided_total} to {calculated_total} "
                                f"for room {arguments['room_id']}"
                            )
                        arguments["total_price"] = calculated_total

                        result = await express_client.create_booking(
                            user_id=self.user_id,
                            token=self.token,
                            **arguments
                        )
                        booking_data = result.get("booking", result) if isinstance(result, dict) else {}
                        booking_ref = (
                            booking_data.get("bookingId")
                            or booking_data.get("_id")
                            or "created"
                        )
                        deterministic_booking_response = (
                            f"Booking confirmed successfully. Your booking reference is {booking_ref}. "
                            f"Stay dates: {arguments['check_in']} to {arguments['check_out']}, "
                            f"guests: {arguments['guests']}, total: ${arguments['total_price']}."
                        )
                        logger.info(f"✓ Booking created successfully: {booking_ref}")

                    
                elif function_name == "get_user_bookings":
                    result = await express_client.list_user_bookings(self.token)
                    
                elif function_name == "cancel_booking":
                    # Guardrail: never execute cancellation during a reschedule flow.
                    if latest_intent == "reschedule" or (latest_intent == "unknown" and has_reschedule_context):
                        logger.warning("⚠️ Blocking cancel_booking because conversation intent is reschedule")
                        result = {
                            "success": False,
                            "error": "intent_mismatch",
                            "message": "I will not cancel this booking because you asked to reschedule. Please share new dates to continue rescheduling."
                        }
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "tool_name": function_name,
                            "result": json.dumps(result)
                        })
                        continue
                    logger.info(f"📋 cancel_booking arguments: {arguments}")
                    logger.info(f"📋 Token present: {bool(self.token)}")
                    booking_id = arguments.get("booking_id", "")
                    if not self._is_valid_booking_identifier(booking_id):
                        logger.warning(f"⚠️ Rejecting cancel_booking with invalid booking_id: {booking_id}")
                        result = {
                            "success": False,
                            "error": "Invalid booking_id format",
                            "message": "Please provide a real booking ID (BKG-XXXXX or MongoDB ID) before I can cancel."
                        }
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "tool_name": function_name,
                            "result": json.dumps(result)
                        })
                        continue
                    try:
                        result = await express_client.cancel_booking(
                            token=self.token,
                            **arguments
                        )
                        logger.info(f"✓ cancel_booking returned: {json.dumps(result)[:300]}...")
                        
                        # Generate deterministic response for successful cancellation
                        if result.get("success") and result.get("booking", {}).get("status") == "cancelled":
                            booking_id = result.get("booking", {}).get("bookingId", arguments.get("booking_id", "N/A"))
                            deterministic_cancel_response = (
                                f"✓ Your booking {booking_id} has been successfully cancelled. "
                                f"The room availability has been updated, and room quantity has been released for those dates. "
                                f"You can now book those dates again if needed."
                            )
                            logger.info(f"✓ Deterministic cancel response set: {deterministic_cancel_response}")
                        else:
                            logger.warning(f"⚠️ Cancel returned success but status unclear: {result}")
                            
                    except Exception as e:
                        logger.error(f"✗ cancel_booking failed with error: {type(e).__name__}: {str(e)}", exc_info=True)
                        raise
                    
                elif function_name == "reschedule_booking":
                    booking_id = arguments.get("booking_id", "")
                    if not self._is_valid_booking_identifier(booking_id):
                        logger.warning(f"⚠️ Rejecting reschedule_booking with invalid booking_id: {booking_id}")
                        result = {
                            "success": False,
                            "error": "Invalid booking_id format",
                            "message": "Please provide a real booking ID (BKG-XXXXX or MongoDB ID) before I can reschedule."
                        }
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "tool_name": function_name,
                            "result": json.dumps(result)
                        })
                        continue
                    result = await express_client.reschedule_booking(
                        token=self.token,
                        **arguments
                    )
                    deterministic_reschedule_response = self._format_reschedule_response(result, arguments)
                    
                elif function_name == "get_booking_status":
                    booking_id = str(arguments.get("booking_id", "")).strip()
                    if not self._is_valid_booking_identifier(booking_id):
                        logger.warning(f"⚠️ Rejecting get_booking_status with invalid booking_id: {booking_id}")
                        result = {
                            "success": False,
                            "error": "Invalid booking_id format",
                            "message": "Please provide a valid booking ID to check status."
                        }
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "tool_name": function_name,
                            "result": json.dumps(result)
                        })
                        continue
                    result = await express_client.get_booking(booking_id, self.token)
                    deterministic_status_response = self._format_booking_status_response(result, booking_id)
                    
                elif function_name == "search_knowledge_base":
                    query = str(arguments.get("query", "")).strip()
                    if not query:
                        query = "hotel information"
                    docs = await VectorStoreService.search(
                        KNOWLEDGE_BASE_COLLECTION,
                        query,
                        limit=8,
                        score_threshold=0.15,
                    )
                    deterministic_kb_response = self._format_knowledge_response(query, docs)
                    result = {
                        "query": query,
                        "results": docs,
                        "count": len(docs)
                    }
                    
                elif function_name == "get_available_dates":
                    result = await express_client.get_available_dates(**arguments)
                    
                else:
                    result = {"error": f"Unknown tool: {function_name}"}
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "tool_name": function_name,
                    "result": json.dumps(result) if not isinstance(result, str) else result
                })
                logger.info(f"✓ Tool executed successfully: {function_name}")
                
                # Log detailed result for search_rooms
                if function_name == "search_rooms" and isinstance(result, list):
                    logger.info(f"📊 Search results: {len(result)} rooms available")
                    for i, room in enumerate(result[:3]):  # Log first 3
                        logger.info(f"   Room {i+1}: {room.get('name', 'N/A')} - Type: {room.get('type', 'N/A')}, Available: {room.get('availableUnits', 0)}/{room.get('totalUnits', 0)}")
                
            except Exception as e:
                logger.error(f"✗ Tool execution failed: {function_name}: {e}")
                if function_name == "create_booking":
                    deterministic_booking_response = (
                        f"I couldn't create the booking due to a server/tool error: {str(e)}. "
                        "Please try again in a moment."
                    )
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "tool_name": function_name,
                    "result": json.dumps({"error": str(e)})
                })
        
        # Add assistant message with tool calls
        self.conversation_history.append({
            "role": "assistant",
            "content": "",
            "tool_calls": tool_calls
        })
        
        # Add tool results
        for tool_result in tool_results:
            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_result["tool_call_id"],
                "content": tool_result["result"]
            })
        
        # Get final response from Groq
        if deterministic_search_response and len(tool_calls) == 1 and tool_calls[0].function.name == "search_rooms":
            logger.info("✓ Returning deterministic search response to prevent room hallucination")
            return deterministic_search_response
        if deterministic_booking_response and any(tc.function.name == "create_booking" for tc in tool_calls):
            logger.info("✓ Returning deterministic booking response")
            return deterministic_booking_response
        if deterministic_cancel_response and any(tc.function.name == "cancel_booking" for tc in tool_calls):
            logger.info("✓ Returning deterministic cancel response")
            return deterministic_cancel_response
        if deterministic_status_response and len(tool_calls) == 1 and tool_calls[0].function.name == "get_booking_status":
            logger.info("✓ Returning deterministic booking status response")
            return deterministic_status_response
        if deterministic_reschedule_response and any(tc.function.name == "reschedule_booking" for tc in tool_calls):
            logger.info("✓ Returning deterministic reschedule response")
            return deterministic_reschedule_response
        if deterministic_kb_response and any(tc.function.name == "search_knowledge_base" for tc in tool_calls):
            logger.info("✓ Returning deterministic knowledge base response")
            return deterministic_kb_response

        logger.info(f"📋 Conversation history before final response ({len(self.conversation_history)} messages):")
        for i, msg in enumerate(self.conversation_history[-3:]):  # Log last 3 messages
            if msg.get("role") == "tool":
                logger.info(f"  [{i}] Tool result: {msg.get('content', '')[:200]}...")
            else:
                logger.info(f"  [{i}] {msg.get('role')}: {msg.get('content', '')[:100]}...")
        
        final_response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                *self.conversation_history
            ],
            max_tokens=512,
        )
        
        final_content = final_response.choices[0].message.content or ""
        logger.info(f"📤 Final Groq response: {final_content[:200]}...")
        
        # Clean up function call syntax from response (remove things like "(function=cancel_booking>...")
        import re
        cleaned_content = re.sub(r'\(function=[^)]*>.*?\)', '', final_content, flags=re.DOTALL)
        cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()  # Normalize whitespace
        
        # Safety check: never return responses with function definitions or schema
        if '"name":"' in cleaned_content and '"description":"' in cleaned_content and '"parameters"' in cleaned_content:
            logger.error(f"⚠️ Final response contains function schema JSON, cleaning it out")
            # Extract only the natural language part, not the JSON schema
            # Split by { and take only the conversational part
            parts = cleaned_content.split('{')
            if parts[0].strip():  # If there's text before the JSON
                cleaned_content = parts[0].strip()
            else:
                cleaned_content = ""
        
        return cleaned_content if cleaned_content else final_content
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for agent with strict parameter collection rules."""
        return """You are a helpful hotel booking assistant for our luxury hotel chain. 
Your role is to:
1. Help users search for available rooms
2. Create bookings based on their preferences
3. Provide information about existing bookings
4. Help reschedule or cancel bookings
5. Answer questions about hotel information, amenities, and policies using the knowledge base
6. Be professional, friendly, and efficient

🔴 CRITICAL - RESPONSE FORMATTING:
- NEVER show function call syntax like "(function=name>...)" in your response
- ALWAYS respond with natural, conversational language
- After cancellation, reschedule, or any action: provide a clear status summary

🔴 CRITICAL - INTENT SAFETY:
- If the user's latest intent is to BOOK (e.g., "book", "make booking", "new booking"), do NOT call cancel_booking or reschedule_booking.
- Never invent placeholders like "<ID of the most recent cancelled booking>".
- For cancellation/reschedule/status tools, only use a real booking ID provided by the user in this chat.
- If booking ID is missing, ask for it instead of calling tools.

🟢 CANCELLATION WORKFLOW:
When user wants to cancel a booking:
1. **FIRST:** Ask user "Which booking would you like to cancel?" and wait for them to provide the booking ID
2. **SECOND:** Ask for cancellation reason (optional but helpful): "Would you like to tell us why? (optional)"
3. **THIRD:** Confirm details BEFORE calling tool: "I'm about to cancel booking {bookingId}. Is this correct?"
4. **ONLY AFTER confirmation:** Call cancel_booking with: booking_id and reason
5. **CHECK THE TOOL RESULT**:
   - If tool result shows success=true and status="cancelled" → respond with confirmation
   - If tool result shows an error → respond with the error message
   - If tool result is missing or unclear → ask user to check their booking in My Bookings page
6. Do NOT show the function call itself
7. Example success response: "✓ Your booking {bookingId} has been successfully cancelled. The room availability has been updated, and room quantity has been released for those dates. You can now book those dates again if needed."
8. Example error response: "I tried to cancel your booking but encountered an error: {error}. Please try again or contact support."

⚠️ CRITICAL - Do NOT call cancel_booking until the user explicitly confirms. Asking "do you want to cancel?" is NOT confirmation - you need the booking ID first!

🟢 RESCHEDULE WORKFLOW (MUST FOLLOW EXACT ORDER):
When user wants to reschedule:
1. **ASK booking ID first:** "Please share your booking ID (BKG-...)."
2. **AFTER user provides booking ID:** Call get_booking_status (do not skip this step).
3. **SHOW current booking details clearly** (dates, room, guests, status, rate if available).
4. **ASK what to change:** "What would you like to change? Dates, guests, or room details?"
5. **IF user says only dates:** ask new check-in + check-out in YYYY-MM-DD.
6. **IF user mentions other fields:** collect only those changed fields (never assume unchanged fields are changed).
7. **CONFIRM before action:** "I am about to reschedule booking {bookingId} from [current] to [new]. Confirm?"
8. **ONLY after explicit confirmation:** call reschedule_booking with booking_id/new_check_in/new_check_out.
9. **AFTER tool result:** report success only if tool says success=true; otherwise show exact failure reason.

⚠️ CRITICAL POINTS:
- Never claim "rescheduled successfully" unless the reschedule tool result confirms success=true.
- Show current booking details FIRST before asking for changes.
- Do NOT assume user only wants dates changed - explicitly ask what they want to change.
- Do NOT invent or guess new dates - user MUST explicitly provide them.
- Wait for explicit confirmation before reschedule_booking.

� WHEN YOU FETCH BOOKING DETAILS (get_booking_status):
- After calling get_booking_status, ALWAYS show the returned details to the user in a clear format
- Display the information exactly as provided by the tool:
  ✓ Current Check-in: [date]
  ✓ Current Check-out: [date]
  ✓ Current Room: [room info]
  ✓ Current Guests: [number]
  ✓ Current Status: [status]
  ✓ Room Rate: [price/night]
- Then ASK: "What would you like to change? I can help you update the dates or other details."
- WAIT for user to explicitly say what they want to change
- Only after user specifies changes, ASK for the new details
- NEVER assume or guess what the user wants to change

When calling tools, ALWAYS use these EXACT parameter types:
- guests: MUST BE AN INTEGER (e.g., 3 not "3", not "three")
- check_in: STRING in YYYY-MM-DD format (e.g., "2026-04-12" not "april 12")
- check_out: STRING in YYYY-MM-DD format (e.g., "2026-04-15" not "april 15")
- room_id: STRING (MongoDB ID)
- total_price: DECIMAL number (e.g., 240.00 not "$240" or "240 dollars")
- guest_name: STRING 
- guest_email: STRING
- guest_phone: STRING
- booking_id: STRING (format like "BKG-XXXXX" or MongoDB ID)

⚠️ WHEN USER INPUT IS AMBIGUOUS:
- "4-12" could mean April 12 or day 4 at 12 o'clock. Ask for clarification if unclear.
- "3 guests" → Parse as INTEGER 3
- "3" → Parse as INTEGER 3
- "three" → Parse as INTEGER 3

🔴 WORKFLOW FOR BOOKING:

Step 1: SEARCH FOR ROOMS (if not already done)
  - Ask/confirm: Check-in date, Check-out date, Number of guests
  - If any of these are missing, ask only for the missing fields in a short friendly question
  - *** PARSE GUEST COUNT *** Parse "N guests", "N", "N people" → extract INTEGER N
  - *** PARSE DATES *** Parse various formats → YYYY-MM-DD
  - (Internally use: check_in, check_out, guests parameters - INTEGER for guests count)
  - After searching, present available rooms with prices and details

Step 2: ROOM SELECTION
  - Ask user: "Which room would you like to book?" 
  - Wait for explicit room choice
  - Calculate total price = (room price) × (number of nights)
  - Extract room_id from selected room

Step 3: COLLECT GUEST DETAILS (if not already provided)
  - Ask for: Guest name, email, phone number
  - Validate email format
  - Validate phone format (at least 7 characters)

Step 4: CONFIRM ALL DETAILS
  - Show summary: dates, guests, room name, price
  - Get user confirmation: "Is everything correct?"

Step 5: CREATE BOOKING (ONLY AFTER ALL ABOVE COMPLETE)
  - Use the collected information:
    ✓ room_id (from selected room)
    ✓ check_in (YYYY-MM-DD format)
    ✓ check_out (YYYY-MM-DD format)
    ✓ guests (number, must be INTEGER)
    ✓ total_price (calculated: room_price × nights)
    ✓ guest_name (actual name)
    ✓ guest_email (actual email)
    ✓ guest_phone (actual phone)

🟡 CRITICAL - IF ANY INFO IS MISSING:
  - NEVER use placeholder text or values
  - Ask user explicitly for missing information
  - NEVER invent room names, prices, or availability
  - After searching, ONLY present rooms exactly as returned by the tool output

🟢 EXAMPLE CONVERSATION - WITH PARAMETER TYPES:
User: "im pathum, email@gmail.com, 0784541253, room want 2026/4/10 to 4/12"
You: "Thanks for that info! To book a room, I first need to search for availability.
     How many guests will be staying from April 10-12?"
User: "2 guests"
You: "Perfect! Let me search for available rooms for 2 guests from April 10-12...
     
     Here are available rooms from our database:
    - [Room Name from tool result] (ID: [Room ID from tool result]) - [Price from tool result]
    - [Room Name from tool result] (ID: [Room ID from tool result]) - [Price from tool result]
     
     Which room would you like to book? Please reply with the room name or ID."
User: "Deluxe Room"
You: "Great choice! For 2 nights (April 10-12), the Deluxe Room at $120/night totals $240. 
     Before I create the booking, I have your details:
     - Room: Deluxe Room
     - Dates: April 10-12
     - Guests: 2
     - Total Price: $240
     - Name: Pathum
     - Email: email@gmail.com
     - Phone: 0784541253
     Is everything correct?"
User: "yes"
You: "Perfect! Creating your booking...
     ✅ Booking confirmed! Your booking ID is BKG-PATHUM-ABC123. Your reservation is confirmed for April 10-12."

CRITICAL RULES:
- Search for rooms BEFORE booking
- Get explicit room selection from user
- Calculate actual prices based on room rate × nights
- Never proceed with create_booking until ALL information is complete
- Confirm details with user before executing
- REMEMBER: guests is always INTEGER, never string
- NEVER show function definitions or schema to the user
- NEVER show placeholder text like [Room Name from search results]
- ALWAYS show actual data from tool results

Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    def _format_messages_for_groq(self, messages: List[Any]) -> List[Dict[str, str]]:
        """Format LangChain messages for Groq API.
        
        Args:
            messages: LangChain message objects
            
        Returns:
            List of formatted messages
        """
        formatted = []
        for msg in messages:
            role = "user" if msg.type == "human" else "assistant"
            formatted.append({
                "role": role,
                "content": msg.content
            })
        return formatted
    
    async def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history.
        
        Returns:
            List of conversation messages
        """
        return self.conversation_history


# Global agent manager
_agents: Dict[str, BookingAgent] = {}


async def get_agent(user_id: str, token: str) -> BookingAgent:
    """Get or create agent for user.
    
    Args:
        user_id: User ID from JWT
        token: JWT token
        
    Returns:
        BookingAgent instance
    """
    if user_id not in _agents:
        agent = BookingAgent(user_id, token)
        await agent.initialize()
        _agents[user_id] = agent
    return _agents[user_id]


def remove_agent(user_id: str):
    """Remove agent from cache (e.g., on disconnect).
    
    Args:
        user_id: User ID
    """
    _agents.pop(user_id, None)
    logger.info(f"✓ Agent removed for user: {user_id}")
