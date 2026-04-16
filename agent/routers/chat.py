"""WebSocket Chat Router for booking agent."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, status
from fastapi.security import HTTPBearer
import json
from typing import Dict, Set
from utils.logger import get_logger
from agents.booking_agent import get_agent, remove_agent
from config.settings import settings
import jwt

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

# Connection manager for WebSocket
class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Store WebSocket connection (already accepted in endpoint)."""
        # Note: websocket.accept() is called in the endpoint, not here
        # to avoid double-accept which causes 403 errors
        self.active_connections[user_id] = websocket
        logger.info(f"✓ WebSocket connection stored: {user_id}")
    
    async def disconnect(self, user_id: str):
        """Remove WebSocket connection."""
        self.active_connections.pop(user_id, None)
        remove_agent(user_id)
        logger.info(f"✓ WebSocket disconnected: {user_id}")
    
    async def send_personal(self, user_id: str, data: dict):
        """Send message to specific user."""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(data)
    
    async def broadcast(self, data: dict):
        """Broadcast to all connected users."""
        for connection in self.active_connections.values():
            await connection.send_json(data)


manager = ConnectionManager()


def verify_token(token: str) -> Dict:
    """Verify JWT token and extract user info.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token data (None if invalid)
    """
    try:
        if not token:
            logger.error(f"🔐 No token provided")
            return None
            
        logger.info(f"🔐 Verifying WebSocket token: {token[:30]}...")
        
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        logger.info(f"🔐 Token decoded successfully")
        logger.info(f"🔐 Payload: {payload}")
        
        # Check for userId field
        user_id = payload.get("userId")
        if not user_id:
            logger.error(f"🔐 No 'userId' in token payload. Keys: {payload.keys()}")
            return None
        
        logger.info(f"✓ Token verified for user: {user_id}, Role: {payload.get('role', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError as e:
        logger.error(f"🔐 Token expired: {str(e)}")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"🔐 Invalid token format: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"🔐 Token verification error: {type(e).__name__}: {str(e)}", exc_info=True)
        return None


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time chat.
    
    Args:
        websocket: WebSocket connection
        user_id: User ID from path
        token: JWT token from query parameter
    """
    try:
        logger.info(f"🔌 WebSocket connection request from user: {user_id}")
        logger.info(f"🔌 Token received: {token[:30]}...")
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            logger.error(f"✗ Token verification failed for user: {user_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
        
        token_user_id = payload.get("userId")
        logger.info(f"🔌 Token user ID: {token_user_id}, Request user ID: {user_id}")
        
        # Validate user_id matches token
        if token_user_id != user_id:
            logger.error(f"✗ User ID mismatch: {user_id} vs {token_user_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User ID mismatch")
            return
        
        # Accept connection
        await websocket.accept()
        logger.info(f"✓ WebSocket accepted for user: {user_id}")
        
        # Connect and initialize agent
        await manager.connect(user_id, websocket)
        agent = await get_agent(user_id, token)
        
        logger.info(f"✓ Agent initialized for user: {user_id}")
        
        # Send welcome message
        await manager.send_personal(user_id, {
            "role": "agent",
            "type": "connection",
            "content": "Welcome to Hotel Booking Assistant! How can I help you today?"
        })
        
        logger.info(f"📨 Welcome message sent to user: {user_id}")
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            user_message = message.get("message", "").strip()
            if not user_message:
                await manager.send_personal(user_id, {
                    "role": "agent",
                    "type": "error",
                    "content": "Empty message. Please type something."
                })
                continue
            
            logger.info(f"📩 Message from {user_id}: {user_message[:50]}...")
            
            try:
                # Process message with agent
                response = await agent.process_message(user_message)
                
                # Send response
                await manager.send_personal(user_id, {
                    "role": "agent",
                    "type": "message",
                    "content": response
                })
                logger.info(f"📤 Response sent to {user_id}: {response[:50]}...")
                
            except Exception as e:
                logger.error(f"✗ Error processing message: {e}")
                await manager.send_personal(user_id, {
                    "role": "agent",
                    "type": "error",
                    "content": f"Sorry, I encountered an error: {str(e)}"
                })
    
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
        logger.info(f"✓ User {user_id} disconnected")
    
    except Exception as e:
        logger.error(f"✗ WebSocket error for {user_id}: {e}")
        await manager.disconnect(user_id)


@router.get("/history/{user_id}")
async def get_conversation_history(
    user_id: str,
    token: str = Query(...)
):
    """Get conversation history for a user.
    
    Args:
        user_id: User ID
        token: JWT token
        
    Returns:
        List of conversation messages
    """
    try:
        # Verify token
        payload = verify_token(token)
        
        # Validate user_id matches token
        if payload.get("userId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID does not match token"
            )
        
        # Get or create agent
        agent = await get_agent(user_id, token)
        history = await agent.get_conversation_history()
        
        logger.info(f"✓ Retrieved conversation history for {user_id} ({len(history)} messages)")
        
        return {
            "user_id": user_id,
            "message_count": len(history),
            "messages": history
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error retrieving history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )


@router.post("/clear/{user_id}")
async def clear_conversation(
    user_id: str,
    token: str = Query(...)
):
    """Clear conversation history for a user.
    
    Args:
        user_id: User ID
        token: JWT token
        
    Returns:
        Confirmation message
    """
    try:
        # Verify token
        payload = verify_token(token)
        
        # Validate user_id matches token
        if payload.get("userId") != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID does not match token"
            )
        
        # Clear agent and memory
        remove_agent(user_id)
        
        logger.info(f"✓ Cleared conversation for {user_id}")
        
        return {
            "status": "success",
            "message": "Conversation cleared"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Error clearing conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear conversation"
        )
