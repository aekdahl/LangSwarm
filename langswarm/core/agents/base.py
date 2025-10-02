"""
LangSwarm V2 Base Agent Implementation

Provides concrete implementations of the agent interfaces and base classes
that provider-specific agents can inherit from or compose with.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncIterator
import uuid

from .interfaces import (
    IAgent, IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, AgentStatus, ProviderType
)
from ..observability.auto_instrumentation import (
    AutoInstrumentedMixin, auto_trace_operation, auto_record_metric, auto_log_operation
)

logger = logging.getLogger(__name__)


@dataclass
class AgentConfiguration:
    """Concrete implementation of agent configuration"""
    
    provider: ProviderType
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    timeout: Optional[int] = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Advanced configuration
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    
    # Tool configuration
    tools_enabled: bool = False
    available_tools: List[str] = field(default_factory=list)
    tool_choice: Optional[str] = None  # "auto", "none", or specific tool name
    
    # Memory configuration
    memory_enabled: bool = False
    max_memory_messages: int = 50
    memory_summary_enabled: bool = False
    
    # Streaming configuration
    streaming_enabled: bool = False
    stream_chunk_size: int = 1024
    
    # Provider-specific configuration
    provider_config: Dict[str, Any] = field(default_factory=dict)
    
    # OpenAI-specific parameters
    base_url: Optional[str] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    tool_choice: Optional[str] = None
    
    # Capabilities
    _capabilities: Optional[List[AgentCapability]] = field(default=None, init=False)
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        """Get supported capabilities based on configuration"""
        if self._capabilities is not None:
            return self._capabilities
        
        caps = [AgentCapability.TEXT_GENERATION]
        
        if self.tools_enabled:
            caps.extend([AgentCapability.FUNCTION_CALLING, AgentCapability.TOOL_USE])
        
        if self.streaming_enabled:
            caps.append(AgentCapability.STREAMING)
        
        if self.memory_enabled:
            caps.extend([AgentCapability.MEMORY, AgentCapability.CONVERSATION_HISTORY])
        
        if self.system_prompt:
            caps.append(AgentCapability.SYSTEM_PROMPTS)
        
        # Provider-specific capabilities
        if self.provider == ProviderType.OPENAI:
            if "gpt-4" in self.model.lower() and "vision" in self.model.lower():
                caps.append(AgentCapability.VISION)
            if "dall-e" in self.model.lower():
                caps.append(AgentCapability.IMAGE_GENERATION)
        
        self._capabilities = caps
        return caps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "api_key": "***" if self.api_key else None,  # Mask API key
            "base_url": self.base_url,
            "system_prompt": self.system_prompt,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "tools_enabled": self.tools_enabled,
            "memory_enabled": self.memory_enabled,
            "streaming_enabled": self.streaming_enabled,
            "capabilities": [cap.value for cap in self.capabilities],
            "provider_config": self.provider_config
        }
    
    def validate(self) -> bool:
        """Validate the configuration"""
        if not self.model:
            raise ValueError("Model name is required")
        
        if self.temperature is not None and not (0.0 <= self.temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        return True


@dataclass
class AgentResponse:
    """Concrete implementation of agent response"""
    
    content: str
    message: AgentMessage
    usage: Optional[AgentUsage] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[Exception] = None
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def success_response(
        cls,
        content: str,
        role: str = "assistant",
        usage: Optional[AgentUsage] = None,
        **metadata
    ) -> 'AgentResponse':
        """Create a successful response"""
        message = AgentMessage(role=role, content=content)
        return cls(
            content=content,
            message=message,
            usage=usage,
            metadata=metadata,
            success=True
        )
    
    @classmethod
    def error_response(
        cls,
        error: Exception,
        content: str = "",
        **metadata
    ) -> 'AgentResponse':
        """Create an error response"""
        message = AgentMessage(role="system", content=f"Error: {content or str(error)}")
        return cls(
            content=content,
            message=message,
            metadata=metadata,
            success=False,
            error=error
        )


class AgentSession(IAgentSession):
    """Concrete implementation of agent session"""
    
    def __init__(self, session_id: Optional[str] = None, max_messages: int = 50):
        self._session_id = session_id or str(uuid.uuid4())
        self._messages: List[AgentMessage] = []
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._max_messages = max_messages
        self._lock = asyncio.Lock()
    
    @property
    def session_id(self) -> str:
        return self._session_id
    
    @property
    def messages(self) -> List[AgentMessage]:
        return self._messages.copy()
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    async def add_message(self, message: AgentMessage) -> None:
        """Add a message to the session"""
        async with self._lock:
            self._messages.append(message)
            self._updated_at = datetime.now()
            
            # Trim messages if we exceed the limit
            if len(self._messages) > self._max_messages:
                # Keep the system message if it exists
                system_messages = [msg for msg in self._messages if msg.role == "system"]
                other_messages = [msg for msg in self._messages if msg.role != "system"]
                
                # Keep the most recent messages
                keep_count = self._max_messages - len(system_messages)
                if keep_count > 0:
                    self._messages = system_messages + other_messages[-keep_count:]
                else:
                    self._messages = system_messages
    
    async def clear_messages(self) -> None:
        """Clear all messages from the session"""
        async with self._lock:
            self._messages.clear()
            self._updated_at = datetime.now()
    
    async def get_context(self, max_tokens: Optional[int] = None) -> List[AgentMessage]:
        """Get conversation context within token limit"""
        if max_tokens is None:
            return self.messages
        
        # Simple token estimation (4 characters ≈ 1 token)
        total_tokens = 0
        context_messages = []
        
        # Include system messages first
        system_messages = [msg for msg in self._messages if msg.role == "system"]
        for msg in system_messages:
            msg_tokens = len(msg.content) // 4
            if total_tokens + msg_tokens <= max_tokens:
                context_messages.append(msg)
                total_tokens += msg_tokens
        
        # Include recent messages in reverse order
        other_messages = [msg for msg in self._messages if msg.role != "system"]
        for msg in reversed(other_messages):
            msg_tokens = len(msg.content) // 4
            if total_tokens + msg_tokens <= max_tokens:
                context_messages.insert(-len(system_messages) if system_messages else 0, msg)
                total_tokens += msg_tokens
            else:
                break
        
        return context_messages


@dataclass
class AgentMetadata:
    """Metadata about an agent instance"""
    
    agent_id: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "2.0.0"
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Statistics
    total_messages: int = 0
    total_tokens_used: int = 0
    total_sessions: int = 0
    last_used: Optional[datetime] = None
    
    # Performance metrics
    average_response_time: float = 0.0
    success_rate: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "description": self.description,
            "tags": self.tags,
            "statistics": {
                "total_messages": self.total_messages,
                "total_tokens_used": self.total_tokens_used,
                "total_sessions": self.total_sessions,
                "last_used": self.last_used.isoformat() if self.last_used else None,
                "average_response_time": self.average_response_time,
                "success_rate": self.success_rate
            }
        }


class BaseAgent(AutoInstrumentedMixin):
    """Base implementation of the V2 agent interface with automatic instrumentation"""
    
    def __init__(
        self,
        name: str,
        configuration: AgentConfiguration,
        provider: IAgentProvider,
        agent_id: Optional[str] = None
    ):
        self._agent_id = agent_id or str(uuid.uuid4())
        self._name = name
        self._configuration = configuration
        self._provider = provider
        self._status = AgentStatus.INITIALIZING
        self._sessions: Dict[str, IAgentSession] = {}
        self._current_session: Optional[IAgentSession] = None
        self._metadata = AgentMetadata(agent_id=self._agent_id, name=name)
        self._tools: Dict[str, Any] = {}
        self._logger = logging.getLogger(f"langswarm.agent.{name}")
        
        # Performance tracking
        self._response_times: List[float] = []
        self._success_count = 0
        self._total_count = 0
        
        # Set component name for auto-instrumentation
        self._component_name = "agent"
        
        # Initialize auto-instrumentation mixin
        super().__init__()
    
    # Properties
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def configuration(self) -> IAgentConfiguration:
        return self._configuration
    
    @property
    def provider(self) -> IAgentProvider:
        return self._provider
    
    @property
    def status(self) -> AgentStatus:
        return self._status
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return self._configuration.capabilities
    
    @property
    def current_session(self) -> Optional[IAgentSession]:
        return self._current_session
    
    # Core functionality
    async def initialize(self) -> None:
        """Initialize the agent with automatic instrumentation"""
        with self._auto_trace("initialize", 
                             agent_id=self._agent_id, 
                             agent_name=self._name,
                             provider=str(self._configuration.provider),
                             model=self._configuration.model) as span:
            
            try:
                self._auto_log("info", f"Initializing agent {self.name}", 
                              agent_id=self._agent_id, provider=str(self._configuration.provider))
                
                # Validate configuration
                self._configuration.validate()
                
                # Validate provider configuration
                await self._provider.validate_configuration(self._configuration)
                
                self._status = AgentStatus.READY
                
                # Record initialization metrics
                self._auto_record_metric("initializations_total", 1.0, "counter",
                                       agent_name=self._name, 
                                       provider=str(self._configuration.provider),
                                       status="success")
                
                if span:
                    span.add_tag("initialization_status", "success")
                
                self._auto_log("info", f"Agent {self.name} initialized successfully",
                              agent_id=self._agent_id, status="ready")
                
            except Exception as e:
                self._status = AgentStatus.ERROR
                
                # Record error metrics
                self._auto_record_metric("initializations_total", 1.0, "counter",
                                       agent_name=self._name,
                                       provider=str(self._configuration.provider),
                                       status="error")
                
                if span:
                    span.add_tag("initialization_status", "error")
                    span.add_tag("error_type", type(e).__name__)
                    span.set_status("error")
                
                self._auto_log("error", f"Failed to initialize agent {self.name}: {e}",
                              agent_id=self._agent_id, error_type=type(e).__name__)
                raise
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully"""
        self._logger.info(f"Shutting down agent {self.name}")
        
        # Close all sessions
        for session in self._sessions.values():
            if hasattr(session, 'close'):
                await session.close()
        
        self._sessions.clear()
        self._current_session = None
        self._status = AgentStatus.DISCONNECTED
        
        self._logger.info(f"Agent {self.name} shutdown complete")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "provider": self.configuration.provider.value,
            "model": self.configuration.model,
            "capabilities": [cap.value for cap in self.capabilities],
            "sessions": {
                "total": len(self._sessions),
                "current": self._current_session.session_id if self._current_session else None
            },
            "tools": {
                "registered": len(self._tools),
                "names": list(self._tools.keys())
            },
            "performance": {
                "average_response_time": self._get_average_response_time(),
                "success_rate": self._get_success_rate(),
                "total_messages": self._metadata.total_messages
            },
            "timestamp": datetime.now().isoformat()
        }
    
    # Session management
    async def create_session(self, session_id: Optional[str] = None) -> IAgentSession:
        """Create a new conversation session"""
        session = AgentSession(
            session_id=session_id,
            max_messages=self._configuration.max_memory_messages
        )
        
        self._sessions[session.session_id] = session
        self._current_session = session
        self._metadata.total_sessions += 1
        
        # Add system prompt if configured
        if self._configuration.system_prompt:
            system_message = AgentMessage(
                role="system",
                content=self._configuration.system_prompt
            )
            await session.add_message(system_message)
        
        self._logger.info(f"Created session {session.session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[IAgentSession]:
        """Get an existing session"""
        return self._sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            if self._current_session and self._current_session.session_id == session_id:
                self._current_session = None
            self._logger.info(f"Deleted session {session_id}")
            return True
        return False
    
    async def list_sessions(self) -> List[str]:
        """List all session IDs"""
        return list(self._sessions.keys())
    
    # Conversation
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> IAgentResponse:
        """Send a chat message with automatic instrumentation"""
        start_time = time.time()
        
        with self._auto_trace("chat",
                             agent_id=self._agent_id,
                             agent_name=self._name,
                             provider=str(self._configuration.provider),
                             model=self._configuration.model,
                             session_id=session_id,
                             message_length=len(message),
                             has_tools=self._configuration.tools_enabled) as span:
            
            try:
                self._auto_log("info", f"Processing chat message for agent {self.name}",
                              agent_id=self._agent_id, 
                              session_id=session_id,
                              message_length=len(message))
                
                # Get or create session
                if session_id:
                    session = await self.get_session(session_id)
                    if not session:
                        raise ValueError(f"Session {session_id} not found")
                else:
                    session = self._current_session
                    if not session:
                        session = await self.create_session()
                
                # Create user message
                user_message = AgentMessage(role="user", content=message)
                await session.add_message(user_message)
                
                # Set status to busy
                self._status = AgentStatus.BUSY
                
                if span:
                    span.add_tag("session_id", session.session_id)
                    span.add_tag("message_role", "user")
                    span.add_tag("input_length", len(message))
                
                # Send message to provider (this is where the actual LLM call happens)
                with self._auto_trace("provider_call",
                                     provider=str(self._configuration.provider),
                                     model=self._configuration.model) as provider_span:
                    
                    response = await self._provider.send_message(
                        user_message, session, self._configuration
                    )
                    
                    if provider_span and response:
                        provider_span.add_tag("response_success", response.success)
                        if response.usage:
                            provider_span.add_tag("input_tokens", response.usage.input_tokens)
                            provider_span.add_tag("output_tokens", response.usage.output_tokens)
                            provider_span.add_tag("total_tokens", response.usage.total_tokens)
                
                # Add response to session
                if response.success and response.message:
                    await session.add_message(response.message)
                
                # Calculate metrics
                duration = time.time() - start_time
                
                # Update statistics
                self._update_statistics(duration, response.success)
                
                # Record detailed metrics
                self._auto_record_metric("chat_requests_total", 1.0, "counter",
                                       agent_name=self._name,
                                       provider=str(self._configuration.provider),
                                       model=self._configuration.model,
                                       status="success" if response.success else "error")
                
                self._auto_record_metric("chat_duration_seconds", duration, "histogram",
                                       agent_name=self._name,
                                       provider=str(self._configuration.provider),
                                       model=self._configuration.model)
                
                self._auto_record_metric("chat_input_length", len(message), "histogram",
                                       agent_name=self._name)
                
                if response.usage:
                    self._auto_record_metric("chat_input_tokens", response.usage.input_tokens, "histogram",
                                           agent_name=self._name, provider=str(self._configuration.provider))
                    self._auto_record_metric("chat_output_tokens", response.usage.output_tokens, "histogram",
                                           agent_name=self._name, provider=str(self._configuration.provider))
                    self._auto_record_metric("chat_total_tokens", response.usage.total_tokens, "histogram",
                                           agent_name=self._name, provider=str(self._configuration.provider))
                
                # Reset status
                self._status = AgentStatus.READY
                
                if span:
                    span.add_tag("chat_success", response.success)
                    span.add_tag("response_length", len(response.content) if response.content else 0)
                    span.add_tag("duration_ms", duration * 1000)
                    if response.usage:
                        span.add_tag("total_tokens", response.usage.total_tokens)
                
                self._auto_log("info", f"Chat completed for agent {self.name}",
                              agent_id=self._agent_id,
                              session_id=session.session_id,
                              success=response.success,
                              duration_ms=duration * 1000)
                
                return response
                
            except Exception as e:
                self._status = AgentStatus.ERROR
                duration = time.time() - start_time
                self._update_statistics(duration, False)
                
                # Record error metrics
                self._auto_record_metric("chat_requests_total", 1.0, "counter",
                                       agent_name=self._name,
                                       provider=str(self._configuration.provider),
                                       model=self._configuration.model,
                                       status="error")
                
                self._auto_record_metric("chat_errors_total", 1.0, "counter",
                                       agent_name=self._name,
                                       error_type=type(e).__name__)
                
                if span:
                    span.add_tag("chat_success", False)
                    span.add_tag("error_type", type(e).__name__)
                    span.add_tag("error_message", str(e))
                    span.set_status("error")
                
                self._auto_log("error", f"Chat error for agent {self.name}: {e}",
                              agent_id=self._agent_id,
                              session_id=session_id,
                              error_type=type(e).__name__)
                
                return AgentResponse.error_response(e)
    
    async def stream_chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[IAgentResponse]:
        """Stream a chat response"""
        if not self._configuration.streaming_enabled:
            # Fallback to regular chat
            response = await self.chat(message, session_id, **kwargs)
            yield response
            return
        
        start_time = time.time()
        
        try:
            # Get or create session
            if session_id:
                session = await self.get_session(session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")
            else:
                session = self._current_session
                if not session:
                    session = await self.create_session()
            
            # Create user message
            user_message = AgentMessage(role="user", content=message)
            await session.add_message(user_message)
            
            # Set status to busy
            self._status = AgentStatus.BUSY
            
            # Stream response from provider
            full_content = ""
            async for chunk in self._provider.stream_message(
                user_message, session, self._configuration
            ):
                if chunk.success:
                    full_content += chunk.content
                yield chunk
            
            # Add complete response to session
            if full_content:
                complete_message = AgentMessage(role="assistant", content=full_content)
                await session.add_message(complete_message)
            
            # Update statistics
            self._update_statistics(time.time() - start_time, True)
            
            # Reset status
            self._status = AgentStatus.READY
            
        except Exception as e:
            self._status = AgentStatus.ERROR
            self._update_statistics(time.time() - start_time, False)
            self._logger.error(f"Stream chat error: {e}")
            yield AgentResponse.error_response(e)
    
    # Tool integration
    async def register_tool(self, tool: Any) -> bool:
        """Register a tool with the agent"""
        try:
            tool_name = getattr(tool, 'name', str(tool))
            self._tools[tool_name] = tool
            self._logger.info(f"Registered tool: {tool_name}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to register tool: {e}")
            return False
    
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            self._logger.info(f"Unregistered tool: {tool_name}")
            return True
        return False
    
    async def list_tools(self) -> List[str]:
        """List registered tools"""
        return list(self._tools.keys())
    
    # V2 System integration
    async def process_through_middleware(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IAgentResponse:
        """Process message through V2 middleware pipeline"""
        try:
            from langswarm.core.middleware import create_default_pipeline
            from langswarm.core.middleware.context import RequestContext, RequestType
            
            # Create middleware pipeline
            pipeline = create_default_pipeline()
            
            # Create request context
            request_context = RequestContext(
                action_id=f"agent.{self.name}.chat",
                method="chat",
                request_type=RequestType.TOOL_CALL,  # Use existing request type
                params={"message": message},
                metadata={
                    "agent_id": self.agent_id,
                    "agent_name": self.name,
                    "provider": self.configuration.provider.value,
                    "model": self.configuration.model,
                    **(context or {})
                }
            )
            
            # Process through middleware
            response = await pipeline.process(request_context)
            
            if response.is_success():
                # If middleware handled it, create agent response
                return AgentResponse.success_response(
                    content=str(response.result),
                    metadata={
                        "middleware_processed": True,
                        "middleware_status": response.status.value,
                        "processing_time": response.processing_time
                    }
                )
            else:
                # If middleware failed, fall back to direct chat
                self._logger.warning("Middleware processing failed, falling back to direct chat")
                return await self.chat(message)
                
        except Exception as e:
            self._logger.error(f"Middleware processing error: {e}")
            # Fall back to direct chat
            return await self.chat(message)
    
    async def get_health(self) -> Dict[str, Any]:
        """Get agent health status and metrics"""
        try:
            # Get basic agent info
            health = {
                "agent_id": self.agent_id,
                "name": self.name,
                "status": self.status.value,
                "provider": self.configuration.provider.value,
                "model": self.configuration.model,
                "capabilities": [cap.value for cap in self.capabilities],
                "tools_registered": len(self._tools),
                "sessions_active": len(self._sessions),
                "total_messages": self._metadata.total_messages,
                "success_rate": self._get_success_rate(),
                "average_response_time": self._get_average_response_time(),
                "created_at": self._metadata.created_at.isoformat() if self._metadata.created_at else None,
                "last_used": self._metadata.last_used.isoformat() if self._metadata.last_used else None,
                "timestamp": datetime.now().isoformat()
            }
            
            # Try to get provider-specific health info
            try:
                provider_health = await self._provider.get_health()
                health["provider_health"] = provider_health
            except Exception as e:
                health["provider_health"] = {"error": str(e)}
            
            return health
            
        except Exception as e:
            self._logger.error(f"Health check failed: {e}")
            return {
                "agent_id": self.agent_id,
                "name": self.name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # Helper methods
    def _update_statistics(self, response_time: float, success: bool) -> None:
        """Update performance statistics"""
        self._response_times.append(response_time)
        self._total_count += 1
        if success:
            self._success_count += 1
        
        self._metadata.total_messages += 1
        self._metadata.last_used = datetime.now()
        self._metadata.average_response_time = self._get_average_response_time()
        self._metadata.success_rate = self._get_success_rate()
    
    def _get_average_response_time(self) -> float:
        """Calculate average response time"""
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times)
    
    def _get_success_rate(self) -> float:
        """Calculate success rate"""
        if self._total_count == 0:
            return 1.0
        return self._success_count / self._total_count
    
    # Tool management methods
    async def add_tools(self, tool_names: List[str]) -> None:
        """Add tools to the agent - provider handles integration"""
        self._configuration.available_tools.extend(tool_names)
        self._configuration.tools_enabled = True
        self._logger.info(f"Added tools to agent {self.name}: {tool_names}")
    
    async def set_tools(self, tool_names: List[str]) -> None:
        """Set tools for the agent - provider handles integration"""
        self._configuration.available_tools = tool_names
        self._configuration.tools_enabled = len(tool_names) > 0
        self._logger.info(f"Set tools for agent {self.name}: {tool_names}")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return self._configuration.available_tools.copy()
