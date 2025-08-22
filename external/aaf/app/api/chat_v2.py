"""
Chat API v2 - JWT-based authentication for AAF Widget
Designed for the new widget/SPA architecture with tenant-based configuration
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import jwt

from ..core.langswarm_manager import get_langswarm_manager, LangSwarmManager
from ..core.config import get_settings
from .tenant_ui import get_current_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat-v2"])


class ChatMessage(BaseModel):
    """Chat message request"""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User message text")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="File attachments")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Chat response"""
    turn_id: str = Field(..., description="Turn identifier")
    message: str = Field(..., description="Assistant response")
    streamed: bool = Field(default=False, description="Whether response was streamed")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls made")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")


class TypingRequest(BaseModel):
    """Typing indicator request"""
    session_id: str = Field(..., description="Session identifier")
    typing: bool = Field(..., description="Whether user is typing")


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str = Field(..., description="Message type")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")


# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


@router.post("/send", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    session_data: Dict[str, Any] = Depends(get_current_session),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Send a chat message and get response
    
    Requires valid JWT authentication. Supports file attachments and metadata.
    """
    try:
        # Validate session matches token
        if message.session_id != session_data["sid"]:
            raise HTTPException(
                status_code=403,
                detail="Session ID mismatch"
            )
        
        # Generate turn ID
        import uuid
        turn_id = f"turn_{uuid.uuid4().hex[:8]}"
        
        # Prepare message for LangSwarm
        chat_kwargs = {
            "session_id": message.session_id,
            "turn_id": turn_id
        }
        
        # Add metadata if present
        if message.metadata:
            chat_kwargs.update(message.metadata)
        
        # Handle attachments if present
        if message.attachments:
            chat_kwargs["attachments"] = message.attachments
        
        # Send to LangSwarm
        response = manager.chat(message.message, **chat_kwargs)
        
        # Log interaction
        logger.info(
            f"Chat interaction - Tenant: {session_data['tid']}, "
            f"Session: {message.session_id}, Turn: {turn_id}"
        )
        
        return ChatResponse(
            turn_id=turn_id,
            message=response,
            streamed=False,
            tool_calls=None,  # TODO: Extract tool calls from LangSwarm response
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": session_data["tid"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.post("/send/stream")
async def send_message_stream(
    message: ChatMessage,
    session_data: Dict[str, Any] = Depends(get_current_session),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Send a chat message and stream the response
    
    Returns Server-Sent Events (SSE) format for streaming responses.
    """
    try:
        # Validate session
        if message.session_id != session_data["sid"]:
            raise HTTPException(status_code=403, detail="Session ID mismatch")
        
        # Generate turn ID
        import uuid
        turn_id = f"turn_{uuid.uuid4().hex[:8]}"
        
        async def stream_response():
            """Stream chat response as SSE"""
            try:
                # Send initial event
                yield f"data: {json.dumps({'type': 'start', 'turn_id': turn_id})}\n\n"
                
                # Prepare streaming kwargs
                chat_kwargs = {
                    "session_id": message.session_id,
                    "turn_id": turn_id,
                    "stream": True
                }
                
                if message.metadata:
                    chat_kwargs.update(message.metadata)
                
                # Stream from LangSwarm
                if hasattr(manager, 'chat_stream'):
                    async for chunk in manager.chat_stream(message.message, **chat_kwargs):
                        chunk_data = {
                            "type": "token",
                            "turn_id": turn_id,
                            "content": chunk
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                else:
                    # Fallback to non-streaming
                    response = manager.chat(message.message, **chat_kwargs)
                    chunk_data = {
                        "type": "message",
                        "turn_id": turn_id,
                        "content": response
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send completion event
                completion_data = {
                    "type": "complete",
                    "turn_id": turn_id,
                    "metadata": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "tenant_id": session_data["tid"]
                    }
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                
            except Exception as e:
                # Send error event
                error_data = {
                    "type": "error",
                    "turn_id": turn_id,
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Authorization, Content-Type"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Streaming chat failed: {str(e)}"
        )


@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
    authorization: str = Header(...)
):
    """
    WebSocket endpoint for real-time chat
    
    Supports bidirectional communication with typing indicators,
    message streaming, and connection management.
    """
    try:
        # Verify JWT token
        from .tenant_ui import verify_jwt_token
        session_data = verify_jwt_token(authorization)
        
        # Validate session
        if session_id != session_data["sid"]:
            await websocket.close(code=1008, reason="Session ID mismatch")
            return
        
        await websocket.accept()
        active_connections[session_id] = websocket
        
        logger.info(f"WebSocket connected - Session: {session_id}, Tenant: {session_data['tid']}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "status",
            "state": "connected",
            "session_id": session_id,
            "tenant_id": session_data["tid"]
        })
        
        # Get LangSwarm manager
        manager = await get_langswarm_manager().__anext__()
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "message":
                    await handle_websocket_message(
                        websocket, data, session_data, manager
                    )
                elif message_type == "typing":
                    await handle_typing_indicator(
                        websocket, data, session_data
                    )
                elif message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    })
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected - Session: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error - Session: {session_id}, Error: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
    finally:
        # Cleanup
        if session_id in active_connections:
            del active_connections[session_id]


async def handle_websocket_message(
    websocket: WebSocket,
    data: Dict[str, Any],
    session_data: Dict[str, Any],
    manager: LangSwarmManager
):
    """Handle incoming chat message via WebSocket"""
    try:
        message_text = data.get("text", "")
        if not message_text:
            await websocket.send_json({
                "type": "error",
                "message": "Message text is required"
            })
            return
        
        # Generate turn ID
        import uuid
        turn_id = f"turn_{uuid.uuid4().hex[:8]}"
        
        # Send typing indicator
        await websocket.send_json({
            "type": "typing",
            "typing": True,
            "agent": True
        })
        
        # Prepare chat kwargs
        chat_kwargs = {
            "session_id": session_data["sid"],
            "turn_id": turn_id
        }
        
        # Add attachments if present
        if "attachments" in data:
            chat_kwargs["attachments"] = data["attachments"]
        
        # Stream response if supported
        if hasattr(manager, 'chat_stream'):
            try:
                async for chunk in manager.chat_stream(message_text, **chat_kwargs):
                    await websocket.send_json({
                        "type": "token",
                        "turn_id": turn_id,
                        "content": chunk
                    })
                
                # Send completion
                await websocket.send_json({
                    "type": "complete",
                    "turn_id": turn_id,
                    "typing": False
                })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "turn_id": turn_id,
                    "message": str(e)
                })
        else:
            # Fallback to regular chat
            response = manager.chat(message_text, **chat_kwargs)
            
            await websocket.send_json({
                "type": "message",
                "turn_id": turn_id,
                "content": response,
                "typing": False
            })
        
    except Exception as e:
        logger.error(f"WebSocket message handling error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


async def handle_typing_indicator(
    websocket: WebSocket,
    data: Dict[str, Any],
    session_data: Dict[str, Any]
):
    """Handle typing indicator from client"""
    try:
        typing = data.get("typing", False)
        
        # Echo typing status back (for multi-user scenarios)
        await websocket.send_json({
            "type": "typing",
            "typing": typing,
            "user": True,
            "session_id": session_data["sid"]
        })
        
    except Exception as e:
        logger.error(f"Typing indicator error: {e}")


@router.post("/typing")
async def set_typing_status(
    typing_req: TypingRequest,
    session_data: Dict[str, Any] = Depends(get_current_session)
):
    """
    Set typing indicator status
    
    Alternative to WebSocket for typing indicators.
    """
    try:
        # Validate session
        if typing_req.session_id != session_data["sid"]:
            raise HTTPException(status_code=403, detail="Session ID mismatch")
        
        # If WebSocket is active, send typing status
        if typing_req.session_id in active_connections:
            websocket = active_connections[typing_req.session_id]
            await websocket.send_json({
                "type": "typing",
                "typing": typing_req.typing,
                "user": True
            })
        
        return {"status": "ok", "typing": typing_req.typing}
        
    except Exception as e:
        logger.error(f"Typing status error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set typing status: {str(e)}"
        )


@router.post("/read-receipt")
async def mark_as_read(
    session_id: str,
    turn_id: str,
    session_data: Dict[str, Any] = Depends(get_current_session)
):
    """
    Mark message as read
    
    Used for read receipt functionality.
    """
    try:
        # Validate session
        if session_id != session_data["sid"]:
            raise HTTPException(status_code=403, detail="Session ID mismatch")
        
        # If WebSocket is active, send read receipt
        if session_id in active_connections:
            websocket = active_connections[session_id]
            await websocket.send_json({
                "type": "read_receipt",
                "turn_id": turn_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {"status": "ok", "turn_id": turn_id}
        
    except Exception as e:
        logger.error(f"Read receipt error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark as read: {str(e)}"
        )


@router.get("/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    offset: int = 0,
    session_data: Dict[str, Any] = Depends(get_current_session),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Get chat history for a session
    
    Returns paginated message history.
    """
    try:
        # Validate session
        if session_id != session_data["sid"]:
            raise HTTPException(status_code=403, detail="Session ID mismatch")
        
        # Get session info from manager
        if hasattr(manager, 'get_session'):
            session_info = await manager.get_session(session_id)
            if not session_info:
                raise HTTPException(status_code=404, detail="Session not found")
        
        # This would typically fetch from your message storage
        # For now, return a placeholder response
        return {
            "session_id": session_id,
            "messages": [],  # TODO: Implement message history retrieval
            "total": 0,
            "limit": limit,
            "offset": offset,
            "has_more": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.get("/sessions/{session_id}/transcript")
async def download_transcript(
    session_id: str,
    format: str = "txt",
    session_data: Dict[str, Any] = Depends(get_current_session)
):
    """
    Download chat transcript
    
    Supports multiple formats: txt, json, csv
    """
    try:
        # Validate session
        if session_id != session_data["sid"]:
            raise HTTPException(status_code=403, detail="Session ID mismatch")
        
        if format not in ["txt", "json", "csv"]:
            raise HTTPException(status_code=400, detail="Invalid format")
        
        # TODO: Implement transcript generation
        # This would fetch message history and format it appropriately
        
        transcript_content = f"Chat transcript for session {session_id}\n"
        transcript_content += f"Generated: {datetime.utcnow().isoformat()}\n"
        transcript_content += "=" * 50 + "\n\n"
        transcript_content += "No messages found.\n"
        
        return StreamingResponse(
            iter([transcript_content.encode()]),
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=chat_transcript_{session_id}.{format}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcript download error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download transcript: {str(e)}"
        )
