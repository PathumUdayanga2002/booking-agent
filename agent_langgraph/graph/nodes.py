import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from graph.state import ChatState
from services import get_express_client
from services import VectorStoreService, KNOWLEDGE_BASE_COLLECTION


def _extract_guest_count(text: str) -> Optional[int]:
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


def _extract_email(text: str) -> Optional[str]:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(r"(?:\+?\d[\d\s\-()]{6,}\d)", text)
    if not match:
        return None
    phone = match.group(0).strip()
    digits = re.sub(r"\D", "", phone)
    return phone if len(digits) >= 7 else None


def _extract_name(text: str) -> Optional[str]:
    lowered = text.lower().strip()
    explicit = re.search(
        r"(?:my\s+name\s+is|name\s+is|i\s+am|i'm)\s+([a-z][a-z\s.'-]{1,60})",
        lowered,
    )
    if explicit:
        candidate = re.split(r"[,;]|\b(?:email|phone|mobile)\b", explicit.group(1), maxsplit=1)[0]
        candidate = re.sub(r"\s+", " ", candidate).strip(" .,-")
        if re.fullmatch(r"[a-zA-Z][a-zA-Z\s.'-]{1,60}", candidate):
            return candidate.title()
    return None


def _extract_iso_dates(text: str) -> List[str]:
    return re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)


def _extract_booking_id(text: str) -> Optional[str]:
    match = re.search(r"\b(BKG-[A-Za-z0-9-]{6,}|[a-fA-F0-9]{24})\b", text)
    return match.group(1) if match else None


def _is_knowledge_query(text: str) -> bool:
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
        "what is",
        "what are",
        "tell me about",
    ]
    return any(word in normalized for word in kb_words)


def _format_knowledge_response(query: str, docs: List[Dict[str, Any]]) -> str:
    if not docs:
        return (
            "I couldn't find that detail in the current hotel knowledge base. "
            "Please rephrase your question, for example: hotel name, room categories, check-in time, spa, or policies."
        )

    top_docs = docs[:3]
    normalized_chunks: List[str] = []
    for doc in top_docs:
        raw_text = str(doc.get("text", "") or "")
        cleaned = re.sub(r"---\s*Page\s*\d+\s*---", " ", raw_text, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if cleaned:
            normalized_chunks.append(cleaned)

    if not normalized_chunks:
        return (
            "I found related knowledge entries but they were empty after processing. "
            "Please ask your question again with a little more detail."
        )

    merged = " ".join(normalized_chunks)
    sentences = re.split(r"(?<=[.!?])\s+", merged)
    selected: List[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue
        selected.append(sentence)
        if len(selected) == 4:
            break

    if not selected:
        selected = [merged[:500].strip()]

    bullet_lines = [f"- {line}" for line in selected]
    return "\n".join(
        [
            f"Here is what I found in our hotel knowledge base for: '{query}'",
            *bullet_lines,
            "If you want, I can also answer a more specific follow-up about this topic.",
        ]
    )


def _calculate_total_price(check_in: str, check_out: str, price_per_night: float) -> float:
    check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
    check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
    nights = (check_out_date - check_in_date).days
    if nights <= 0:
        raise ValueError("Check-out date must be after check-in date")
    return round(float(price_per_night) * nights, 2)


def _is_negative_confirmation(text: str) -> bool:
    lowered = text.lower().strip()
    tokens = set(re.findall(r"[a-z]+", lowered))
    negatives = {"no", "not", "cancel", "stop", "wrong"}
    return len(tokens) <= 4 and any(word in tokens for word in negatives)


def _is_explicit_confirmation(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    tokens = set(re.findall(r"[a-z]+", normalized))
    confirmation_words = {"yes", "confirm", "confirmed", "correct", "true", "ok", "okay", "sure"}
    return bool(tokens) and len(tokens) <= 3 and any(word in tokens for word in confirmation_words)


def _is_valid_booking_identifier(booking_id: str) -> bool:
    if not isinstance(booking_id, str):
        return False
    normalized = booking_id.strip()
    if not normalized:
        return False

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


def _format_search_rooms_response(arguments: Dict[str, Any], rooms: List[Dict[str, Any]]) -> str:
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
        lines.append(
            f"- {room.get('name', 'Unknown Room')} (ID: {room.get('_id', 'N/A')}) - "
            f"${room.get('pricePerNight', 'N/A')}/night (available {room.get('availableUnits', 0)}/{room.get('totalUnits', 0)})"
        )
    lines.append("Which room would you like to book? Please reply with the room name or ID from this list.")
    return "\n".join(lines)


def _select_room_from_message(message: str, rooms: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    lowered = message.lower()
    for room in rooms:
        room_id = str(room.get("_id", ""))
        room_name = str(room.get("name", "")).lower()
        if room_id and room_id.lower() in lowered:
            return room
        if room_name and room_name in lowered:
            return room
    return None


def _format_booking_status_response(result: Dict[str, Any], requested_booking_id: str) -> str:
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
    return "\n".join(lines)


def _format_reschedule_response(result: Dict[str, Any], arguments: Dict[str, Any]) -> str:
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
    updated_check_in = booking.get("checkIn") or booking.get("check_out") or new_check_in
    updated_check_out = booking.get("checkOut") or booking.get("check_out") or new_check_out
    updated_booking_ref = booking.get("bookingId") or booking.get("_id") or booking_id

    old_range = f"{old_check_in} to {old_check_out}" if old_check_in and old_check_out else "previous dates"
    return (
        f"✓ Your booking `{updated_booking_ref}` has been successfully rescheduled.\n"
        f"- Previous dates: {old_range}\n"
        f"- New dates: {updated_check_in} to {updated_check_out}\n"
        "The booking record has been updated in the system."
    )


def detect_intent_node(state: ChatState) -> ChatState:
    message = state.get("user_message", "").lower()
    active_intent = state.get("active_intent")

    if active_intent:
        state["intent"] = active_intent
        return state

    if _is_knowledge_query(message):
        intent = "knowledge"
    elif any(word in message for word in ["book", "reserve", "booking"]):
        intent = "book"
    elif any(word in message for word in ["cancel", "cancell"]):
        intent = "cancel"
    elif any(word in message for word in ["reschedule", "change", "modify"]):
        intent = "reschedule"
    elif any(word in message for word in ["hotel", "room", "amenities", "contact", "policy"]):
        intent = "knowledge"
    else:
        intent = "general"

    state["intent"] = intent
    return state


async def handle_intent_node(state: ChatState) -> ChatState:
    intent = state.get("intent", "general")
    message = state.get("user_message", "")
    slots = state.get("slots", {})
    stage = state.get("stage")

    if intent != "book" and not state.get("active_intent"):
        if intent == "cancel":
            state["active_intent"] = "cancel"
            state["stage"] = "need_booking_id"
            state["slots"] = {}
            state["final_response"] = "Please share your booking ID and I will help you cancel it safely."
            return state
        elif intent == "reschedule":
            state["active_intent"] = "reschedule"
            state["stage"] = "need_booking_id"
            state["slots"] = {}
            state["final_response"] = "Please share your booking ID and your new check-in/check-out dates."
            return state
        elif intent == "knowledge":
            try:
                docs = await VectorStoreService.search(
                    KNOWLEDGE_BASE_COLLECTION,
                    message,
                    limit=8,
                    score_threshold=0.15,
                )
                state["final_response"] = _format_knowledge_response(message, docs)
            except Exception:
                state["final_response"] = (
                    "I understood this as a hotel information question, but the knowledge service is currently unavailable. "
                    "Please try again shortly."
                )
        else:
            state["final_response"] = f"I received: {message}"
        return state

    if state.get("active_intent") == "cancel":
        client = await get_express_client()
        stage = state.get("stage")
        if stage == "need_booking_id":
            booking_id = _extract_booking_id(message) or message.strip()
            if not _is_valid_booking_identifier(booking_id):
                state["final_response"] = "Please share your booking ID (example: BKG-ABC123 or a 24-char booking ID)."
                return state

            slots["booking_id"] = booking_id
            result = await client.get_booking(booking_id, state["token"])
            slots["booking"] = result
            state["slots"] = slots
            state["stage"] = "confirm_cancel"
            state["final_response"] = f"{_format_booking_status_response(result, booking_id)}\n\nDo you want me to cancel this booking now?"
            return state

        if stage == "confirm_cancel":
            if _is_negative_confirmation(message):
                state["active_intent"] = None
                state["stage"] = None
                state["slots"] = {}
                state["final_response"] = "Understood. I will keep your booking unchanged."
                return state

            if not _is_explicit_confirmation(message):
                state["final_response"] = "Please reply with 'yes' to confirm cancellation, or 'no' to keep this booking."
                return state

            booking_id = slots.get("booking_id", "")
            result = await client.cancel_booking(
                booking_id=booking_id,
                token=state["token"],
                reason="Cancelled via LangGraph assistant",
            )
            booking_ref = (
                result.get("booking", {}).get("bookingId")
                or result.get("booking", {}).get("id")
                or booking_id
            )
            state["active_intent"] = None
            state["stage"] = None
            state["slots"] = {}
            state["final_response"] = f"Your booking {booking_ref} has been cancelled successfully."
            return state

    if state.get("active_intent") == "reschedule":
        client = await get_express_client()
        stage = state.get("stage")

        if stage == "need_booking_id":
            booking_id = _extract_booking_id(message) or message.strip()
            if not _is_valid_booking_identifier(booking_id):
                state["final_response"] = "Please share your booking ID first (example: BKG-ABC123)."
                return state

            slots["booking_id"] = booking_id
            result = await client.get_booking(booking_id, state["token"])
            slots["booking"] = result
            state["slots"] = slots
            state["stage"] = "collect_reschedule_changes"
            state["final_response"] = (
                f"{_format_booking_status_response(result, booking_id)}\n\n"
                "Please provide the new check-in and check-out dates. "
                "If you also want to update guest count/name/email/phone, include them in the same message."
            )
            return state

        if stage == "collect_reschedule_changes":
            iso_dates = _extract_iso_dates(message)
            if len(iso_dates) >= 2:
                slots["new_check_in"] = iso_dates[0]
                slots["new_check_out"] = iso_dates[1]

            guest_count = _extract_guest_count(message)
            if guest_count is not None:
                slots["new_guests"] = guest_count

            name = _extract_name(message)
            email = _extract_email(message)
            phone = _extract_phone(message)
            if name:
                slots["new_guest_name"] = name
            if email:
                slots["new_guest_email"] = email
            if phone:
                slots["new_guest_phone"] = phone

            if not slots.get("new_check_in") or not slots.get("new_check_out"):
                state["final_response"] = "Please provide the new check-in and check-out dates in YYYY-MM-DD format."
                state["slots"] = slots
                return state

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

            state["stage"] = "confirm_reschedule"
            state["slots"] = slots
            state["final_response"] = (
                "Please confirm your reschedule request:\n"
                f"- Booking ID: {slots['booking_id']}\n"
                f"- New check-in: {slots['new_check_in']}\n"
                f"- New check-out: {slots['new_check_out']}"
                f"{optional_text}\n"
                "Reply 'yes' to confirm or 'no' to cancel this update."
            )
            return state

        if stage == "confirm_reschedule":
            if _is_negative_confirmation(message):
                state["active_intent"] = None
                state["stage"] = None
                state["slots"] = {}
                state["final_response"] = "No changes were made. Your booking remains unchanged."
                return state

            if not _is_explicit_confirmation(message):
                state["final_response"] = "Please reply with 'yes' to confirm reschedule, or 'no' to cancel."
                return state

            result = await client.reschedule_booking(
                booking_id=slots["booking_id"],
                new_check_in=slots["new_check_in"],
                new_check_out=slots["new_check_out"],
                token=state["token"],
                new_guests=slots.get("new_guests"),
                new_guest_name=slots.get("new_guest_name"),
                new_guest_email=slots.get("new_guest_email"),
                new_guest_phone=slots.get("new_guest_phone"),
            )

            response = _format_reschedule_response(
                result,
                {
                    "booking_id": slots["booking_id"],
                    "new_check_in": slots["new_check_in"],
                    "new_check_out": slots["new_check_out"],
                },
            )
            state["active_intent"] = None
            state["stage"] = None
            state["slots"] = {}
            state["final_response"] = response
            return state

    if not state.get("active_intent"):
        state["active_intent"] = "book"
        stage = "collect_search"
        state["stage"] = stage

    iso_dates = _extract_iso_dates(message)
    if len(iso_dates) >= 2:
        slots["check_in"] = iso_dates[0]
        slots["check_out"] = iso_dates[1]
    guests = _extract_guest_count(message)
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
            state["slots"] = slots
            state["final_response"] = (
                "Sure, I can help with your booking. "
                f"Please share your {', '.join(missing)}. "
                "Example: 2026-04-20 to 2026-04-28 for 3 guests."
            )
            return state

        client = await get_express_client()
        rooms = await client.search_rooms(
            check_in=slots["check_in"],
            check_out=slots["check_out"],
            guests=int(slots["guests"]),
        )
        slots["rooms"] = rooms
        state["slots"] = slots
        state["stage"] = "select_room"
        state["final_response"] = _format_search_rooms_response(
            {
                "check_in": slots["check_in"],
                "check_out": slots["check_out"],
                "guests": slots["guests"],
            },
            rooms,
        )
        return state

    if stage == "select_room":
        selected = _select_room_from_message(message, slots.get("rooms", []))
        if not selected:
            state["slots"] = slots
            state["final_response"] = "Please choose a room from the list by room name or room ID."
            return state

        slots["selected_room"] = selected
        state["stage"] = "collect_guest_details"

    if state.get("stage") == "collect_guest_details":
        name = _extract_name(message)
        email = _extract_email(message)
        phone = _extract_phone(message)
        if name:
            slots["guest_name"] = name
        if email:
            slots["guest_email"] = email
        if phone:
            slots["guest_phone"] = phone

        missing = [field for field in ["guest_name", "guest_email", "guest_phone"] if not slots.get(field)]
        if missing:
            state["slots"] = slots
            state["final_response"] = "I still need your full name, email, and phone number to continue the booking."
            return state

        selected_room = slots.get("selected_room", {})
        total_price = _calculate_total_price(
            slots["check_in"],
            slots["check_out"],
            float(selected_room.get("pricePerNight", 0)),
        )
        slots["total_price"] = total_price
        state["stage"] = "confirm_booking"
        state["slots"] = slots
        state["final_response"] = (
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
        return state

    if state.get("stage") == "confirm_booking":
        if _is_negative_confirmation(message):
            state["active_intent"] = None
            state["stage"] = None
            state["slots"] = {}
            state["final_response"] = "No problem. I have stopped this booking flow. Tell me your updated details when you are ready."
            return state

        if not _is_explicit_confirmation(message):
            state["slots"] = slots
            state["final_response"] = "Please reply with 'yes' to confirm this booking, or 'no' to cancel this booking flow."
            return state

        selected_room = slots.get("selected_room", {})
        client = await get_express_client()
        result = await client.create_booking(
            token=state["token"],
            room_id=str(selected_room.get("_id")),
            check_in=slots["check_in"],
            check_out=slots["check_out"],
            guests=int(slots["guests"]),
            total_price=float(slots["total_price"]),
            guest_name=slots["guest_name"],
            guest_email=slots["guest_email"],
            guest_phone=slots["guest_phone"],
        )
        booking_data = result.get("booking", result) if isinstance(result, dict) else {}
        booking_ref = booking_data.get("bookingId") or booking_data.get("_id") or "N/A"

        check_in = slots["check_in"]
        check_out = slots["check_out"]
        guests = slots["guests"]

        state["active_intent"] = None
        state["stage"] = None
        state["slots"] = {}
        state["final_response"] = (
            f"Your booking is confirmed. Booking ID: {booking_ref}. "
            f"Stay: {check_in} to {check_out} for {guests} guest(s)."
        )
        return state

    state["slots"] = slots
    state["final_response"] = "I can help with booking. Please share check-in date, check-out date, and guest count."
    return state
