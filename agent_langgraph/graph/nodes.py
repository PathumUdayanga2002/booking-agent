import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from graph.state import ChatState
from services import get_express_client


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


def detect_intent_node(state: ChatState) -> ChatState:
    message = state.get("user_message", "").lower()
    active_intent = state.get("active_intent")

    if active_intent:
        state["intent"] = active_intent
        return state

    if any(word in message for word in ["book", "reserve", "booking"]):
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
            state["final_response"] = "Please share your booking ID and I will help you cancel it safely."
        elif intent == "reschedule":
            state["final_response"] = "Please share your booking ID and your new check-in/check-out dates."
        elif intent == "knowledge":
            state["final_response"] = "I understood this as a hotel information question. Knowledge retrieval will be added in the next parity slice."
        else:
            state["final_response"] = f"I received: {message}"
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
