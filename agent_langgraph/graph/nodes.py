from graph.state import ChatState


def detect_intent_node(state: ChatState) -> ChatState:
    message = state.get("user_message", "").lower()

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


def generate_response_node(state: ChatState) -> ChatState:
    intent = state.get("intent", "general")
    message = state.get("user_message", "")

    if intent == "book":
        reply = "I can help with booking. Please share check-in date, check-out date, and guest count."
    elif intent == "cancel":
        reply = "Please share your booking ID and I will help you cancel it safely."
    elif intent == "reschedule":
        reply = "Please share your booking ID and your new check-in/check-out dates."
    elif intent == "knowledge":
        reply = (
            "I understood this as a hotel information question. "
            "In the next phase, this node will call vector search and return grounded knowledge answers."
        )
    else:
        reply = f"I received: {message}"

    state["final_response"] = reply
    return state
