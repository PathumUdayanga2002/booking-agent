import json
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from config import get_logger
from graph import build_chat_graph
from services import verify_token

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        self.active_connections[user_id] = websocket
        logger.info("WS connected for user %s", user_id)

    async def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        logger.info("WS disconnected for user %s", user_id)

    async def send_personal(self, user_id: str, data: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_json(data)


manager = ConnectionManager()
chat_graph = build_chat_graph()


@router.websocket("/ws/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str, token: str = Query(...)):
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    token_user_id = payload.get("userId")
    if token_user_id != user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User ID mismatch")
        return

    await websocket.accept()
    await manager.connect(user_id, websocket)

    await manager.send_personal(
        user_id,
        {
            "role": "agent",
            "type": "connection",
            "content": "Welcome to LangGraph Booking Assistant! How can I help you today?",
        },
    )

    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            user_message = str(message.get("message", "")).strip()

            if not user_message:
                await manager.send_personal(
                    user_id,
                    {
                        "role": "agent",
                        "type": "error",
                        "content": "Empty message. Please type something.",
                    },
                )
                continue

            state = {
                "user_id": user_id,
                "user_message": user_message,
                "intent": "unknown",
                "conversation_history": [{"role": "user", "content": user_message}],
                "final_response": "",
            }

            result = chat_graph.invoke(state)
            response_text = result.get("final_response", "I could not generate a response.")

            await manager.send_personal(
                user_id,
                {
                    "role": "agent",
                    "type": "message",
                    "content": response_text,
                },
            )
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
    except Exception as exc:
        logger.exception("WebSocket failure for user %s: %s", user_id, exc)
        await manager.disconnect(user_id)
