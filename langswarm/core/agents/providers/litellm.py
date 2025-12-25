"""
LiteLLM Provider Implementation for LangSwarm V2

Unified provider that uses LiteLLM to support 100+ LLM providers (OpenAI, Anthropic, Gemini, etc.)
through a single interface. Replaces individual provider implementations.
"""

import asyncio
import json
import logging
import time
import os
from typing import List, AsyncIterator, Dict, Any, Optional
from datetime import datetime

from langswarm.core.utils.optional_imports import optional_import, requires

# Import litellm
litellm = optional_import('litellm', 'LiteLLM provider')

from ..interfaces import (
    IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, ProviderType
)
from ..base import AgentResponse, AgentSession, BaseAgent

logger = logging.getLogger(__name__)


@requires('litellm')
class LiteLLMProvider(IAgentProvider):
    """
    Unified LiteLLM provider implementation.
    
    Routes all LLM calls through LiteLLM, enabling:
    - Support for 100+ providers (OpenAI, Anthropic, Gemini, etc.)
    - Unified API for chat, streaming, and tools
    - Automatic failover and retries
    - Cost tracking
    - Observability via callbacks (LangFuse, etc.)
    """
    
    def __init__(self):
        if not litellm:
            raise ImportError("LiteLLM package not installed. Run: pip install litellm")
        
        # Configure LiteLLM defaults
        litellm.drop_params = True  # Auto-drop unsupported params
        
        # Monkeypatch litellm.utils.is_cached_message to fix Gemini TypeError
        # Fixes: TypeError: 'TextPromptClient' object is not iterable
        try:
            import litellm.utils as litellm_utils
            def noop_is_cached_message(message):
                return False
            litellm_utils.is_cached_message = noop_is_cached_message
            logger.info("Applied monkeypatch to litellm.utils.is_cached_message to fix Gemini compatibility.")
        except Exception as e:
            logger.warning(f"Failed to apply litellm monkeypatch: {e}")
        
        # Cache tool definitions
        self._tool_definitions_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Auto-detect and enable LangFuse if environment variables are set
        self._auto_configure_langfuse()
    
    def _auto_configure_langfuse(self):
        """
        Automatically configure LangFuse observability if environment variables are set.
        
        Checks for:
        - LANGFUSE_PUBLIC_KEY
        - LANGFUSE_SECRET_KEY
        - LANGFUSE_HOST (optional)
        
        If credentials are found, registers LangFuse callbacks with LiteLLM.
        
        Note: LiteLLM's Langfuse callback automatically tracks:
        - Latency (request duration)
        - Token usage
        - Costs
        - Session grouping (via metadata.session_id)
        - Trace naming (via metadata.trace_name)
        """
        # Check if LangFuse credentials are in environment
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        
        if not public_key or not secret_key:
            # No LangFuse credentials found, skip configuration
            return
        
        try:
            # Verify langfuse package is installed
            import langfuse
            import packaging.version
            
            # Check for incompatible v3.x
            try:
                current_version = packaging.version.parse(langfuse.version.__version__)
                if current_version >= packaging.version.parse("3.0.0"):
                    logger.warning(
                        f"⚠️  Incompatible Langfuse version detected: {current_version}. "
                        "LiteLLM currently requires langfuse<3.0.0 (e.g., 2.53.0). "
                        "Observability may fail. Please run: pip install 'langfuse<3.0.0'"
                    )
                else:
                    logger.debug(f"Langfuse version {current_version} is compatible")
            except Exception as e:
                logger.debug(f"Failed to check langfuse version: {e}")
            
            # Register LangFuse callbacks with LiteLLM
            # Use list assignment to ensure callbacks are properly initialized
            if not isinstance(litellm.success_callback, list):
                litellm.success_callback = []
            if not isinstance(litellm.failure_callback, list):
                litellm.failure_callback = []
            
            if "langfuse" not in litellm.success_callback:
                litellm.success_callback.append("langfuse")
            if "langfuse" not in litellm.failure_callback:
                litellm.failure_callback.append("langfuse")
            
            # Get optional host setting (support both standard env vars)
            host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"
            
            # Ensure it's set in environment for the SDK to pick it up if it wasn't already
            if host:
                os.environ["LANGFUSE_HOST"] = host
            
            logger.info(
                f"✅ LangFuse observability enabled for LiteLLM "
                f"(host: {host}, callbacks: {litellm.success_callback})"
            )
            
        except ImportError:
            logger.warning(
                "⚠️  LangFuse credentials found in environment, but 'langfuse' package is not installed. "
                "Install it with: pip install langfuse or pip install langswarm[observability]"
            )
        except Exception as e:
            logger.warning(f"⚠️  Failed to auto-configure LangFuse: {e}")
    
    @property
    def provider_type(self) -> ProviderType:
        # We map everything to a generic "LITELLM" type or custom type
        # For now, we can reuse OPENAI type or add a new LITELLM type to the enum
        # But since ProviderType is an enum, we might need to extend it or pick a default.
        # Let's check ProviderType definition later. For now, assume we might need to add it.
        # If we can't add it easily, we might return ProviderType.CUSTOM or similar if it exists.
        # Checking imports... ProviderType is imported.
        # Let's assume we'll add LITELLM to ProviderType or use a placeholder.
        # For safety, let's return ProviderType.OPENAI as a fallback since LiteLLM mimics it,
        # or better, check if we can modify the Enum.
        return ProviderType.LITELLM
    
    @property
    def supported_models(self) -> List[str]:
        """All models supported by LiteLLM"""
        # LiteLLM supports almost everything, so we return a wildcard or common list
        return ["*"]
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        """Capabilities supported by LiteLLM (depends on underlying model)"""
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.FUNCTION_CALLING,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.VISION,
            AgentCapability.SYSTEM_PROMPTS,
            AgentCapability.CONVERSATION_HISTORY,
            AgentCapability.MULTIMODAL
        ]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate configuration"""
        if not config.model:
            raise ValueError("Model name required for LiteLLM provider")
            
        # LiteLLM handles API keys via env vars or params.
        # We don't strictly enforce api_key in config if it's in env.
        
        return True
    
    async def create_session(self, config: IAgentConfiguration) -> IAgentSession:
        """Create a new session"""
        return AgentSession(max_messages=config.max_memory_messages)
    
    async def send_message(
        self, 
        message: Optional[AgentMessage], 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Send a message via LiteLLM"""
        try:
            # Build messages
            messages = await self._build_messages(session, message, config)
            
            # Prepare parameters
            params = self._build_params(config, messages, session=session)
            
            # Make API call
            start_time = time.time()
            response = await litellm.acompletion(**params)
            execution_time = time.time() - start_time
            
            # Process response
            return self._process_response(response, execution_time, config)
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            
            # Handle RateLimitError and APIError as user-facing responses
            if hasattr(litellm, 'RateLimitError') and isinstance(e, litellm.RateLimitError):
                error_msg = f"⚠️ **Rate Limit Exceeded**: {str(e)}"
                logger.warning(f"LiteLLM RateLimitError: {e}")
                return AgentResponse.success_response(
                    content=error_msg,
                    role="assistant",
                    execution_time=execution_time,
                    metadata={"error": True, "error_type": "RateLimitError"}
                )
            
            if hasattr(litellm, 'APIError') and isinstance(e, litellm.APIError):
                error_msg = f"⚠️ **Provider Error**: {str(e)}"
                logger.warning(f"LiteLLM APIError: {e}")
                return AgentResponse.success_response(
                    content=error_msg,
                    role="assistant",
                    execution_time=execution_time,
                    metadata={"error": True, "error_type": "APIError"}
                )

            logger.error(f"LiteLLM error: {e}")
            return AgentResponse.error_response(
                e, 
                content=f"LiteLLM error: {str(e)}",
                execution_time=execution_time
            )
    
    async def stream_message(
        self,
        message: Optional[AgentMessage],
        session: IAgentSession, 
        config: IAgentConfiguration
    ) -> AsyncIterator[IAgentResponse]:
        """Stream a response via LiteLLM"""
        try:
            # Build messages
            messages = await self._build_messages(session, message, config)
            
            # Prepare parameters with streaming
            params = self._build_params(config, messages, stream=True, session=session)
            
            # Make streaming API call
            start_time = time.time()
            stream = await litellm.acompletion(**params)
            
            # Process streaming response
            async for chunk in self._process_stream(stream, start_time, config):
                yield chunk
                
        except Exception as e:
            # Handle RateLimitError and APIError as user-facing responses
            if hasattr(litellm, 'RateLimitError') and isinstance(e, litellm.RateLimitError):
                error_msg = f"⚠️ **Rate Limit Exceeded**: {str(e)}"
                logger.warning(f"LiteLLM streaming RateLimitError: {e}")
                yield AgentResponse.success_response(
                    content=error_msg,
                    role="assistant",
                    metadata={"error": True, "error_type": "RateLimitError"}
                )
            elif hasattr(litellm, 'APIError') and isinstance(e, litellm.APIError):
                error_msg = f"⚠️ **Provider Error**: {str(e)}"
                logger.warning(f"LiteLLM streaming APIError: {e}")
                yield AgentResponse.success_response(
                    content=error_msg,
                    role="assistant",
                    metadata={"error": True, "error_type": "APIError"}
                )
            else:
                logger.error(f"LiteLLM streaming error: {e}")
                yield AgentResponse.error_response(e)
    
    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Execute a tool call (re-uses send_message with tool context)"""
        try:
            # Create a tool call message
            tool_message = AgentMessage(
                role="user",
                content=f"Use the {tool_name} tool with parameters: {json.dumps(tool_parameters)}",
                tool_calls=[{
                    "id": f"call_{int(time.time())}",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(tool_parameters)
                    }
                }]
            )
            
            # Send as regular message but with tool context
            response = await self.send_message(tool_message, session, config)
            
            # Add tool execution metadata
            if response.success:
                response = AgentResponse(
                    content=response.content,
                    message=response.message,
                    usage=response.usage,
                    metadata={
                        **response.metadata,
                        "tool_executed": tool_name,
                        "tool_parameters": tool_parameters,
                        "tool_response": True
                    },
                    success=True
                )
            
            return response
            
        except Exception as e:
            logger.error(f"LiteLLM tool call error: {e}")
            return AgentResponse.error_response(e)
            
    async def _build_messages(
        self, 
        session: IAgentSession, 
        new_message: Optional[AgentMessage],
        config: IAgentConfiguration
    ) -> List[Dict[str, Any]]:
        """Convert session messages to LiteLLM/OpenAI format"""
        messages = []
        
        # System prompt
        system_content = config.system_prompt or ""
        
        # Inject tool instructions if tools enabled
        if config.tools_enabled and config.available_tools:
            tool_instructions = self._get_tool_instructions(config.available_tools)
            if tool_instructions:
                system_content += f"\\n\\n# Available Tools\\n{tool_instructions}"
        
        if system_content:
            messages.append({
                "role": "system",
                "content": system_content
            })
        
        # Context messages
        context_messages = await session.get_context(
            max_tokens=config.max_tokens - 1000 if config.max_tokens else None
        )
        
        for msg in context_messages:
            if msg.role == "system":
                continue
                
            openai_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            if msg.tool_calls:
                openai_msg["tool_calls"] = msg.tool_calls
            
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
            
            messages.append(openai_msg)
        
        # New message (skip if None - tool continuation case)
        if new_message is not None:
            # CRITICAL FIX: Check if the message is already in the context to prevent duplication
            # BaseAgent adds message to session before calling send_message, so it might be in context_messages
            is_duplicate = False
            if messages:
                last_msg = messages[-1]
                if (last_msg.get("role") == new_message.role and 
                    last_msg.get("content") == new_message.content):
                    is_duplicate = True
            
            if not is_duplicate:
                messages.append({
                    "role": new_message.role,
                    "content": new_message.content
                })
        
        return messages
    
    def _build_params(
        self, 
        config: IAgentConfiguration, 
        messages: List[Dict[str, Any]],
        stream: bool = False,
        session: Optional[IAgentSession] = None
    ) -> Dict[str, Any]:
        """Build LiteLLM parameters"""
        params = {
            "model": config.model,
            "messages": messages,
            "stream": stream
        }
        
        # Add Langfuse observability metadata
        # See: https://docs.litellm.ai/docs/observability/langfuse_integration
        # Supported keys: session_id, trace_name, trace_id, trace_user_id, generation_name, tags
        if "metadata" not in params:
            params["metadata"] = {}
        
        # Session tracking - used by Langfuse to group related calls
        if session and hasattr(session, 'session_id') and session.session_id:
            params["metadata"]["session_id"] = session.session_id
            logger.debug(f"Langfuse session_id set: {session.session_id}")
        else:
            logger.debug(f"No session_id available (session={session}, has_attr={hasattr(session, 'session_id') if session else 'N/A'})")
        
        # Agent name and trace naming
        if hasattr(config, 'provider_config') and config.provider_config:
            agent_name = config.provider_config.get("agent_name")
            if agent_name:
                # trace_name is used by Langfuse to name the trace
                params["metadata"]["trace_name"] = agent_name
                # Also keep agent_name for filtering/grouping
                params["metadata"]["agent_name"] = agent_name
                logger.debug(f"Langfuse trace_name set: {agent_name}")
            
            # Handle conditional observability disabling
            if config.provider_config.get("observability_disable_tracing", False):
                # Disable LiteLLM callbacks for this request
                if "extra_headers" not in params:
                    params["extra_headers"] = {}
                params["extra_headers"]["x-litellm-disable-callbacks"] = "true"
            
            # Enable debug mode for Langfuse if requested
            if config.provider_config.get("debug_langfuse", False):
                params["metadata"]["debug_langfuse"] = True
        
        # Log the full metadata for debugging (at debug level)
        if params.get("metadata"):
            logger.debug(f"Langfuse metadata: {params['metadata']}")
        
        # Optional params
        if config.max_tokens:
            params["max_tokens"] = config.max_tokens
        if config.temperature is not None:
            params["temperature"] = config.temperature
        if config.top_p is not None:
            params["top_p"] = config.top_p
        if config.frequency_penalty is not None:
            params["frequency_penalty"] = config.frequency_penalty
        if config.presence_penalty is not None:
            params["presence_penalty"] = config.presence_penalty
        if config.stop_sequences:
            params["stop"] = config.stop_sequences
        if config.api_key:
            params["api_key"] = config.api_key
        if config.base_url:
            params["api_base"] = config.base_url
            
        # Timeout
        if hasattr(config, 'timeout') and config.timeout:
            params["timeout"] = config.timeout
            
        # Fallbacks (from provider_config)
        if hasattr(config, 'provider_config') and config.provider_config:
            if "fallbacks" in config.provider_config:
                params["fallbacks"] = config.provider_config["fallbacks"]
            
        # Tools
        if config.tools_enabled and config.available_tools:
            cache_key = ",".join(sorted(config.available_tools))
            
            if cache_key not in self._tool_definitions_cache:
                # Reuse the OpenAI tool builder since LiteLLM uses the same format
                # We need to import it or duplicate logic. 
                # For now, let's duplicate the logic to keep this provider self-contained
                # but simplified.
                self._tool_definitions_cache[cache_key] = self._build_tool_definitions(config.available_tools)
            
            params["tools"] = self._tool_definitions_cache[cache_key]
            
            if config.tool_choice:
                params["tool_choice"] = config.tool_choice
                
        return params

    def _build_tool_definitions(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Build tool definitions using V2 registry (same as OpenAI provider)"""
        try:
            from langswarm.tools.registry import ToolRegistry
            registry = ToolRegistry()
            unique_tool_names = list(dict.fromkeys(tool_names))
            
            tools = []
            seen_function_names = set()
            
            for tool_name in unique_tool_names:
                tool = registry.get_tool(tool_name)
                if not tool:
                    continue
                
                if hasattr(tool, 'metadata') and hasattr(tool.metadata, 'methods'):
                    methods = tool.metadata.methods
                    for method_name, method_schema in methods.items():
                        flattened_name = f"{tool_name}__{method_name}"
                        if flattened_name in seen_function_names:
                            continue
                        seen_function_names.add(flattened_name)
                        
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": flattened_name,
                                "description": method_schema.description,
                                "parameters": {
                                    "type": "object",
                                    "properties": method_schema.parameters,
                                    "required": method_schema.required
                                }
                            }
                        })
                else:
                    if tool_name not in seen_function_names:
                        # Fallback to MCP schema extraction
                        # Simplified version of OpenAIProvider._get_tool_mcp_schema
                        mcp_schema = self._get_tool_mcp_schema(tool)
                        function_name = tool_name
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "description": mcp_schema.get("description", ""),
                                "parameters": mcp_schema.get("input_schema", {
                                    "type": "object",
                                    "properties": {},
                                    "additionalProperties": True
                                })
                            }
                        })
                        seen_function_names.add(tool_name)
            
            return tools
        except Exception as e:
            logger.error(f"Failed to build tool definitions: {e}")
            return []

    def _get_tool_mcp_schema(self, tool: Any) -> Dict[str, Any]:
        """Get standard MCP schema"""
        if hasattr(tool, 'list_tools'):
            tools_list = tool.list_tools()
            if tools_list:
                return tools_list[0]
        
        if hasattr(tool, 'metadata'):
            return {
                "name": getattr(tool.metadata, 'name', 'unknown'),
                "description": getattr(tool.metadata, 'description', ''),
                "input_schema": getattr(tool.metadata, 'input_schema', {})
            }
        return {"name": str(tool), "description": "", "input_schema": {}}

    def _get_tool_instructions(self, tool_names: List[str]) -> str:
        """Get formatted tool instructions"""
        try:
            from langswarm.tools.registry import ToolRegistry
            registry = ToolRegistry()
            instructions = []
            for tool_name in tool_names:
                tool = registry.get_tool(tool_name)
                if tool and hasattr(tool, 'metadata'):
                    instruction = getattr(tool.metadata, 'instruction', None)
                    if instruction:
                        instructions.append(f"\\n## {tool_name}\\n{instruction}")
            return "\\n".join(instructions) if instructions else ""
        except Exception:
            return ""

    def _process_response(
        self, 
        response: Any, 
        execution_time: float,
        config: IAgentConfiguration
    ) -> AgentResponse:
        """Process LiteLLM response"""
        if not response or not response.choices:
            return AgentResponse.error_response("Empty response from LiteLLM", execution_time=execution_time)
            
        choice = response.choices[0]
        message = choice.message
        
        agent_message = AgentMessage(
            role="assistant",
            content=message.content or "",
            tool_calls=getattr(message, 'tool_calls', None),
            metadata={
                "model": config.model,
                "finish_reason": choice.finish_reason,
                "provider": "litellm"
            }
        )
        
        usage = None
        if hasattr(response, 'usage') and response.usage:
            # LiteLLM provides cost in response._hidden_params or we calculate it
            # But AgentUsage expects us to calculate it usually.
            # LiteLLM has a cost_per_token function we can use.
            try:
                cost = litellm.completion_cost(completion_response=response)
            except:
                cost = 0.0
                
            usage = AgentUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                model=config.model,
                cost_estimate=cost
            )
            
        return AgentResponse.success_response(
            content=message.content or "",
            message=agent_message,
            usage=usage,
            execution_time=execution_time,
            model=config.model,
            finish_reason=choice.finish_reason,
            provider="litellm"
        )
        
    async def _process_stream(
        self, 
        stream: Any, 
        start_time: float,
        config: IAgentConfiguration
    ) -> AsyncIterator[AgentResponse]:
        """Process LiteLLM streaming response (same as OpenAI)"""
        collected_content = ""
        tool_calls_buffer = {}
        
        async for chunk in stream:
            if not chunk.choices:
                continue
                
            choice = chunk.choices[0]
            delta = choice.delta
            
            # Content
            content = delta.content
            if content:
                collected_content += content
                chunk_message = AgentMessage(
                    role="assistant",
                    content=content,
                    metadata={"chunk": True, "model": config.model, "provider": "litellm"}
                )
                yield AgentResponse.success_response(
                    content=content,
                    message=chunk_message,
                    streaming=True,
                    chunk_index=len(collected_content),
                    execution_time=time.time() - start_time
                )
            
            # Tool calls
            if delta.tool_calls:
                for tool_call_chunk in delta.tool_calls:
                    index = tool_call_chunk.index
                    if index not in tool_calls_buffer:
                        tool_calls_buffer[index] = {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
                    
                    if tool_call_chunk.id:
                        tool_calls_buffer[index]["id"] += tool_call_chunk.id
                    if hasattr(tool_call_chunk, "function") and tool_call_chunk.function:
                        if tool_call_chunk.function.name:
                            tool_calls_buffer[index]["function"]["name"] += tool_call_chunk.function.name
                        if tool_call_chunk.function.arguments:
                            tool_calls_buffer[index]["function"]["arguments"] += tool_call_chunk.function.arguments
            
            # Completion
            if choice.finish_reason:
                final_tool_calls = []
                if tool_calls_buffer:
                    for index in sorted(tool_calls_buffer.keys()):
                        tc = tool_calls_buffer[index]
                        final_tool_calls.append({
                            "id": tc["id"],
                            "type": tc["type"],
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        })
                
                final_message = AgentMessage(
                    role="assistant",
                    content="",
                    tool_calls=final_tool_calls if final_tool_calls else None,
                    metadata={
                        "model": config.model,
                        "finish_reason": choice.finish_reason,
                        "provider": "litellm",
                        "stream_complete": True
                    }
                )
                
                yield AgentResponse.success_response(
                    content="",
                    message=final_message,
                    streaming=False,
                    stream_complete=True,
                    execution_time=time.time() - start_time,
                    finish_reason=choice.finish_reason
                )

    async def get_health(self) -> Dict[str, Any]:
        return {
            "provider": "litellm",
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
