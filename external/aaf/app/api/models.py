"""
Pydantic models for API requests and responses
"""
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


# Chat API Models
class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    agent_id: Optional[str] = Field(None, description="Specific agent ID to use")
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    stream: bool = Field(False, description="Whether to stream the response")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="Agent response")
    agent_id: str = Field(..., description="ID of the agent that responded")
    session_id: str = Field(..., description="Session ID used for the conversation")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")


class StreamChatChunk(BaseModel):
    """Streaming chat chunk model"""
    chunk: str = Field(..., description="Response chunk")
    agent_id: str = Field(..., description="ID of the agent responding")
    session_id: str = Field(..., description="Session ID")
    is_complete: bool = Field(False, description="Whether this is the final chunk")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Agent Management Models
class AgentInfo(BaseModel):
    """Agent information model"""
    id: str = Field(..., description="Agent ID")
    model: str = Field(..., description="LLM model used")
    behavior: str = Field(..., description="Agent behavior type")
    is_conversational: bool = Field(..., description="Whether agent maintains conversation history")
    has_memory: bool = Field(..., description="Whether agent has memory enabled")
    has_tools: bool = Field(..., description="Whether agent has tools available")


class AgentConfigRequest(BaseModel):
    """Agent configuration request model"""
    id: str = Field(..., description="Agent ID")
    agent_type: str = Field(default="langchain-openai", description="Agent type")
    model: str = Field(..., description="LLM model to use")
    behavior: str = Field(default="helpful", description="Agent behavior")
    system_prompt: Optional[str] = Field(None, description="System prompt for the agent")
    memory: Optional[Dict[str, Any]] = Field(None, description="Memory configuration")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Tool configurations")
    retrievers: Optional[List[Dict[str, Any]]] = Field(None, description="Retriever configurations")
    is_conversational: bool = Field(True, description="Enable conversation history")
    max_history_length: int = Field(20, description="Maximum conversation history length")


# Configuration Management Models
class ConfigurationResponse(BaseModel):
    """Configuration response model"""
    config: Dict[str, Any] = Field(..., description="Current LangSwarm configuration")
    agents: List[AgentInfo] = Field(..., description="List of configured agents")


class ConfigurationUpdateRequest(BaseModel):
    """Configuration update request model"""
    config: Dict[str, Any] = Field(..., description="New LangSwarm configuration")


# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message model"""
    type: str = Field(..., description="Message type (chat, ping, etc.)")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WebSocketChatMessage(BaseModel):
    """WebSocket chat message model"""
    message: str = Field(..., description="User message")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


# Session Management Models
class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str = Field(..., description="Session ID")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")
    message_count: int = Field(..., description="Number of messages in session")
    agent_id: str = Field(..., description="Primary agent for the session")


# Error Models
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Health Check Models
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    langswarm_status: str = Field(..., description="LangSwarm manager status")
    agents_count: int = Field(..., description="Number of active agents")


# Management API Models
class RestartRequest(BaseModel):
    """Restart request model"""
    force: bool = Field(False, description="Force restart even if there are active sessions")
    backup_config: bool = Field(True, description="Backup current configuration before restart")


class RestartResponse(BaseModel):
    """Restart response model"""
    success: bool = Field(..., description="Whether restart was successful")
    message: str = Field(..., description="Restart status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agents_reinitialized: int = Field(..., description="Number of agents reinitialized")


# Tool and Prompt Management Models
class ToolConfigRequest(BaseModel):
    """Tool configuration request model"""
    name: str = Field(..., description="Tool name")
    type: str = Field(..., description="Tool type")
    config: Dict[str, Any] = Field(..., description="Tool configuration")
    enabled: bool = Field(True, description="Whether tool is enabled")


class PromptTemplate(BaseModel):
    """Prompt template model"""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    template: str = Field(..., description="Prompt template content")
    variables: List[str] = Field(..., description="Template variables")
    description: Optional[str] = Field(None, description="Template description")


class ModelConfigRequest(BaseModel):
    """Model configuration request model"""
    model_name: str = Field(..., description="Model name")
    provider: str = Field(..., description="Model provider (openai, anthropic, etc.)")
    config: Dict[str, Any] = Field(..., description="Model configuration parameters")
    enabled: bool = Field(True, description="Whether model is enabled")
