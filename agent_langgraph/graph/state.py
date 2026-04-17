from typing import Any, Dict, List, Optional, TypedDict


class ChatMessage(TypedDict):
    role: str
    content: str


class ChatState(TypedDict):
    user_id: str
    token: str
    user_message: str
    intent: str
    active_intent: Optional[str]
    stage: Optional[str]
    slots: Dict[str, Any]
    conversation_history: List[ChatMessage]
    final_response: str
