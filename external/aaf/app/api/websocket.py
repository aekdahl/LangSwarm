"""
WebSocket endpoints for AAF Backend
Real-time chat interface with LangSwarm agents
"""
import logging
import json
import asyncio
from typing import Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi.routing import APIRouter
import uuid
from datetime import datetime

from ..core.langswarm_manager import get_langswarm_manager, LangSwarmManager
from .models import WebSocketMessage, WebSocketChatMessage, StreamChatChunk

logger = logging.getLogger(__name__)


def serialize_message(message: WebSocketMessage) -> dict:
    """Serialize WebSocket message with datetime conversion"""
    data = message.dict()
    if 'timestamp' in data and isinstance(data['timestamp'], datetime):
        data['timestamp'] = data['timestamp'].isoformat()
    return data

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_sessions: Dict[str, str] = {}  # connection_id -> session_id
    
    async def connect(self, websocket: WebSocket, connection_id: str, session_id: Optional[str] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        # Assign or generate session ID
        if not session_id:
            session_id = str(uuid.uuid4())
        self.connection_sessions[connection_id] = session_id
        
        logger.info(f"WebSocket connected: {connection_id} (session: {session_id})")
        
        # Send welcome message
        welcome_msg = WebSocketMessage(
            type="connection",
            data={
                "status": "connected",
                "connection_id": connection_id,
                "session_id": session_id
            }
        )
        await self.send_personal_message(serialize_message(welcome_msg), websocket)
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.connection_sessions:
            session_id = self.connection_sessions[connection_id]
            del self.connection_sessions[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id} (session: {session_id})")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            # Handle datetime serialization
            if isinstance(message, dict):
                serialized_message = self._serialize_datetime(message)
            else:
                serialized_message = message
            await websocket.send_text(json.dumps(serialized_message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
    
    def _serialize_datetime(self, obj):
        """Recursively serialize datetime objects in a dictionary"""
        if isinstance(obj, dict):
            return {key: self._serialize_datetime(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj
    
    async def send_message_to_connection(self, connection_id: str, message: dict):
        """Send a message to a specific connection by ID"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await self.send_personal_message(message, websocket)
    
    def get_session_id(self, connection_id: str) -> Optional[str]:
        """Get session ID for a connection"""
        return self.connection_sessions.get(connection_id)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()

# WebSocket router
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """Main WebSocket endpoint for chat interface"""
    
    connection_id = str(uuid.uuid4())
    langswarm_manager = await get_langswarm_manager()
    
    await manager.connect(websocket, connection_id, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "unknown")
                
                logger.info(f"WebSocket message received: {message_type} from {connection_id}")
                
                if message_type == "chat":
                    await handle_chat_message(
                        connection_id, message_data, langswarm_manager, websocket
                    )
                elif message_type == "ping":
                    await handle_ping_message(connection_id, websocket)
                elif message_type == "get_agents":
                    await handle_get_agents(connection_id, langswarm_manager, websocket)
                elif message_type == "connect":
                    await handle_connect_message(connection_id, message_data, websocket)
                else:
                    error_msg = WebSocketMessage(
                        type="error",
                        data={"error": f"Unknown message type: {message_type}"}
                    )
                    await manager.send_personal_message(serialize_message(error_msg), websocket)
                    
            except json.JSONDecodeError:
                error_msg = WebSocketMessage(
                    type="error", 
                    data={"error": "Invalid JSON format"}
                )
                await manager.send_personal_message(serialize_message(error_msg), websocket)
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                error_msg = WebSocketMessage(
                    type="error",
                    data={"error": f"Server error: {str(e)}"}
                )
                await manager.send_personal_message(serialize_message(error_msg), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(connection_id)


async def handle_chat_message(
    connection_id: str, 
    message_data: dict, 
    langswarm_manager: LangSwarmManager, 
    websocket: WebSocket
):
    """Handle chat messages from WebSocket clients"""
    
    try:
        # Extract chat data
        chat_data = message_data.get("data", {})
        user_message = chat_data.get("message", "")
        agent_id = chat_data.get("agent_id")
        stream = chat_data.get("stream", True)  # Default to streaming for WebSocket
        
        if not user_message.strip():
            error_msg = WebSocketMessage(
                type="error",
                data={"error": "Empty message not allowed"}
            )
            await manager.send_personal_message(serialize_message(error_msg), websocket)
            return
        
        # Get session ID for this connection
        session_id = manager.get_session_id(connection_id)
        
        # Echo user message back to confirm receipt
        user_echo = WebSocketMessage(
            type="user_message",
            data={
                "message": user_message,
                "session_id": session_id,
                "agent_id": agent_id or langswarm_manager.default_agent_id
            }
        )
        await manager.send_personal_message(serialize_message(user_echo), websocket)
        
        if stream:
            # Handle streaming response
            await handle_streaming_chat(
                connection_id, user_message, agent_id, session_id, 
                langswarm_manager, websocket
            )
        else:
            # Handle non-streaming response
            response = await langswarm_manager.chat(
                message=user_message,
                agent_id=agent_id,
                session_id=session_id
            )
            
            response_msg = WebSocketMessage(
                type="agent_response",
                data={
                    "response": response,
                    "agent_id": agent_id or langswarm_manager.default_agent_id,
                    "session_id": session_id,
                    "is_complete": True
                }
            )
            await manager.send_personal_message(serialize_message(response_msg), websocket)
            
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        error_msg = WebSocketMessage(
            type="error",
            data={"error": f"Chat error: {str(e)}"}
        )
        await manager.send_personal_message(error_msg.dict(), websocket)


async def handle_streaming_chat(
    connection_id: str,
    user_message: str, 
    agent_id: Optional[str],
    session_id: str,
    langswarm_manager: LangSwarmManager,
    websocket: WebSocket
):
    """Handle streaming chat responses"""
    
    try:
        # Send typing indicator
        typing_msg = WebSocketMessage(
            type="typing",
            data={
                "agent_id": agent_id or langswarm_manager.default_agent_id,
                "session_id": session_id
            }
        )
        await manager.send_personal_message(serialize_message(typing_msg), websocket)
        
        # Stream the response
        async for chunk in langswarm_manager.chat_stream(
            message=user_message,
            agent_id=agent_id,
            session_id=session_id
        ):
            chunk_msg = WebSocketMessage(
                type="agent_chunk",
                data={
                    "chunk": chunk,
                    "agent_id": agent_id or langswarm_manager.default_agent_id,
                    "session_id": session_id,
                    "is_complete": False
                }
            )
            await manager.send_personal_message(serialize_message(chunk_msg), websocket)
        
        # Send completion marker
        complete_msg = WebSocketMessage(
            type="agent_chunk",
            data={
                "chunk": "",
                "agent_id": agent_id or langswarm_manager.default_agent_id,
                "session_id": session_id,
                "is_complete": True
            }
        )
        await manager.send_personal_message(serialize_message(complete_msg), websocket)
        
    except Exception as e:
        logger.error(f"Error in streaming chat: {e}")
        error_msg = WebSocketMessage(
            type="error",
            data={"error": f"Streaming error: {str(e)}"}
        )
        await manager.send_personal_message(error_msg.dict(), websocket)


async def handle_ping_message(connection_id: str, websocket: WebSocket):
    """Handle ping messages for connection health check"""
    
    pong_msg = WebSocketMessage(
        type="pong",
        data={"timestamp": datetime.utcnow().isoformat()}
    )
    await manager.send_personal_message(serialize_message(pong_msg), websocket)


async def handle_get_agents(
    connection_id: str, 
    langswarm_manager: LangSwarmManager, 
    websocket: WebSocket
):
    """Handle requests for agent information"""
    
    try:
        agents = langswarm_manager.list_agents()
        agents_msg = WebSocketMessage(
            type="agents_list",
            data={
                "agents": agents,
                "default_agent": langswarm_manager.default_agent_id
            }
        )
        await manager.send_personal_message(serialize_message(agents_msg), websocket)
        
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        error_msg = WebSocketMessage(
            type="error",
            data={"error": f"Failed to get agents: {str(e)}"}
        )
        await manager.send_personal_message(error_msg.dict(), websocket)


async def handle_connect_message(connection_id: str, message_data: dict, websocket: WebSocket):
    """Handle connection/handshake messages from WebSocket clients"""
    
    try:
        # Send connection acknowledgment
        connect_ack = WebSocketMessage(
            type="connected",
            data={
                "connection_id": connection_id,
                "status": "ready",
                "message": "WebSocket connection established successfully"
            }
        )
        await manager.send_personal_message(serialize_message(connect_ack), websocket)
        logger.info(f"Connection acknowledged for {connection_id}")
        
    except Exception as e:
        logger.error(f"Error handling connect message: {e}")
        error_msg = WebSocketMessage(
            type="error",
            data={"error": f"Connection failed: {str(e)}"}
        )
        await manager.send_personal_message(serialize_message(error_msg), websocket)


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return {
        "active_connections": manager.get_connection_count(),
        "timestamp": datetime.utcnow().isoformat()
    }
