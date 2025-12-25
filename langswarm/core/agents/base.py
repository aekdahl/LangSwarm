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
from typing import Any, Dict, List, Optional, AsyncIterator, TYPE_CHECKING
import uuid

from .interfaces import (
    IAgent, IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, AgentStatus, ProviderType
)
from ..observability.auto_instrumentation import (
    AutoInstrumentedMixin, auto_trace_operation, auto_record_metric, auto_log_operation
)

# Type hint for memory manager without importing (avoid circular imports)
if TYPE_CHECKING:
    from langswarm.core.memory import IMemoryManager

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
    max_tool_iterations: int = 10  # Maximum iterations for tool call refinement
    
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
    """
    Concrete implementation of agent response.
    
    IMPORTANT: response.content and response.message.content are ALWAYS kept in sync.
    Users can access either one and get the same value:
    
    ```python
    result = await agent.chat("Hello")
    
    # Both access methods return the same content:
    print(result.content)          # "Hi there!"
    print(result.message.content)  # "Hi there!"
    ```
    
    The __post_init__ validator ensures consistency is maintained.
    """
    
    content: str
    message: AgentMessage
    usage: Optional[AgentUsage] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[Exception] = None
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Ensure response.content and response.message.content are always in sync"""
        if self.message and self.message.content != self.content:
            # Log warning but auto-correct to maintain consistency
            logger.warning(
                f"AgentResponse content mismatch detected and auto-corrected: "
                f"response.content='{self.content[:50]}...' != "
                f"response.message.content='{self.message.content[:50]}...'"
            )
            # Use message.content as source of truth
            object.__setattr__(self, 'content', self.message.content)
    
    @classmethod
    def success_response(
        cls,
        content: str,
        role: str = "assistant",
        usage: Optional[AgentUsage] = None,
        message: Optional[AgentMessage] = None,
        **metadata
    ) -> 'AgentResponse':
        """Create a successful response"""
        # Use provided message or create a new one
        if message is None:
            message = AgentMessage(role=role, content=content)
        
        # CRITICAL: Ensure response.content and response.message.content are ALWAYS in sync
        # Use message.content as the source of truth if a message is provided
        final_content = message.content if message else content
        
        return cls(
            content=final_content,
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
        # Filter out any None values that may have been added
        return [msg for msg in self._messages if msg is not None]
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    async def add_message(self, message: AgentMessage) -> None:
        """Add a message to the session"""
        if message is None:
            logging.getLogger(__name__).warning("Attempted to add None message to session, ignoring")
            return
        async with self._lock:
            self._messages.append(message)
            self._updated_at = datetime.now()
            
            # Trim messages if we exceed the limit
            if len(self._messages) > self._max_messages:
                # Keep the system message if it exists (filter out None values)
                system_messages = [msg for msg in self._messages if msg is not None and msg.role == "system"]
                other_messages = [msg for msg in self._messages if msg is not None and msg.role != "system"]
                
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
        
        # Include system messages first (filter out None values)
        system_messages = [msg for msg in self._messages if msg is not None and msg.role == "system"]
        for msg in system_messages:
            msg_tokens = len(msg.content) // 4
            if total_tokens + msg_tokens <= max_tokens:
                context_messages.append(msg)
                total_tokens += msg_tokens
        
        # Include recent messages in reverse order (filter out None values)
        other_messages = [msg for msg in self._messages if msg is not None and msg.role != "system"]
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
    
    # Hierarchy support
    parent_id: Optional[str] = None  # ID of parent agent (for sub-agents)
    
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
            "parent_id": self.parent_id,
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
        agent_id: Optional[str] = None,
        memory_manager: Optional["IMemoryManager"] = None
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
        
        # External memory manager for persistent session storage
        self._memory_manager: Optional["IMemoryManager"] = memory_manager
        
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
                
                # Start memory manager if configured
                if self._memory_manager:
                    await self._memory_manager.start()
                    self._logger.info(f"Started memory manager for agent {self.name}")
                
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
        
        # Stop memory manager if configured
        if self._memory_manager:
            await self._memory_manager.stop()
            self._logger.info(f"Stopped memory manager for agent {self.name}")
            
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
    
    async def _get_or_create_session(self, session_id: Optional[str] = None) -> IAgentSession:
        """
        Get or create a session with two-level caching strategy:
        1. Check local in-memory cache first (fast path)
        2. If external memory exists, try to restore session from persistent storage
        3. Create new session if not found anywhere
        
        Args:
            session_id: Optional session ID. If None, uses current session or creates new one.
            
        Returns:
            The session (existing or newly created)
        """
        # If no session_id provided, use current session or create new one
        if session_id is None:
            if self._current_session:
                return self._current_session
            return await self.create_session()
        
        # Level 1: Check local in-memory cache first (fast path)
        if session_id in self._sessions:
            session = self._sessions[session_id]
            self._current_session = session
            return session
        
        # Level 2: If external memory exists, try to restore session
        if self._memory_manager:
            try:
                external_session = await self._memory_manager.get_session(session_id)
                if external_session:
                    # Load messages from external into local AgentSession
                    messages = await external_session.get_messages()
                    local_session = await self.create_session(session_id=session_id)
                    
                    # Convert external messages to AgentMessages and populate session
                    # Skip system message if already added by create_session
                    has_system = any(m is not None and m.role == "system" for m in local_session.messages)
                    
                    for msg in messages:
                        # Skip None messages and system messages if we already have one
                        if msg is None:
                            continue
                        if msg.role.value == "system" and has_system:
                            continue
                        
                        agent_msg = AgentMessage(
                            role=msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                            content=msg.content,
                            metadata=msg.metadata if hasattr(msg, 'metadata') else {}
                        )
                        await local_session.add_message(agent_msg)
                    
                    self._logger.info(f"Restored session {session_id} from external memory with {len(messages)} messages")
                    return local_session
            except Exception as e:
                self._logger.warning(f"Failed to restore session from external memory: {e}")
        
        # Level 3: Create new session
        return await self.create_session(session_id=session_id)
    
    async def _persist_to_memory(self, session: IAgentSession, message: AgentMessage) -> None:
        """
        Persist a message to external memory (write-through caching).
        
        Args:
            session: The local session
            message: The message to persist
        """
        if not self._memory_manager:
            return
        
        try:
            # Get or create external session
            external_session = await self._memory_manager.get_or_create_session(
                session_id=session.session_id,
                agent_id=self._agent_id
            )
            
            # Import Message class from memory module
            from langswarm.core.memory import Message, MessageRole
            
            # Convert role string to MessageRole enum
            role_map = {
                "user": MessageRole.USER,
                "assistant": MessageRole.ASSISTANT,
                "system": MessageRole.SYSTEM,
                "tool": MessageRole.TOOL if hasattr(MessageRole, 'TOOL') else MessageRole.SYSTEM
            }
            role = role_map.get(message.role, MessageRole.USER) if message is not None else MessageRole.USER
            
            # Create memory Message and add to external session
            memory_message = Message(
                role=role,
                content=message.content,
                metadata=message.metadata if hasattr(message, 'metadata') else {}
            )
            await external_session.add_message(memory_message)
            
            self._logger.debug(f"Persisted message to external memory for session {session.session_id}")
            
        except Exception as e:
            # Don't fail the main operation if persistence fails
            self._logger.warning(f"Failed to persist message to external memory: {e}")
    
    async def _execute_tool_calls(
        self,
        response: IAgentResponse,
        session: IAgentSession
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute tool calls from response and add results to session.
        Returns list of tool results if tools were executed, None otherwise.
        Does NOT call back to LLM - this must be done by caller.
        """
        try:
            # Add the assistant's message with tool calls to session (if not None)
            if response.message is not None:
                await session.add_message(response.message)
                # Persist assistant's tool call message to external memory
                await self._persist_to_memory(session, response.message)
            else:
                self._logger.warning("Response message is None, skipping session add")
            
            # Get tool registry
            from langswarm.tools.registry import ToolRegistry
            registry = ToolRegistry()
            
            # Execute each tool call
            tool_results = []
            for tool_call in response.message.tool_calls:
                try:
                    # Extract tool information
                    if hasattr(tool_call, 'function'):
                        # OpenAI format
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        tool_call_id = tool_call.id
                    elif isinstance(tool_call, dict):
                        # Dictionary format
                        tool_name = tool_call.get('name') or tool_call.get('function', {}).get('name')
                        args_str = tool_call.get('arguments') or tool_call.get('function', {}).get('arguments', '{}')
                        tool_args = json.loads(args_str) if isinstance(args_str, str) else args_str
                        tool_call_id = tool_call.get('id', f"call_{int(time.time())}")
                    else:
                        self._logger.error(f"Unknown tool_call format: {type(tool_call)}")
                        continue
                    
                    self._logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                    
                    # Extract base tool name and method if using flattened calling
                    base_tool_name = tool_name
                    extracted_method = None
                    if '__' in tool_name:
                        # Flattened method calling: "bigquery_vector_search__similarity_search"
                        base_tool_name, extracted_method = tool_name.split('__', 1)
                        self._logger.info(f"Detected flattened call: tool={base_tool_name}, method={extracted_method}")
                    
                    # Get tool from registry using base name
                    tool = registry.get_tool(base_tool_name)
                    if not tool:
                        error_msg = f"Tool '{base_tool_name}' not found in registry"
                        self._logger.error(error_msg)
                        tool_results.append({
                            "tool_call_id": tool_call_id,
                            "role": "tool",
                            "content": json.dumps({"error": error_msg})
                        })
                        continue
                    
                    # Execute tool - handle V2 IToolInterface structure
                    if hasattr(tool, 'execution') and hasattr(tool.execution, 'execute'):
                        # V2 IToolInterface - proper structure
                        # Determine method to call
                        method = ''
                        if extracted_method:
                            # Use extracted method from flattened name
                            method = extracted_method
                            self._logger.info(f"Using flattened method calling: {method}")
                        elif 'method' in tool_args:
                            # Explicit method in parameters
                            method = tool_args.pop('method')
                            self._logger.info(f"Using explicit method from parameters: {method}")
                        else:
                            self._logger.warning(f"No method specified for tool {tool_name}, will try empty method")
                        
                        self._logger.info(f"Calling tool.execution.execute(method='{method}', parameters={tool_args})")
                        
                        result = await tool.execution.execute(
                            method=method,
                            parameters=tool_args,
                            context=None
                        )
                    elif hasattr(tool, 'run'):
                        # MCP tools with run() method (including MCPToolAdapter wrapped tools)
                        self._logger.info(f"Calling MCP tool.run() with parameters: {list(tool_args.keys())}")
                        result = await tool.run(tool_args)
                    elif hasattr(tool, 'call_tool'):
                        # MCP standard call_tool method
                        result = await tool.call_tool(base_tool_name, tool_args)
                    elif hasattr(tool, 'execute'):
                        # Direct execute method
                        result = await tool.execute(**tool_args)
                    elif hasattr(tool, 'call'):
                        # Call method
                        result = await tool.call(**tool_args)
                    elif callable(tool):
                        # Callable tool
                        result = await tool(**tool_args)
                    else:
                        error_msg = f"Tool '{base_tool_name}' is not callable"
                        self._logger.error(error_msg)
                        result = {"error": error_msg}
                    
                    # Format result - handle different result types
                    if isinstance(result, str):
                        # Already a string, use as-is
                        pass
                    elif hasattr(result, 'to_dict'):
                        # ToolResult object with to_dict() method
                        result = json.dumps(result.to_dict())
                    elif hasattr(result, 'dict'):
                        # Pydantic model with dict() method  
                        result = json.dumps(result.dict())
                    else:
                        # Try direct JSON serialization
                        try:
                            result = json.dumps(result)
                        except (TypeError, ValueError) as e:
                            # If serialization fails, convert to string
                            self._logger.warning(f"Could not JSON serialize tool result, converting to string: {e}")
                            result = str(result)
                    
                    tool_results.append({
                        "tool_call_id": tool_call_id,
                        "role": "tool",
                        "name": tool_name,
                        "content": result
                    })
                    
                    self._logger.info(f"Tool {tool_name} executed successfully")
                    
                except Exception as tool_error:
                    self._logger.error(f"Error executing tool {tool_name}: {tool_error}")
                    tool_results.append({
                        "tool_call_id": tool_call_id if 'tool_call_id' in locals() else f"call_error_{int(time.time())}",
                        "role": "tool",
                        "content": json.dumps({"error": str(tool_error)})
                    })
            
            # Add tool result messages to session
            for tool_result in tool_results:
                tool_message = AgentMessage(
                    role="tool",
                    content=tool_result["content"],
                    tool_call_id=tool_result["tool_call_id"],
                    metadata={"tool_name": tool_result.get("name", "unknown")}
                )
                await session.add_message(tool_message)
                # Persist tool result to external memory
                await self._persist_to_memory(session, tool_message)
            
            return tool_results
            
        except Exception as e:
            self._logger.error(f"Error in tool execution: {e}")
            # We don't return error response here, just raise or return None
            # The caller should handle exceptions
            raise e

    async def _handle_tool_calls(
        self,
        response: IAgentResponse,
        session: IAgentSession
    ) -> IAgentResponse:
        """
        Legacy method for backward compatibility.
        Executes tools and gets final response (blocking).
        """
        try:
            # Execute tools
            tool_results = await self._execute_tool_calls(response, session)
            
            if not tool_results:
                return response
            
            # Send tool results back to provider to get final response
            self._logger.info("Sending tool results back to LLM for final response")
            
            # No new message needed - tool results are already in session
            final_response = await self._provider.send_message(
                None, session, self._configuration
            )
            
            return final_response
            
        except Exception as e:
            self._logger.error(f"Error in tool call handling: {e}")
            return AgentResponse.error_response(
                error=e,
                content=f"Tool execution failed: {str(e)}"
            )
    
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
                
                # Get or create session using two-level caching
                session = await self._get_or_create_session(session_id)
                
                # Create user message (with deduplication)
                user_message = AgentMessage(role="user", content=message)
                
                # Check if message is already the last one in session
                is_duplicate = False
                if session.messages:
                    last_msg = session.messages[-1]
                    if last_msg is not None and last_msg.role == "user" and last_msg.content == message:
                        is_duplicate = True
                        user_message = last_msg # Use existing message instance
                        self._logger.debug("Skipping duplicate user message in session (chat)")
                
                if not is_duplicate:
                    await session.add_message(user_message)
                    
                    # Persist to external memory (write-through)
                    await self._persist_to_memory(session, user_message)
                
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
                            provider_span.add_tag("input_tokens", response.usage.prompt_tokens)
                            provider_span.add_tag("output_tokens", response.usage.completion_tokens)
                            provider_span.add_tag("total_tokens", response.usage.total_tokens)
                
                # Handle tool calls with self-correction loop
                max_iterations = self._configuration.max_tool_iterations
                iteration = 0
                
                while (response.success and 
                       response.message and 
                       response.message.tool_calls and 
                       iteration < max_iterations):
                    
                    self._logger.info(
                        f"Tool iteration {iteration+1}/{max_iterations}: "
                        f"{len(response.message.tool_calls)} tool call(s)"
                    )
                    
                    # Execute tools (updates session)
                    await self._execute_tool_calls(response, session)
                    
                    # Get next response from provider (no new message needed - tool results are in session)
                    response = await self._provider.send_message(
                        None, session, self._configuration
                    )
                    
                    iteration += 1
                
                # Warn if max iterations reached with pending tool calls
                response_handled = False
                if iteration >= max_iterations and response.message and response.message.tool_calls:
                    self._logger.warning(
                        f"Max tool iterations ({max_iterations}) reached. "
                        f"Executing pending tools to ensure valid conversation state."
                    )
                    # Execute the pending tools so we have a valid state (ToolCall + ToolResult)
                    # This adds the messages to the session
                    await self._execute_tool_calls(response, session)
                    response_handled = True
                
                # Add final response to session (if not already handled)
                if response.success and response.message and not response_handled:
                    await session.add_message(response.message)
                    # Persist assistant response to external memory
                    await self._persist_to_memory(session, response.message)
                
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
                    self._auto_record_metric("chat_input_tokens", response.usage.prompt_tokens, "histogram",
                                           agent_name=self._name, provider=str(self._configuration.provider))
                    self._auto_record_metric("chat_output_tokens", response.usage.completion_tokens, "histogram",
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
        """Stream a chat response with tool call support"""
        if not self._configuration.streaming_enabled:
            # Fallback to regular chat
            response = await self.chat(message, session_id, **kwargs)
            yield response
            return
        
        start_time = time.time()
        
        try:
            # Get or create session using two-level caching
            session = await self._get_or_create_session(session_id)
            
            # Create user message (with deduplication)
            user_message = AgentMessage(role="user", content=message)
            
            # Check if message is already the last one in session
            is_duplicate = False
            if session.messages:
                last_msg = session.messages[-1]
                if last_msg is not None and last_msg.role == "user" and last_msg.content == message:
                    is_duplicate = True
                    user_message = last_msg # Use existing message instance
                    self._logger.debug("Skipping duplicate user message in session")
            
            if not is_duplicate:
                await session.add_message(user_message)
                
                # Persist to external memory (write-through)
                await self._persist_to_memory(session, user_message)
            
            # Set status to busy
            self._status = AgentStatus.BUSY
            
            # Stream response from provider
            full_content = ""
            last_chunk = None
            async for chunk in self._provider.stream_message(
                user_message, session, self._configuration
            ):
                if chunk.success:
                    full_content += chunk.content
                last_chunk = chunk  # Keep reference to final chunk for tool call detection
                yield chunk
            
            # CRITICAL FIX: Check if the final chunk has tool calls that need execution
            # This was missing and causing tool calls to be ignored in streaming mode!
            # Match chat() behavior - check only for tool_calls presence, not tools_enabled
            if (last_chunk and 
                last_chunk.message and 
                last_chunk.message.tool_calls and 
                len(last_chunk.message.tool_calls) > 0):
                
                self._logger.info(
                    f"Stream complete with {len(last_chunk.message.tool_calls)} tool call(s). "
                    f"Executing tools and continuing..."
                )
                
                # Execute tool calls and get final response (same logic as chat())
                max_iterations = self._configuration.max_tool_iterations
                iteration = 0
                response = last_chunk
                
                while (response.success and 
                       response.message and 
                       response.message.tool_calls and 
                       iteration < max_iterations):
                    
                    self._logger.info(
                        f"Tool iteration {iteration+1}/{max_iterations}: "
                        f"{len(response.message.tool_calls)} tool call(s)"
                    )
                    
                    # Execute tools (updates session)
                    await self._execute_tool_calls(response, session)
                    
                    # Stream next response from provider (no new message needed - tool results are in session)
                    last_chunk = None
                    async for chunk in self._provider.stream_message(
                        None, session, self._configuration
                    ):
                        if chunk.success:
                            full_content += chunk.content
                        last_chunk = chunk
                        yield chunk
                    
                    # Update response for next iteration check
                    if last_chunk:
                        response = last_chunk
                    else:
                        # Should not happen if stream worked
                        break
                        
                    iteration += 1
                
                # Warn if max iterations reached with pending tool calls
                if iteration >= max_iterations and response.message and response.message.tool_calls:
                    self._logger.warning(
                        f"Max tool iterations ({max_iterations}) reached in streaming mode. "
                        f"Executing pending tools to ensure valid conversation state."
                    )
                    # Execute the pending tools so we have a valid state (ToolCall + ToolResult)
                    await self._execute_tool_calls(response, session)
            else:
                # No tool calls - add complete response to session
                self._logger.debug("No tool calls to execute in stream")
                if full_content:
                    complete_message = AgentMessage(role="assistant", content=full_content)
                    await session.add_message(complete_message)
                    # Persist assistant response to external memory
                    await self._persist_to_memory(session, complete_message)
            
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
        # CRITICAL FIX: Deduplicate before adding to prevent OpenAI 128 tool limit errors
        current_tools = set(self._configuration.available_tools)
        new_tools = [t for t in tool_names if t not in current_tools]
        
        if new_tools:
            self._configuration.available_tools.extend(new_tools)
            self._configuration.tools_enabled = True
            self._logger.info(f"Added {len(new_tools)} new tools to agent {self.name}: {new_tools}")
        else:
            self._logger.debug(f"No new tools to add (all already present): {tool_names}")
    
    async def set_tools(self, tool_names: List[str]) -> None:
        """Set tools for the agent - provider handles integration"""
        # CRITICAL FIX: Deduplicate the input list to prevent OpenAI 128 tool limit errors
        unique_tools = list(dict.fromkeys(tool_names))  # Preserves order, removes duplicates
        
        if len(unique_tools) != len(tool_names):
            self._logger.warning(f"Removed {len(tool_names) - len(unique_tools)} duplicate tools from input")
        
        self._configuration.available_tools = unique_tools
        self._configuration.tools_enabled = len(unique_tools) > 0
        self._logger.info(f"Set {len(unique_tools)} unique tools for agent {self.name}: {unique_tools}")
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return self._configuration.available_tools.copy()
    
    # Alias for workflow compatibility - AgentStep calls send_message
    async def send_message(self, message: str, session_id: Optional[str] = None, **kwargs) -> IAgentResponse:
        """Alias for chat() - provides workflow compatibility with AgentStep"""
        return await self.chat(message, session_id, **kwargs)
