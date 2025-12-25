"""
Mistral Provider Implementation for LangSwarm V2
"""

import asyncio
import json
import logging
import time
from typing import List, AsyncIterator, Dict, Any, Optional

try:
    from mistralai.async_client import MistralAsyncClient
    from mistralai.models.chat_completion import ChatMessage
except ImportError:
    MistralAsyncClient = None
    ChatMessage = None

from ..interfaces import (
    IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, ProviderType
)
from ..base import AgentResponse, AgentSession

logger = logging.getLogger(__name__)


class MistralProvider(IAgentProvider):
    """Native Mistral provider implementation with tool support"""
    
    def __init__(self):
        if not MistralAsyncClient:
            raise ImportError("Mistral package not installed. Run: pip install mistralai")
        
        self._client_cache: Dict[str, MistralAsyncClient] = {}
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.MISTRAL
    
    @property
    def supported_models(self) -> List[str]:
        """Mistral models supported by this provider - sourced from centralized config"""
        from .config import get_supported_models
        return get_supported_models("mistral")
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.FUNCTION_CALLING,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING
        ]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate Mistral configuration"""
        if config.model not in self.supported_models:
            raise ValueError(f"Model {config.model} not supported")
        if not config.api_key:
            raise ValueError("API key required")
        return True
    
    async def create_session(self, config: IAgentConfiguration) -> IAgentSession:
        """Create a new session"""
        return AgentSession(max_messages=config.max_memory_messages)
    
    async def send_message(
        self, 
        message: AgentMessage, 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Send message to Mistral"""
        try:
            client = self._get_client(config)
            messages = self._build_messages(session, message, config)
            tools = None
            
            if config.tools_enabled and config.available_tools:
                tools = self._build_tool_definitions(config.available_tools)
            
            start_time = time.time()
            response = await client.chat(
                model=config.model,
                messages=messages,
                tools=tools,
                temperature=config.temperature or 0.7,
                max_tokens=config.max_tokens or 4096
            )
            execution_time = time.time() - start_time
            
            return self._process_response(response, execution_time, config)
            
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            return AgentResponse.error_response(e)
    
    async def stream_message(
        self,
        message: AgentMessage,
        session: IAgentSession, 
        config: IAgentConfiguration
    ) -> AsyncIterator[IAgentResponse]:
        """Stream response from Mistral"""
        try:
            client = self._get_client(config)
            messages = self._build_messages(session, message, config)
            tools = None
            
            if config.tools_enabled and config.available_tools:
                tools = self._build_tool_definitions(config.available_tools)
            
            start_time = time.time()
            stream = await client.chat_stream(
                model=config.model,
                messages=messages,
                tools=tools,
                temperature=config.temperature or 0.7,
                max_tokens=config.max_tokens or 4096
            )
            
            content_buffer = ""
            async for chunk in stream:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        content_buffer += delta.content
                        yield AgentResponse(
                            message=AgentMessage(
                                role="assistant",
                                content=content_buffer,
                                metadata={"provider": "mistral", "streaming": True}
                            ),
                            execution_time=time.time() - start_time,
                            provider_response=chunk
                        )
                        
        except Exception as e:
            logger.error(f"Mistral streaming error: {e}")
            yield AgentResponse.error_response(e)
    
    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Execute tool call"""
        tool_message = AgentMessage(
            role="user",
            content=f"Use {tool_name} with {json.dumps(tool_parameters)}"
        )
        return await self.send_message(tool_message, session, config)
    
    def _get_client(self, config: IAgentConfiguration) -> MistralAsyncClient:
        """Get Mistral client"""
        client_key = f"{config.api_key[:10]}"
        if client_key not in self._client_cache:
            self._client_cache[client_key] = MistralAsyncClient(api_key=config.api_key)
        return self._client_cache[client_key]
    
    def _build_tool_definitions(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Build Mistral tool definitions"""
        try:
            from langswarm.tools.registry import ToolRegistry
            registry = ToolRegistry()
            
            if not registry._tools:
                registry.auto_populate_with_mcp_tools()
            
            tools = []
            for tool_name in tool_names:
                tool_info = registry.get_tool(tool_name)
                if tool_info:
                    mcp_schema = self._get_tool_mcp_schema(tool_info)
                    mistral_tool = self._convert_mcp_to_mistral_format(mcp_schema, tool_name)
                    tools.append(mistral_tool)
            
            return tools
        except Exception as e:
            raise RuntimeError(f"Failed to build tool definitions: {e}")
    
    def _get_tool_mcp_schema(self, tool: Any) -> Dict[str, Any]:
        """Get MCP schema from tool (IToolInterface object)"""
        if hasattr(tool, 'list_tools'):
            tools_list = tool.list_tools()
            if tools_list:
                return tools_list[0]
        
        if hasattr(tool, 'metadata'):
            metadata = tool.metadata
            return {
                "name": getattr(metadata, 'name', 'unknown'),
                "description": getattr(metadata, 'description', ''),
                "input_schema": getattr(metadata, 'input_schema', {"type": "object", "properties": {}})
            }
        
        return {
            "name": str(tool),
            "description": "",
            "input_schema": {"type": "object", "properties": {}}
        }
    
    def _convert_mcp_to_mistral_format(self, mcp_schema: Dict[str, Any], tool_name: str = None) -> Dict[str, Any]:
        """Convert MCP to Mistral format"""
        # Use the registry key (tool_name) to ensure valid tool name
        function_name = tool_name if tool_name else mcp_schema.get("name", "unknown_tool")
        
        return {
            "type": "function",
            "function": {
                "name": function_name,
                "description": mcp_schema.get("description", ""),
                "parameters": mcp_schema.get("input_schema", {
                    "type": "object",
                    "properties": {}
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
    
    def _build_messages(
        self, 
        session: IAgentSession, 
        new_message: AgentMessage,
        config: IAgentConfiguration
    ) -> List[ChatMessage]:
        """Build messages for Mistral"""
        messages = []
        
        # Build system prompt with tool instructions
        system_content = config.system_prompt or ""
        if config.tools_enabled and config.available_tools:
            tool_instructions = self._get_tool_instructions(config.available_tools)
            if tool_instructions:
                system_content += f"\n\n# Available Tools\n{tool_instructions}"
        
        if system_content:
            messages.append(ChatMessage(role="system", content=system_content))
        
        for msg in session.messages:
            # Skip None messages
            if msg is None:
                continue
            if msg.role in ["user", "assistant"]:
                messages.append(ChatMessage(role=msg.role, content=msg.content))
        
        messages.append(ChatMessage(role=new_message.role, content=new_message.content))
        return messages
    
    def _process_response(
        self, 
        response: Any, 
        execution_time: float,
        config: IAgentConfiguration
    ) -> AgentResponse:
        """Process Mistral response"""
        try:
            choice = response.choices[0]
            message = choice.message
            
            agent_message = AgentMessage(
                role="assistant",
                content=message.content or "",
                metadata={
                    "model": config.model,
                    "provider": "mistral",
                    "finish_reason": choice.finish_reason
                }
            )
            
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = AgentUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    model=config.model
                )
            
            return AgentResponse(
                message=agent_message,
                usage=usage,
                execution_time=execution_time,
                provider_response=response
            )
            
        except Exception as e:
            logger.error(f"Failed to process Mistral response: {e}")
            return AgentResponse.error_response(e)