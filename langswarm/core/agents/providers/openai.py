"""
OpenAI Provider Implementation for LangSwarm V2

Native OpenAI integration that replaces the complex AgentWrapper with
clean, OpenAI-specific implementation optimized for OpenAI's API patterns.
"""

import asyncio
import json
import logging
import time
from typing import List, AsyncIterator, Dict, Any, Optional
from datetime import datetime

from langswarm.core.utils.optional_imports import optional_import, requires

# Optional imports with helpful error messages
openai = optional_import('openai', 'OpenAI provider')
AsyncOpenAI = None
if openai:
    try:
        from openai import AsyncOpenAI
    except ImportError:
        AsyncOpenAI = None

from ..interfaces import (
    IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, ProviderType
)
from ..base import AgentResponse, AgentSession, BaseAgent

logger = logging.getLogger(__name__)


@requires('openai')
class OpenAIProvider(IAgentProvider):
    """
    Native OpenAI provider implementation.
    
    Provides optimized integration with OpenAI's API including:
    - GPT-4o, GPT-4, GPT-3.5-turbo support
    - Function calling integration
    - Streaming responses
    - Vision capabilities (GPT-4V)
    - Token usage tracking
    - Retry logic and error handling
    """
    
    def __init__(self):
        # The @requires decorator ensures openai is available
        if not AsyncOpenAI:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        self._client_cache: Dict[str, AsyncOpenAI] = {}
        # Cache tool definitions to avoid rebuilding on every message (critical for performance)
        self._tool_definitions_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    @property
    def supported_models(self) -> List[str]:
        """OpenAI models supported by this provider - sourced from centralized config"""
        from .config import get_supported_models
        return get_supported_models("openai")
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        """Capabilities supported by OpenAI"""
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.FUNCTION_CALLING,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.VISION,
            AgentCapability.SYSTEM_PROMPTS,
            AgentCapability.CONVERSATION_HISTORY,
            AgentCapability.REALTIME_VOICE,  # For compatible models
            AgentCapability.MULTIMODAL
        ]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate OpenAI-specific configuration"""
        # Check if model is supported
        if config.model not in self.supported_models:
            raise ValueError(f"Model {config.model} not supported by OpenAI provider")
        
        # Check API key
        if not config.api_key:
            raise ValueError("API key required for OpenAI provider")
        
        # Validate model-specific constraints
        if config.model.startswith("o1-"):
            # O1 models have specific constraints
            if config.temperature and config.temperature != 1.0:
                logger.warning("O1 models ignore temperature parameter")
            if config.system_prompt:
                logger.warning("O1 models don't support system prompts")
        
        # Test API connectivity
        try:
            client = self._get_client(config)
            # Simple API test - list models
            await client.models.list()
            return True
        except Exception as e:
            raise ValueError(f"OpenAI API validation failed: {e}")
    
    async def create_session(self, config: IAgentConfiguration) -> IAgentSession:
        """Create a new OpenAI conversation session"""
        return AgentSession(max_messages=config.max_memory_messages)
    
    async def send_message(
        self, 
        message: AgentMessage, 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Send a message to OpenAI and get response"""
        try:
            client = self._get_client(config)
            
            # Build messages for OpenAI API
            messages = await self._build_openai_messages(session, message, config)
            
            # Prepare OpenAI API call parameters
            api_params = self._build_api_params(config, messages)
            
            # Make API call
            start_time = time.time()
            response = await client.chat.completions.create(**api_params)
            execution_time = time.time() - start_time
            
            # Process response
            return self._process_openai_response(response, execution_time, config)
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0.0
            logger.error(f"OpenAI API error: {e}")
            return AgentResponse.error_response(
                e, 
                content=f"OpenAI API error: {str(e)}",
                execution_time=execution_time
            )
    
    async def stream_message(
        self,
        message: AgentMessage,
        session: IAgentSession, 
        config: IAgentConfiguration
    ) -> AsyncIterator[IAgentResponse]:
        """Stream a response from OpenAI"""
        try:
            client = self._get_client(config)
            
            # Build messages for OpenAI API
            messages = await self._build_openai_messages(session, message, config)
            
            # Prepare OpenAI API call parameters with streaming
            api_params = self._build_api_params(config, messages, stream=True)
            
            # Make streaming API call
            start_time = time.time()
            stream = await client.chat.completions.create(**api_params)
            
            # Process streaming response
            async for chunk in self._process_openai_stream(stream, start_time, config):
                yield chunk
                
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield AgentResponse.error_response(e)
    
    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Execute a tool call through OpenAI function calling"""
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
            logger.error(f"OpenAI tool call error: {e}")
            return AgentResponse.error_response(e)
    
    def _get_client(self, config: IAgentConfiguration) -> AsyncOpenAI:
        """Get or create OpenAI client for configuration"""
        client_key = f"{config.api_key[:10]}_{config.base_url or 'default'}"
        
        if client_key not in self._client_cache:
            client_params = {
                "api_key": config.api_key,
                "timeout": config.timeout,
            }
            
            if config.base_url:
                client_params["base_url"] = config.base_url
            
            self._client_cache[client_key] = AsyncOpenAI(**client_params)
        
        return self._client_cache[client_key]
    
    async def _build_openai_messages(
        self, 
        session: IAgentSession, 
        new_message: AgentMessage,
        config: IAgentConfiguration
    ) -> List[Dict[str, Any]]:
        """Convert session messages to OpenAI format"""
        messages = []
        
        # Build system message with tool instructions
        system_content = config.system_prompt or ""
        
        # Inject tool instructions if tools enabled
        if config.tools_enabled and config.available_tools:
            tool_instructions = self._get_tool_instructions(config.available_tools)
            if tool_instructions:
                system_content += f"\n\n# Available Tools\n{tool_instructions}"
        
        # Add system message at the beginning if we have content
        if system_content:
            messages.append({
                "role": "system",
                "content": system_content
            })
        
        # Get conversation context
        context_messages = await session.get_context(
            max_tokens=config.max_tokens - 1000 if config.max_tokens else None
        )
        
        # Convert to OpenAI format
        for msg in context_messages:
            # Skip None messages and system messages from context (we already added our own)
            if msg is None or msg.role == "system":
                continue
                
            openai_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            # Add tool calls if present
            if msg.tool_calls:
                openai_msg["tool_calls"] = msg.tool_calls
            
            # Add tool call ID if present
            if msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id
            
            messages.append(openai_msg)
        
        # Add new message
        messages.append({
            "role": new_message.role,
            "content": new_message.content
        })
        
        return messages
    
    def _build_api_params(
        self, 
        config: IAgentConfiguration, 
        messages: List[Dict[str, Any]],
        stream: bool = False
    ) -> Dict[str, Any]:
        """Build OpenAI API parameters"""
        params = {
            "model": config.model,
            "messages": messages,
            "stream": stream
        }
        
        # Add optional parameters
        if config.max_tokens:
            params["max_tokens"] = config.max_tokens
        
        if config.temperature is not None and not config.model.startswith("o1-"):
            params["temperature"] = config.temperature
        
        if config.top_p is not None:
            params["top_p"] = config.top_p
        
        if config.frequency_penalty is not None:
            params["frequency_penalty"] = config.frequency_penalty
        
        if config.presence_penalty is not None:
            params["presence_penalty"] = config.presence_penalty
        
        if config.stop_sequences:
            params["stop"] = config.stop_sequences
        
        # Add tool configuration if enabled
        if config.tools_enabled and config.available_tools:
            # CRITICAL FIX: Use cache to avoid rebuilding tool definitions on every message
            cache_key = ",".join(sorted(config.available_tools))  # Stable cache key
            
            if cache_key not in self._tool_definitions_cache:
                logger.debug(f"Building tool definitions for {len(config.available_tools)} tools (cache miss)")
                self._tool_definitions_cache[cache_key] = self._build_tool_definitions(config.available_tools)
            else:
                logger.debug(f"Using cached tool definitions for {len(config.available_tools)} tools")
            
            params["tools"] = self._tool_definitions_cache[cache_key]
            
            if config.tool_choice:
                params["tool_choice"] = config.tool_choice
        
        return params
    
    def _build_tool_definitions(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Build OpenAI tool definitions from V2 tool registry using MCP standard with flattened methods"""
        try:
            from langswarm.tools.registry import ToolRegistry
            
            # Get real tool definitions from V2 registry
            registry = ToolRegistry()
            
            # CRITICAL FIX: Deduplicate tool_names to prevent building same tool multiple times
            unique_tool_names = list(dict.fromkeys(tool_names))  # Preserves order, removes duplicates
            
            logger.info(f"Building definitions for tools: {unique_tool_names}")
            
            if len(unique_tool_names) != len(tool_names):
                logger.warning(f"Deduplicated {len(tool_names) - len(unique_tool_names)} duplicate tool names in input")
            
            tools = []
            seen_function_names = set()  # Track flattened names to prevent OpenAI duplicates
            
            for tool_name in unique_tool_names:
                tool = registry.get_tool(tool_name)
                if not tool:
                    # FAIL FAST - no fallback to mock tools
                    raise ValueError(f"Tool '{tool_name}' not found in V2 registry. "
                                   f"Ensure tool is properly registered before use.")
                
                # Check if tool has methods to expose as flattened names
                if hasattr(tool, 'metadata') and hasattr(tool.metadata, 'methods'):
                    methods = tool.metadata.methods  # Dict[str, ToolSchema]
                    
                    if methods and len(methods) > 0:
                        # Tool supports multiple methods - register each as separate function
                        logger.info(f"Tool '{tool_name}' has {len(methods)} methods, creating flattened definitions")
                        
                    for method_name, method_schema in methods.items():
                        # Create flattened name: tool__method (double underscore, dots not allowed by OpenAI)
                        flattened_name = f"{tool_name}__{method_name}"
                        
                        # CRITICAL FIX: Skip if already registered
                        if flattened_name in seen_function_names:
                            logger.debug(f"Skipping duplicate flattened method: {flattened_name}")
                            continue
                        
                        seen_function_names.add(flattened_name)
                        
                        # Convert ToolSchema to OpenAI format
                        openai_tool = {
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
                        }
                        tools.append(openai_tool)
                        logger.debug(f"Registered flattened method: {flattened_name}")
                else:
                    # Tool has metadata but no methods, register as single tool
                    if tool_name not in seen_function_names:
                        logger.info(f"Tool '{tool_name}' has no methods, registering as single function")
                        mcp_schema = self._get_tool_mcp_schema(tool)
                        openai_tool = self._convert_mcp_to_openai_format(mcp_schema, tool_name)
                        tools.append(openai_tool)
                        seen_function_names.add(tool_name)
                    else:
                        logger.debug(f"Skipping duplicate tool: {tool_name}")
            
            # CRITICAL FIX: Check OpenAI's 128 tool limit
            if len(tools) > 128:
                error_msg = (
                    f"OpenAI API has a maximum of 128 tools, but {len(tools)} were generated "
                    f"from {len(unique_tool_names)} unique tool(s). "
                    f"Reduce the number of tools/methods or use tool filtering."
                )
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            final_tool_names = [t["function"]["name"] for t in tools]
            logger.info(f"✅ Built {len(tools)} tool definitions for OpenAI: {final_tool_names}")
            return tools
            
        except ImportError as e:
            raise RuntimeError(f"V2 tool system not available: {e}. "
                             f"Cannot create tool definitions without V2 registry.")
        except Exception as e:
            raise RuntimeError(f"Failed to build tool definitions: {e}")
    
    def _get_tool_mcp_schema(self, tool: Any) -> Dict[str, Any]:
        """Get standard MCP schema from V2 tool (IToolInterface object)"""
        if not tool:
            raise ValueError("Tool instance not found in registry")
        
        # Get MCP schema using standard MCP protocol
        try:
            # Use list_tools to get standard MCP format
            if hasattr(tool, 'list_tools'):
                tools_list = tool.list_tools()
                if tools_list and len(tools_list) > 0:
                    # Return the first tool's schema (most tools have one main schema)
                    return tools_list[0]
            
            # Fallback: construct from tool metadata
            if hasattr(tool, 'metadata'):
                metadata = tool.metadata
                return {
                    "name": getattr(metadata, 'name', 'unknown'),
                    "description": getattr(metadata, 'description', ''),
                    "input_schema": getattr(metadata, 'input_schema', {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": True
                    })
                }
            
            # Last resort: basic schema
            return {
                "name": str(tool),
                "description": "",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to get MCP schema for tool: {e}")
    
    def _convert_mcp_to_openai_format(self, mcp_schema: Dict[str, Any], tool_name: str = None) -> Dict[str, Any]:
        """Convert standard MCP schema to OpenAI function calling format"""
        # Use the registry key (tool_name) as the function name to ensure OpenAI compatibility
        # Registry keys are guaranteed to match pattern ^[a-zA-Z0-9_-]+$
        function_name = tool_name if tool_name else mcp_schema.get("name", "unknown_tool")
        
        return {
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
        }
    
    def _get_tool_instructions(self, tool_names: List[str]) -> str:
        """Get formatted tool instructions from template.md files"""
        try:
            from langswarm.tools.registry import ToolRegistry
            
            registry = ToolRegistry()
            instructions = []
            
            for tool_name in tool_names:
                tool = registry.get_tool(tool_name)
                if tool and hasattr(tool, 'metadata'):
                    instruction = getattr(tool.metadata, 'instruction', None)
                    if instruction:
                        instructions.append(f"\n## {tool_name}\n{instruction}")
            
            return "\n".join(instructions) if instructions else ""
            
        except Exception as e:
            logger.warning(f"Failed to load tool instructions: {e}")
            return ""
    
    def _process_openai_response(
        self, 
        response: Any, 
        execution_time: float,
        config: IAgentConfiguration
    ) -> AgentResponse:
        """Process OpenAI API response"""
        # Check if response is valid
        if not response:
            logger.error("OpenAI API returned None response")
            return AgentResponse.error_response(
                "OpenAI API returned empty response",
                execution_time=execution_time
            )
        
        # Check if choices exist
        if not hasattr(response, 'choices') or not response.choices:
            logger.error(f"OpenAI API response has no choices: {response}")
            return AgentResponse.error_response(
                "OpenAI API response has no choices",
                execution_time=execution_time
            )
        
        choice = response.choices[0]
        message = choice.message
        
        # Create agent message
        agent_message = AgentMessage(
            role="assistant",
            content=message.content or "",
            tool_calls=getattr(message, 'tool_calls', None),
            metadata={
                "model": config.model,
                "finish_reason": choice.finish_reason,
                "provider": "openai"
            }
        )
        
        # Create usage information
        usage = None
        if hasattr(response, 'usage') and response.usage:
            usage = AgentUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                model=config.model,
                cost_estimate=self._estimate_cost(response.usage, config.model)
            )
        
        return AgentResponse.success_response(
            content=message.content or "",
            message=agent_message,  # Pass the detailed message object
            usage=usage,
            execution_time=execution_time,
            model=config.model,
            finish_reason=choice.finish_reason,
            provider="openai"
        )
    
    async def _process_openai_stream(
        self, 
        stream: Any, 
        start_time: float,
        config: IAgentConfiguration
    ) -> AsyncIterator[AgentResponse]:
        """Process OpenAI streaming response"""
        collected_content = ""
        # CRITICAL FIX: Use a dictionary to aggregate tool call deltas by index
        # OpenAI sends tool calls in parts (deltas) which must be stitched together
        tool_calls_buffer = {}
        
        async for chunk in stream:
            if not chunk.choices:
                continue
                
            choice = chunk.choices[0]
            delta = choice.delta
            
            # Handle content chunks
            content = delta.content
            
            # Handle refusal (OpenAI safety refusals)
            if hasattr(delta, 'refusal') and delta.refusal:
                content = delta.refusal
            
            if content:
                collected_content += content
                
                # Yield content chunk
                chunk_message = AgentMessage(
                    role="assistant",
                    content=content,
                    metadata={
                        "chunk": True,
                        "model": config.model,
                        "provider": "openai"
                    }
                )
                
                yield AgentResponse.success_response(
                    content=content,
                    message=chunk_message,  # Pass the chunk message
                    streaming=True,
                    chunk_index=len(collected_content),
                    execution_time=time.time() - start_time
                )
            
            # Handle tool calls - Aggregate deltas
            if delta.tool_calls:
                for tool_call_chunk in delta.tool_calls:
                    index = tool_call_chunk.index
                    
                    if index not in tool_calls_buffer:
                        tool_calls_buffer[index] = {
                            "id": "",
                            "type": "function",
                            "function": {
                                "name": "",
                                "arguments": ""
                            }
                        }
                    
                    # Aggregate parts
                    if tool_call_chunk.id:
                        tool_calls_buffer[index]["id"] += tool_call_chunk.id
                    
                    if hasattr(tool_call_chunk, "function") and tool_call_chunk.function:
                        if tool_call_chunk.function.name:
                            tool_calls_buffer[index]["function"]["name"] += tool_call_chunk.function.name
                        
                        if tool_call_chunk.function.arguments:
                            tool_calls_buffer[index]["function"]["arguments"] += tool_call_chunk.function.arguments
            
            # Handle stream completion
            if choice.finish_reason:
                # Convert aggregated tool calls to list of dicts (AgentMessage expects dicts)
                final_tool_calls = []
                if tool_calls_buffer:
                    # Sort by index to maintain order
                    for index in sorted(tool_calls_buffer.keys()):
                        tc_data = tool_calls_buffer[index]
                        
                        # Create proper dictionary structure matching OpenAI format
                        tool_call_dict = {
                            "id": tc_data["id"],
                            "type": tc_data["type"],
                            "function": {
                                "name": tc_data["function"]["name"],
                                "arguments": tc_data["function"]["arguments"]
                            }
                        }
                        
                        final_tool_calls.append(tool_call_dict)
                
                # Final chunk signals completion - EMPTY content since all content already sent
                # This prevents duplication when applications concatenate all chunks
                final_message = AgentMessage(
                    role="assistant",
                    content="",  # Empty - all content already sent in incremental chunks
                    tool_calls=final_tool_calls if final_tool_calls else None,
                    metadata={
                        "model": config.model,
                        "finish_reason": choice.finish_reason,
                        "provider": "openai",
                        "stream_complete": True,
                        "total_content": collected_content  # Full text in metadata for reference
                    }
                )
                
                yield AgentResponse.success_response(
                    content="",  # Empty - prevents duplication
                    message=final_message,
                    streaming=False,
                    stream_complete=True,
                    execution_time=time.time() - start_time,
                    finish_reason=choice.finish_reason,
                    total_collected_content=collected_content  # Available in metadata if needed
                )
    
    def _estimate_cost(self, usage: Any, model: str) -> float:
        """Estimate cost for OpenAI API usage (prices per 1K tokens, updated Nov 2024)"""
        # Pricing from https://openai.com/api/pricing/
        rates = {
            # GPT-4o family (flagship multimodal)
            "gpt-4o": {"input": 0.0025, "output": 0.01},
            "gpt-4o-2024-11-20": {"input": 0.0025, "output": 0.01},
            "gpt-4o-2024-08-06": {"input": 0.0025, "output": 0.01},
            "gpt-4o-2024-05-13": {"input": 0.005, "output": 0.015},
            "chatgpt-4o-latest": {"input": 0.005, "output": 0.015},
            
            # GPT-4o mini (cost-effective)
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4o-mini-2024-07-18": {"input": 0.00015, "output": 0.0006},
            
            # O1 reasoning models
            "o1": {"input": 0.015, "output": 0.06},
            "o1-2024-12-17": {"input": 0.015, "output": 0.06},
            "o1-preview": {"input": 0.015, "output": 0.06},
            "o1-preview-2024-09-12": {"input": 0.015, "output": 0.06},
            "o1-mini": {"input": 0.003, "output": 0.012},
            "o1-mini-2024-09-12": {"input": 0.003, "output": 0.012},
            
            # GPT-4 Turbo
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4-turbo-2024-04-09": {"input": 0.01, "output": 0.03},
            "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
            
            # GPT-4 base
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-0613": {"input": 0.03, "output": 0.06},
            
            # GPT-3.5 Turbo
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
            "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
        }
        
        # Try exact match first, then prefix match for versioned models
        model_rates = rates.get(model)
        if not model_rates:
            # Try to find a matching base model
            for rate_model in rates:
                if model.startswith(rate_model.split("-2024")[0]):
                    model_rates = rates[rate_model]
                    break
        
        if not model_rates:
            return 0.0
        
        input_cost = (usage.prompt_tokens / 1000) * model_rates["input"]
        output_cost = (usage.completion_tokens / 1000) * model_rates["output"]
        
        return input_cost + output_cost
    
    async def get_health(self) -> Dict[str, Any]:
        """Get OpenAI provider health status"""
        return {
            "provider": "openai",
            "status": "healthy",
            "supported_models": self.supported_models,
            "capabilities": [cap.value for cap in self.supported_capabilities],
            "api_available": True,  # Would check actual API in real implementation
            "timestamp": datetime.now().isoformat()
        }


class OpenAIAgent(BaseAgent):
    """
    OpenAI-specific agent implementation.
    
    Extends BaseAgent with OpenAI-specific optimizations and features.
    """
    
    def __init__(self, name: str, configuration: 'AgentConfiguration', agent_id: Optional[str] = None):
        # Create OpenAI provider
        provider = OpenAIProvider()
        
        # Initialize base agent
        super().__init__(name, configuration, provider, agent_id)
        
        # OpenAI-specific initialization
        self._openai_features = {
            "supports_vision": "vision" in configuration.model.lower(),
            "supports_function_calling": True,
            "supports_streaming": True,
            "supports_realtime": configuration.model in ["gpt-4o", "gpt-4o-realtime"],
            "max_context_tokens": self._get_context_limit(configuration.model)
        }
    
    def _get_context_limit(self, model: str) -> int:
        """Get context limit for OpenAI model"""
        limits = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-4-vision-preview": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
            "o1-preview": 128000,
            "o1-mini": 128000
        }
        return limits.get(model, 4096)
    
    async def health_check(self) -> Dict[str, Any]:
        """Enhanced health check with OpenAI-specific information"""
        base_health = await super().health_check()
        
        base_health.update({
            "openai_features": self._openai_features,
            "context_limit": self._openai_features["max_context_tokens"],
            "api_available": await self._check_api_availability()
        })
        
        return base_health
    
    async def _check_api_availability(self) -> bool:
        """Check if OpenAI API is available"""
        try:
            # Test API connectivity
            await self._provider.validate_configuration(self._configuration)
            return True
        except Exception:
            return False
    
    # OpenAI-specific methods can be added here
    async def generate_image(self, prompt: str, **kwargs) -> AgentResponse:
        """Generate image using DALL-E (if available)"""
        # This would integrate with OpenAI's image generation API
        # For now, return a placeholder
        return AgentResponse.success_response(
            content=f"Image generation requested: {prompt}",
            image_generation=True,
            dall_e_prompt=prompt
        )
