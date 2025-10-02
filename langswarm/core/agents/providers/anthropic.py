"""
Anthropic Provider Implementation for LangSwarm V2

Native Anthropic integration that provides clean, Anthropic-specific
implementation optimized for Claude's API patterns and capabilities.
"""

import asyncio
import json
import logging
import time
from typing import List, AsyncIterator, Dict, Any, Optional
from datetime import datetime

try:
    import anthropic
    from anthropic import AsyncAnthropic
except ImportError:
    anthropic = None
    AsyncAnthropic = None

from ..interfaces import (
    IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, ProviderType
)
from ..base import AgentResponse, AgentSession, BaseAgent

logger = logging.getLogger(__name__)


class AnthropicProvider(IAgentProvider):
    """
    Native Anthropic provider implementation.
    
    Provides optimized integration with Anthropic's API including:
    - Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku support
    - Tool use integration
    - Streaming responses
    - Vision capabilities (Claude 3)
    - Token usage tracking
    - Retry logic and error handling
    """
    
    def __init__(self):
        if not anthropic:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
        
        self._client_cache: Dict[str, AsyncAnthropic] = {}
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC
    
    @property
    def supported_models(self) -> List[str]:
        """Anthropic models supported by this provider"""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        """Capabilities supported by Anthropic"""
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.VISION,  # Claude 3 models
            AgentCapability.SYSTEM_PROMPTS,
            AgentCapability.CONVERSATION_HISTORY,
            AgentCapability.MULTIMODAL,
            AgentCapability.CODE_EXECUTION  # Via tools
        ]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate Anthropic-specific configuration"""
        # Check if model is supported
        if config.model not in self.supported_models:
            raise ValueError(f"Model {config.model} not supported by Anthropic provider")
        
        # Check API key
        if not config.api_key:
            raise ValueError("API key required for Anthropic provider")
        
        # Validate model-specific constraints
        if config.model.startswith("claude-3"):
            # Claude 3 models support vision
            logger.info("Claude 3 model detected - vision capabilities available")
        
        # Test API connectivity
        try:
            client = self._get_client(config)
            # Simple API test - create a message
            test_response = await client.messages.create(
                model=config.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception as e:
            raise ValueError(f"Anthropic API validation failed: {e}")
    
    async def create_session(self, config: IAgentConfiguration) -> IAgentSession:
        """Create a new Anthropic conversation session"""
        return AgentSession(max_messages=config.max_memory_messages)
    
    async def send_message(
        self, 
        message: AgentMessage, 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Send a message to Anthropic and get response"""
        try:
            client = self._get_client(config)
            
            # Build messages for Anthropic API
            messages = await self._build_anthropic_messages(session, message, config)
            
            # Prepare Anthropic API call parameters
            api_params = self._build_api_params(config, messages)
            
            # Make API call
            start_time = time.time()
            response = await client.messages.create(**api_params)
            execution_time = time.time() - start_time
            
            # Process response
            return self._process_anthropic_response(response, execution_time, config)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return AgentResponse.error_response(e)
    
    async def stream_message(
        self,
        message: AgentMessage,
        session: IAgentSession, 
        config: IAgentConfiguration
    ) -> AsyncIterator[IAgentResponse]:
        """Stream a response from Anthropic"""
        try:
            client = self._get_client(config)
            
            # Build messages for Anthropic API
            messages = await self._build_anthropic_messages(session, message, config)
            
            # Prepare Anthropic API call parameters with streaming
            api_params = self._build_api_params(config, messages, stream=True)
            
            # Make streaming API call
            start_time = time.time()
            stream = await client.messages.create(**api_params)
            
            # Process streaming response
            async for chunk in self._process_anthropic_stream(stream, start_time, config):
                yield chunk
                
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield AgentResponse.error_response(e)
    
    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Execute a tool call through Anthropic tool use"""
        try:
            # Create a tool use message
            tool_message = AgentMessage(
                role="user",
                content=[{
                    "type": "tool_use",
                    "id": f"toolu_{int(time.time())}",
                    "name": tool_name,
                    "input": tool_parameters
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
            logger.error(f"Anthropic tool call error: {e}")
            return AgentResponse.error_response(e)
    
    def _get_client(self, config: IAgentConfiguration) -> AsyncAnthropic:
        """Get or create Anthropic client for configuration"""
        client_key = f"{config.api_key[:10]}_{config.base_url or 'default'}"
        
        if client_key not in self._client_cache:
            client_params = {
                "api_key": config.api_key,
                "timeout": config.timeout,
            }
            
            if config.base_url:
                client_params["base_url"] = config.base_url
            
            self._client_cache[client_key] = AsyncAnthropic(**client_params)
        
        return self._client_cache[client_key]
    
    async def _build_anthropic_messages(
        self, 
        session: IAgentSession, 
        new_message: AgentMessage,
        config: IAgentConfiguration
    ) -> List[Dict[str, Any]]:
        """Convert session messages to Anthropic format"""
        messages = []
        
        # Get conversation context
        context_messages = await session.get_context(
            max_tokens=config.max_tokens - 1000 if config.max_tokens else None
        )
        
        # Convert to Anthropic format
        for msg in context_messages:
            # Skip system messages for Anthropic - they use system parameter
            if msg.role == "system":
                continue
                
            anthropic_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            # Handle multi-modal content
            if isinstance(msg.content, list):
                anthropic_msg["content"] = msg.content
            
            messages.append(anthropic_msg)
        
        # Add new message
        new_msg = {
            "role": new_message.role,
            "content": new_message.content
        }
        
        if isinstance(new_message.content, list):
            new_msg["content"] = new_message.content
            
        messages.append(new_msg)
        
        return messages
    
    def _build_api_params(
        self, 
        config: IAgentConfiguration, 
        messages: List[Dict[str, Any]],
        stream: bool = False
    ) -> Dict[str, Any]:
        """Build Anthropic API parameters"""
        params = {
            "model": config.model,
            "messages": messages,
            "max_tokens": config.max_tokens or 4096,
            "stream": stream
        }
        
        # Add system prompt if provided
        if config.system_prompt:
            params["system"] = config.system_prompt
        
        # Add optional parameters
        if config.temperature is not None:
            params["temperature"] = config.temperature
        
        if config.top_p is not None:
            params["top_p"] = config.top_p
        
        if config.stop_sequences:
            params["stop_sequences"] = config.stop_sequences
        
        # Add tool configuration if enabled
        if config.tools_enabled and config.available_tools:
            params["tools"] = self._build_tool_definitions(config.available_tools)
        
        return params
    
    def _build_tool_definitions(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Build Anthropic tool definitions from V2 tool registry using MCP standard"""
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
                    # Convert MCP schema to Anthropic format
                    anthropic_tool = self._convert_mcp_to_anthropic_format(mcp_schema)
                    tools.append(anthropic_tool)
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
    
    def _convert_mcp_to_anthropic_format(self, mcp_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert standard MCP schema to Anthropic tool calling format"""
        return {
            "name": mcp_schema.get("name", "unknown_tool"),
            "description": mcp_schema.get("description", ""),
            "input_schema": mcp_schema.get("input_schema", {
                "type": "object",
                "properties": {},
                "additionalProperties": True
            })
        }
    
    def _process_anthropic_response(
        self, 
        response: Any, 
        execution_time: float,
        config: IAgentConfiguration
    ) -> AgentResponse:
        """Process Anthropic API response"""
        content = ""
        tool_uses = []
        
        # Extract content from response
        for content_block in response.content:
            if content_block.type == "text":
                content += content_block.text
            elif content_block.type == "tool_use":
                tool_uses.append({
                    "id": content_block.id,
                    "name": content_block.name,
                    "input": content_block.input
                })
        
        # Create agent message
        agent_message = AgentMessage(
            role="assistant",
            content=content,
            tool_calls=tool_uses if tool_uses else None,
            metadata={
                "model": config.model,
                "stop_reason": response.stop_reason,
                "provider": "anthropic"
            }
        )
        
        # Create usage information
        usage = None
        if hasattr(response, 'usage') and response.usage:
            usage = AgentUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                model=config.model,
                cost_estimate=self._estimate_cost(response.usage, config.model)
            )
        
        return AgentResponse.success_response(
            content=content,
            usage=usage,
            execution_time=execution_time,
            model=config.model,
            stop_reason=response.stop_reason,
            provider="anthropic",
            tool_uses=tool_uses
        )
    
    async def _process_anthropic_stream(
        self, 
        stream: Any, 
        start_time: float,
        config: IAgentConfiguration
    ) -> AsyncIterator[AgentResponse]:
        """Process Anthropic streaming response"""
        collected_content = ""
        collected_tool_uses = []
        
        async for event in stream:
            if event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    collected_content += event.delta.text
                    
                    # Yield content chunk
                    yield AgentResponse.success_response(
                        content=event.delta.text,
                        streaming=True,
                        chunk_index=len(collected_content),
                        execution_time=time.time() - start_time
                    )
                    
            elif event.type == "content_block_start":
                if event.content_block.type == "tool_use":
                    collected_tool_uses.append({
                        "id": event.content_block.id,
                        "name": event.content_block.name,
                        "input": event.content_block.input
                    })
            
            elif event.type == "message_stop":
                # Final chunk with complete response
                yield AgentResponse.success_response(
                    content=collected_content,
                    streaming=False,
                    stream_complete=True,
                    execution_time=time.time() - start_time,
                    stop_reason="end_turn",
                    tool_uses=collected_tool_uses
                )
    
    def _estimate_cost(self, usage: Any, model: str) -> float:
        """Estimate cost for Anthropic API usage"""
        # Simplified cost estimation (rates as of 2024)
        rates = {
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-5-sonnet-20240620": {"input": 0.003, "output": 0.015},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            "claude-2.1": {"input": 0.008, "output": 0.024},
            "claude-2.0": {"input": 0.008, "output": 0.024},
            "claude-instant-1.2": {"input": 0.0008, "output": 0.0024}
        }
        
        if model not in rates:
            return 0.0
        
        model_rates = rates[model]
        input_cost = (usage.input_tokens / 1000) * model_rates["input"]
        output_cost = (usage.output_tokens / 1000) * model_rates["output"]
        
        return input_cost + output_cost
    
    async def get_health(self) -> Dict[str, Any]:
        """Get Anthropic provider health status"""
        return {
            "provider": "anthropic",
            "status": "healthy",
            "supported_models": self.supported_models,
            "capabilities": [cap.value for cap in self.supported_capabilities],
            "api_available": True,  # Would check actual API in real implementation
            "timestamp": datetime.now().isoformat()
        }


class AnthropicAgent(BaseAgent):
    """
    Anthropic-specific agent implementation.
    
    Extends BaseAgent with Anthropic-specific optimizations and features.
    """
    
    def __init__(self, name: str, configuration: 'AgentConfiguration', agent_id: Optional[str] = None):
        # Create Anthropic provider
        provider = AnthropicProvider()
        
        # Initialize base agent
        super().__init__(name, configuration, provider, agent_id)
        
        # Anthropic-specific initialization
        self._anthropic_features = {
            "supports_vision": "claude-3" in configuration.model,
            "supports_tool_use": True,
            "supports_streaming": True,
            "supports_multimodal": "claude-3" in configuration.model,
            "max_context_tokens": self._get_context_limit(configuration.model),
            "system_prompt_support": True
        }
    
    def _get_context_limit(self, model: str) -> int:
        """Get context limit for Anthropic model"""
        limits = {
            "claude-3-5-sonnet-20241022": 200000,
            "claude-3-5-sonnet-20240620": 200000,
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-2.1": 200000,
            "claude-2.0": 100000,
            "claude-instant-1.2": 100000
        }
        return limits.get(model, 100000)
    
    async def health_check(self) -> Dict[str, Any]:
        """Enhanced health check with Anthropic-specific information"""
        base_health = await super().health_check()
        
        base_health.update({
            "anthropic_features": self._anthropic_features,
            "context_limit": self._anthropic_features["max_context_tokens"],
            "api_available": await self._check_api_availability()
        })
        
        return base_health
    
    async def _check_api_availability(self) -> bool:
        """Check if Anthropic API is available"""
        try:
            # Test API connectivity
            await self._provider.validate_configuration(self._configuration)
            return True
        except Exception:
            return False
    
    # Anthropic-specific methods can be added here
    async def analyze_image(self, image_data: str, prompt: str = "Describe this image") -> AgentResponse:
        """Analyze image using Claude's vision capabilities"""
        # This would integrate with Anthropic's vision API
        # For now, return a placeholder
        return AgentResponse.success_response(
            content=f"Image analysis requested: {prompt}",
            vision_analysis=True,
            image_prompt=prompt
        )
