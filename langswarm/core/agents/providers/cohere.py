"""
Cohere Provider Implementation for LangSwarm V2

Native Cohere integration that provides clean, Cohere-specific
implementation optimized for Command models and their capabilities.
"""

import asyncio
import json
import logging
import time
from typing import List, AsyncIterator, Dict, Any, Optional
from datetime import datetime

try:
    import cohere
    from cohere import AsyncClient
except ImportError:
    cohere = None
    AsyncClient = None

from ..interfaces import (
    IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, ProviderType
)
from ..base import AgentResponse, AgentSession, BaseAgent

logger = logging.getLogger(__name__)


class CohereProvider(IAgentProvider):
    """
    Native Cohere provider implementation.
    
    Provides optimized integration with Cohere's API including:
    - Command R+, Command R, Command model support
    - Tool use integration
    - RAG capabilities
    - Streaming responses
    - Embeddings integration
    - Token usage tracking
    - Retry logic and error handling
    """
    
    def __init__(self):
        if not cohere:
            raise ImportError("Cohere package not installed. Run: pip install cohere")
        
        self._client_cache: Dict[str, AsyncClient] = {}
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.COHERE
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "command-r-plus",
            "command-r",
            "command",
            "command-nightly",
            "command-light",
            "command-light-nightly"
        ]
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.FUNCTION_CALLING,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.CONVERSATION_HISTORY,
            AgentCapability.SYSTEM_PROMPTS
        ]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate Cohere-specific configuration"""
        # Check if model is supported
        if config.model not in self.supported_models:
            raise ValueError(f"Model {config.model} not supported by Cohere provider")
        
        # Check API key
        if not config.api_key:
            raise ValueError("API key required for Cohere provider")
        
        # Test API connectivity
        try:
            client = self._get_client(config)
            # Simple API test
            models = await client.models.list()
            return True
        except Exception as e:
            raise ValueError(f"Cohere API validation failed: {e}")
    
    async def create_session(self, config: IAgentConfiguration) -> IAgentSession:
        """Create a new Cohere conversation session"""
        return AgentSession(max_messages=config.max_memory_messages)
    
    async def send_message(
        self, 
        message: AgentMessage, 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Send a message to Cohere and get response"""
        try:
            client = self._get_client(config)
            
            # Build chat history for Cohere API
            chat_history = await self._build_cohere_history(session, config)
            
            # Prepare tools if enabled
            tools = None
            if config.tools_enabled and config.available_tools:
                tools = self._build_tool_definitions(config.available_tools)
            
            # Make API call
            start_time = time.time()
            response = await client.chat(
                model=config.model,
                message=message.content,
                chat_history=chat_history,
                preamble=config.system_prompt,
                tools=tools,
                temperature=config.temperature or 0.7,
                max_tokens=config.max_tokens or 4096,
                p=config.top_p or 0.9,
                stop_sequences=config.stop_sequences or []
            )
            execution_time = time.time() - start_time
            
            # Process response
            return self._process_cohere_response(response, execution_time, config)
            
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            return AgentResponse.error_response(e)
    
    async def stream_message(
        self,
        message: AgentMessage,
        session: IAgentSession, 
        config: IAgentConfiguration
    ) -> AsyncIterator[IAgentResponse]:
        """Stream a response from Cohere"""
        try:
            client = self._get_client(config)
            
            # Build chat history for Cohere API
            chat_history = await self._build_cohere_history(session, config)
            
            # Prepare tools if enabled
            tools = None
            if config.tools_enabled and config.available_tools:
                tools = self._build_tool_definitions(config.available_tools)
            
            # Make streaming API call
            start_time = time.time()
            stream = await client.chat_stream(
                model=config.model,
                message=message.content,
                chat_history=chat_history,
                preamble=config.system_prompt,
                tools=tools,
                temperature=config.temperature or 0.7,
                max_tokens=config.max_tokens or 4096,
                p=config.top_p or 0.9,
                stop_sequences=config.stop_sequences or []
            )
            
            # Process streaming response
            async for chunk in self._process_cohere_stream(stream, start_time, config):
                yield chunk
                
        except Exception as e:
            logger.error(f"Cohere streaming error: {e}")
            yield AgentResponse.error_response(e)
    
    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Execute a tool call through Cohere tool use"""
        try:
            # Create a tool call message
            tool_message = AgentMessage(
                role="user",
                content=f"Use the {tool_name} tool with these parameters: {json.dumps(tool_parameters)}",
                metadata={
                    "tool_call": {
                        "name": tool_name,
                        "parameters": tool_parameters
                    }
                }
            )
            
            # Send as regular message but with tool context
            response = await self.send_message(tool_message, session, config)
            
            # Add tool execution metadata
            if hasattr(response, 'metadata'):
                response.metadata.update({
                    "tool_execution": {
                        "tool_executed": tool_name,
                        "tool_parameters": tool_parameters,
                        "tool_response": True
                    }
                })
            
            return response
            
        except Exception as e:
            logger.error(f"Cohere tool call error: {e}")
            return AgentResponse.error_response(e)
    
    def _get_client(self, config: IAgentConfiguration) -> AsyncClient:
        """Get or create Cohere client for configuration"""
        client_key = f"{config.api_key[:10]}"
        
        if client_key not in self._client_cache:
            self._client_cache[client_key] = AsyncClient(api_key=config.api_key)
        
        return self._client_cache[client_key]
    
    def _build_tool_definitions(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Build Cohere tool definitions from V2 tool registry using MCP standard"""
        try:
            from langswarm.tools.registry import ToolRegistry
            
            # Get real tool definitions from V2 registry
            registry = ToolRegistry()
            
            # Auto-populate registry with adapted MCP tools if empty
            if not registry._tools:
                registry.auto_populate_with_mcp_tools()
            
            tools = []
            for tool_name in tool_names:
                tool_info = registry.get_tool(tool_name)
                if tool_info:
                    # Get standard MCP schema from tool
                    mcp_schema = self._get_tool_mcp_schema(tool_info)
                    # Convert MCP schema to Cohere format
                    cohere_tool = self._convert_mcp_to_cohere_format(mcp_schema)
                    tools.append(cohere_tool)
                else:
                    # FAIL FAST - no fallback to mock tools
                    raise ValueError(f"Tool '{tool_name}' not found in V2 registry. "
                                   f"Ensure tool is properly registered before use.")
            
            return tools
            
        except ImportError as e:
            raise RuntimeError(f"V2 tool system not available: {e}. "
                             f"Cannot create tool definitions without V2 registry.")
        except Exception as e:
            raise RuntimeError(f"Failed to build tool definitions: {e}")
    
    def _get_tool_mcp_schema(self, tool_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get standard MCP schema from V2 tool"""
        tool_instance = tool_info.get('tool_instance')
        if not tool_instance:
            raise ValueError("Tool instance not found in registry")
        
        # Get MCP schema using standard MCP protocol
        try:
            # Use list_tools to get standard MCP format
            if hasattr(tool_instance, 'list_tools'):
                tools_list = tool_instance.list_tools()
                if tools_list and len(tools_list) > 0:
                    # Return the first tool's schema (most tools have one main schema)
                    return tools_list[0]
            
            # Fallback: construct from metadata
            metadata = tool_info.get('metadata', {})
            return {
                "name": metadata.get('name', tool_info.get('name', 'unknown')),
                "description": metadata.get('description', ''),
                "input_schema": metadata.get('input_schema', {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True
                })
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to get MCP schema for tool: {e}")
    
    def _convert_mcp_to_cohere_format(self, mcp_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard MCP schema to Cohere tool calling format"""
        return {
            "name": mcp_schema.get("name", "unknown_tool"),
            "description": mcp_schema.get("description", ""),
            "parameter_definitions": self._convert_json_schema_to_cohere_params(
                mcp_schema.get("input_schema", {})
            )
        }
    
    def _convert_json_schema_to_cohere_params(self, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON schema to Cohere parameter definitions"""
        parameter_definitions = {}
        
        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])
        
        for param_name, param_schema in properties.items():
            param_def = {
                "description": param_schema.get("description", f"Parameter {param_name}"),
                "type": param_schema.get("type", "str").upper(),
                "required": param_name in required
            }
            
            # Handle enum values
            if "enum" in param_schema:
                param_def["options"] = param_schema["enum"]
            
            parameter_definitions[param_name] = param_def
        
        return parameter_definitions
    
    async def _build_cohere_history(
        self, 
        session: IAgentSession, 
        config: IAgentConfiguration
    ) -> List[Dict[str, str]]:
        """Build chat history for Cohere API"""
        history = []
        
        # Get recent messages (excluding current)
        messages = session.messages[:-1] if session.messages else []
        
        for message in messages:
            if message.role in ["user", "assistant"]:
                # Map to Cohere format
                cohere_role = "USER" if message.role == "user" else "CHATBOT"
                history.append({
                    "role": cohere_role,
                    "message": message.content
                })
        
        return history
    
    def _process_cohere_response(
        self, 
        response: Any, 
        execution_time: float,
        config: IAgentConfiguration
    ) -> AgentResponse:
        """Process Cohere API response"""
        try:
            # Extract content from response
            content = response.text or ""
            
            # Handle tool calls if present
            tool_calls = None
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_calls = [
                    {
                        "name": tool_call.name,
                        "parameters": tool_call.parameters
                    }
                    for tool_call in response.tool_calls
                ]
            
            # Create agent message
            agent_message = AgentMessage(
                role="assistant",
                content=content,
                tool_calls=tool_calls,
                metadata={
                    "model": config.model,
                    "finish_reason": getattr(response, 'finish_reason', 'stop'),
                    "provider": "cohere",
                    "generation_id": getattr(response, 'generation_id', None)
                }
            )
            
            # Create usage information
            usage = None
            if hasattr(response, 'meta') and response.meta:
                tokens = getattr(response.meta, 'tokens', None) or getattr(response.meta, 'billed_units', {})
                if tokens:
                    usage = AgentUsage(
                        prompt_tokens=getattr(tokens, 'input_tokens', 0),
                        completion_tokens=getattr(tokens, 'output_tokens', 0),
                        total_tokens=getattr(tokens, 'input_tokens', 0) + getattr(tokens, 'output_tokens', 0),
                        model=config.model,
                        cost_estimate=self._estimate_cost(tokens, config.model)
                    )
            
            return AgentResponse(
                message=agent_message,
                usage=usage,
                execution_time=execution_time,
                provider_response=response
            )
            
        except Exception as e:
            logger.error(f"Failed to process Cohere response: {e}")
            return AgentResponse.error_response(e)
    
    async def _process_cohere_stream(
        self, 
        stream: Any, 
        start_time: float,
        config: IAgentConfiguration
    ) -> AsyncIterator[AgentResponse]:
        """Process streaming response from Cohere"""
        try:
            content_buffer = ""
            
            async for chunk in stream:
                if hasattr(chunk, 'event_type'):
                    if chunk.event_type == "text-generation":
                        # Accumulate text content
                        if hasattr(chunk, 'text'):
                            content_buffer += chunk.text
                            
                            # Create streaming response
                            agent_message = AgentMessage(
                                role="assistant",
                                content=content_buffer,
                                metadata={
                                    "model": config.model,
                                    "provider": "cohere",
                                    "streaming": True,
                                    "generation_id": getattr(chunk, 'generation_id', None)
                                }
                            )
                            
                            yield AgentResponse(
                                message=agent_message,
                                execution_time=time.time() - start_time,
                                provider_response=chunk
                            )
                    
                    elif chunk.event_type == "stream-end":
                        # Final response with complete metadata
                        agent_message = AgentMessage(
                            role="assistant",
                            content=content_buffer,
                            metadata={
                                "model": config.model,
                                "provider": "cohere",
                                "streaming": False,
                                "finish_reason": getattr(chunk, 'finish_reason', 'stop'),
                                "generation_id": getattr(chunk, 'generation_id', None)
                            }
                        )
                        
                        # Create usage information if available
                        usage = None
                        if hasattr(chunk, 'response') and hasattr(chunk.response, 'meta'):
                            tokens = getattr(chunk.response.meta, 'tokens', None) or getattr(chunk.response.meta, 'billed_units', {})
                            if tokens:
                                usage = AgentUsage(
                                    prompt_tokens=getattr(tokens, 'input_tokens', 0),
                                    completion_tokens=getattr(tokens, 'output_tokens', 0),
                                    total_tokens=getattr(tokens, 'input_tokens', 0) + getattr(tokens, 'output_tokens', 0),
                                    model=config.model,
                                    cost_estimate=self._estimate_cost(tokens, config.model)
                                )
                        
                        yield AgentResponse(
                            message=agent_message,
                            usage=usage,
                            execution_time=time.time() - start_time,
                            provider_response=chunk
                        )
                        
        except Exception as e:
            logger.error(f"Cohere streaming error: {e}")
            yield AgentResponse.error_response(e)
    
    def _estimate_cost(self, tokens: Any, model: str) -> float:
        """Estimate cost based on token usage and model"""
        # Cohere pricing (approximate, as of 2024)
        pricing = {
            "command-r-plus": {"input": 3.0, "output": 15.0},  # per 1M tokens
            "command-r": {"input": 0.5, "output": 1.5},
            "command": {"input": 1.0, "output": 2.0},
            "command-nightly": {"input": 1.0, "output": 2.0},
            "command-light": {"input": 0.3, "output": 0.6},
            "command-light-nightly": {"input": 0.3, "output": 0.6}
        }
        
        if model not in pricing:
            return 0.0
        
        input_tokens = getattr(tokens, 'input_tokens', 0)
        output_tokens = getattr(tokens, 'output_tokens', 0)
        
        input_cost = (input_tokens / 1_000_000) * pricing[model]["input"]
        output_cost = (output_tokens / 1_000_000) * pricing[model]["output"]
        
        return input_cost + output_cost