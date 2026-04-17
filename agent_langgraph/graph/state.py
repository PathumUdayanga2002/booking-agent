from typing import List, TypedDict


class ChatMessage(TypedDict):
    role: str
    content: str


class ChatState(TypedDict):
    user_id: str
    user_message: str
    intent: str
    conversation_history: List[ChatMessage]
    final_response: str
