"""
Chat API endpoints for AAF Backend
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json
import uuid

from ..core.langswarm_manager import get_langswarm_manager, LangSwarmManager
from .models import ChatRequest, ChatResponse, StreamChatChunk, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
@router.post("", response_model=ChatResponse)  # Handle requests without trailing slash
async def chat(
    request: ChatRequest,
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Send a chat message to an agent and get a response
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get response from agent
        response = await manager.chat(
            message=request.message,
            agent_id=request.agent_id,
            session_id=session_id
        )
        
        # Determine which agent was used
        agent_id = request.agent_id or manager.default_agent_id
        
        return ChatResponse(
            response=response,
            agent_id=agent_id,
            session_id=session_id,
            metadata=request.metadata
        )
        
    except ValueError as e:
        logger.error(f"Chat request validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Stream a chat response from an agent
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Determine which agent will be used
        agent_id = request.agent_id or manager.default_agent_id
        
        async def generate_stream():
            """Generate streaming response"""
            try:
                async for chunk in manager.chat_stream(
                    message=request.message,
                    agent_id=request.agent_id,
                    session_id=session_id
                ):
                    chunk_data = StreamChatChunk(
                        chunk=chunk,
                        agent_id=agent_id,
                        session_id=session_id,
                        is_complete=False
                    )
                    yield f"data: {chunk_data.json()}\n\n"
                
                # Send completion marker
                final_chunk = StreamChatChunk(
                    chunk="",
                    agent_id=agent_id,
                    session_id=session_id,
                    is_complete=True
                )
                yield f"data: {final_chunk.json()}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_chunk = {
                    "error": str(e),
                    "agent_id": agent_id,
                    "session_id": session_id
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except ValueError as e:
        logger.error(f"Stream request validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Stream request failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/agents")
async def list_agents(
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    List all available agents
    """
    try:
        agents = manager.list_agents()
        return {"agents": agents}
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/agents/{agent_id}")
async def get_agent_info(
    agent_id: str,
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Get information about a specific agent
    """
    try:
        agent = manager.get_agent(agent_id)
        
        agent_info = {
            "id": getattr(agent, 'name', agent_id),
            "model": getattr(agent, 'model', 'unknown'),
            "behavior": getattr(agent, 'specialization', 'helpful'),
            "is_conversational": True,  # LLM agents are conversational
            "has_memory": hasattr(agent, 'memory') and agent.memory is not None,
            "has_tools": False,  # Basic LLM doesn't have tools
            "system_prompt": getattr(agent, 'system_prompt', None)
        }
        
        return agent_info
        
    except ValueError as e:
        logger.error(f"Agent not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Failed to get agent info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/{session_id}/reset")
async def reset_session(
    session_id: str,
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Reset a conversation session (clear history)
    """
    try:
        # Delete the session from BigQuery
        success = await manager.delete_session(session_id)
        
        if success:
            return {"message": f"Session {session_id} reset successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
        
    except Exception as e:
        logger.error(f"Failed to reset session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}")
async def get_session_info(
    session_id: str,
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Get information about a conversation session
    """
    try:
        session = await manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session["session_id"],
            "agent_id": session.get("agent_id"),
            "created_at": session["created_at"],
            "last_activity": session["last_activity"],
            "expires_at": session["expires_at"],
            "data": session.get("data", {}),
            "user_context": session.get("user_context", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions")
async def list_sessions(
    limit: int = 50,
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    List active sessions
    """
    try:
        sessions = await manager.list_active_sessions()
        
        # Limit results
        if limit and len(sessions) > limit:
            sessions = sessions[:limit]
        
        return {
            "sessions": sessions,
            "count": len(sessions),
            "limited": limit < len(sessions) if limit else False
        }
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/stats")
async def get_session_stats(
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Get session statistics
    """
    try:
        stats = await manager.get_session_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
