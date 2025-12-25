"""
Google Gemini Provider Implementation for LangSwarm V2

Native Gemini integration that provides clean, Google-specific
implementation optimized for Gemini's API patterns and capabilities.
"""

import asyncio
import json
import logging
import time
from typing import List, AsyncIterator, Dict, Any, Optional
from datetime import datetime

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None

from ..interfaces import (
    IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, ProviderType
)
from ..base import AgentResponse, AgentSession, BaseAgent

logger = logging.getLogger(__name__)


class GeminiProvider(IAgentProvider):
    """
    Native Google Gemini provider implementation.
    
    Provides optimized integration with Google's Gemini API including:
    - Gemini Pro, Gemini Pro Vision, Gemini Ultra support
    - Function calling integration
    - Streaming responses
    - Vision and multimodal capabilities
    - Safety settings and content filtering
    - Token usage tracking
    """
    
    def __init__(self):
        if not genai:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
        
        self._models_cache: Dict[str, Any] = {}
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GEMINI
    
    @property
    def supported_models(self) -> List[str]:
        """Gemini models supported by this provider - sourced from centralized config"""
        from .config import get_supported_models
        return get_supported_models("gemini")
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        """Capabilities supported by Gemini"""
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.FUNCTION_CALLING,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.VISION,
            AgentCapability.SYSTEM_PROMPTS,
            AgentCapability.CONVERSATION_HISTORY,
            AgentCapability.MULTIMODAL,
            AgentCapability.CODE_EXECUTION
        ]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate Gemini-specific configuration"""
        # Check if model is supported
        if config.model not in self.supported_models:
            raise ValueError(f"Model {config.model} not supported by Gemini provider")
        
        # Check API key
        if not config.api_key:
            raise ValueError("API key required for Gemini provider")
        
        # Validate model-specific constraints
        if "vision" in config.model.lower():
            logger.info("Vision model detected - multimodal capabilities available")
        
        # Test API connectivity
        try:
            genai.configure(api_key=config.api_key)
            # Simple API test - list models
            models = genai.list_models()
            return True
        except Exception as e:
            raise ValueError(f"Gemini API validation failed: {e}")
    
    async def create_session(self, config: IAgentConfiguration) -> IAgentSession:
        """Create a new Gemini conversation session"""
        return AgentSession(max_messages=config.max_memory_messages)
    
    async def send_message(
        self, 
        message: AgentMessage, 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Send a message to Gemini and get response"""
        try:
            # Configure Gemini
            genai.configure(api_key=config.api_key)
            model = self._get_model(config)
            
            # Build messages for Gemini API
            prompt = await self._build_gemini_prompt(session, message, config)
            
            # Make API call
            start_time = time.time()
            response = await asyncio.to_thread(model.generate_content, prompt)
            execution_time = time.time() - start_time
            
            # Process response
            return self._process_gemini_response(response, execution_time, config)
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return AgentResponse.error_response(e)
    
    async def stream_message(
        self,
        message: AgentMessage,
        session: IAgentSession, 
        config: IAgentConfiguration
    ) -> AsyncIterator[IAgentResponse]:
        """Stream a response from Gemini"""
        try:
            # Configure Gemini
            genai.configure(api_key=config.api_key)
            model = self._get_model(config)
            
            # Build prompt for Gemini API
            prompt = await self._build_gemini_prompt(session, message, config)
            
            # Make streaming API call
            start_time = time.time()
            response_stream = await asyncio.to_thread(model.generate_content, prompt, stream=True)
            
            # Process streaming response
            async for chunk in self._process_gemini_stream(response_stream, start_time, config):
                yield chunk
                
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield AgentResponse.error_response(e)
    
    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Execute a tool call through Gemini function calling"""
        try:
            # Create a tool call message
            tool_message = AgentMessage(
                role="user",
                content=f"Use the {tool_name} function with these parameters: {json.dumps(tool_parameters)}",
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
            logger.error(f"Gemini tool call error: {e}")
            return AgentResponse.error_response(e)
    
    def _get_model(self, config: IAgentConfiguration):
        """Get or create Gemini model for configuration"""
        model_key = f"{config.model}_{config.api_key[:10]}"
        
        if model_key not in self._models_cache:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=config.temperature or 0.7,
                max_output_tokens=config.max_tokens or 4096,
                top_p=config.top_p or 0.95,
                stop_sequences=config.stop_sequences or []
            )
            
            # Configure safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            # Add tools if enabled
            tools = None
            if config.tools_enabled and config.available_tools:
                tools = self._build_tool_definitions(config.available_tools)
            
            # Build system instruction with tool instructions
            system_instruction = config.system_prompt or ""
            if config.tools_enabled and config.available_tools:
                tool_instructions = self._get_tool_instructions(config.available_tools)
                if tool_instructions:
                    system_instruction += f"\n\n# Available Tools\n{tool_instructions}"
            
            # Create model
            model = genai.GenerativeModel(
                model_name=config.model,
                generation_config=generation_config,
                safety_settings=safety_settings,
                system_instruction=system_instruction if system_instruction else None,
                tools=tools
            )
            
            self._models_cache[model_key] = model
        
        return self._models_cache[model_key]
    
    def _build_tool_definitions(self, tool_names: List[str]) -> List[Dict[str, Any]]:
        """Build Gemini tool definitions from V2 tool registry using MCP standard"""
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
                    # Convert MCP schema to Gemini format (use registry key as name)
                    gemini_tool = self._convert_mcp_to_gemini_format(mcp_schema, tool_name)
                    tools.append(gemini_tool)
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
    
    def _convert_mcp_to_gemini_format(self, mcp_schema: Dict[str, Any], tool_name: str = None) -> Dict[str, Any]:
        """Convert standard MCP schema to Gemini function calling format"""
        # Use the registry key (tool_name) to ensure valid tool name
        function_name = tool_name if tool_name else mcp_schema.get("name", "unknown_tool")
        
        return {
            "function_declarations": [{
                "name": function_name,
                "description": mcp_schema.get("description", ""),
                "parameters": mcp_schema.get("input_schema", {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True
                })
            }]
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
    
    async def _build_gemini_prompt(
        self, 
        session: IAgentSession, 
        new_message: AgentMessage,
        config: IAgentConfiguration
    ) -> str:
        """Convert session messages to Gemini prompt format"""
        # Get conversation context
        context_messages = await session.get_context(
            max_tokens=config.max_tokens - 1000 if config.max_tokens else None
        )
        
        # Build conversation history
        conversation_parts = []
        
        for msg in context_messages:
            # Skip None messages
            if msg is None:
                continue
            if msg.role == "user":
                conversation_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                conversation_parts.append(f"Assistant: {msg.content}")
            # Skip system messages as they're handled by system_instruction
        
        # Add new message
        conversation_parts.append(f"User: {new_message.content}")
        
        # Join into single prompt
        prompt = "\n\n".join(conversation_parts)
        
        return prompt
    
    def _process_gemini_response(
        self, 
        response: Any, 
        execution_time: float,
        config: IAgentConfiguration
    ) -> AgentResponse:
        """Process Gemini API response"""
        try:
            # Extract content from response
            content = response.text or ""
            
            # Create agent message
            agent_message = AgentMessage(
                role="assistant",
                content=content,
                metadata={
                    "model": config.model,
                    "finish_reason": getattr(response, 'finish_reason', 'stop'),
                    "provider": "gemini",
                    "safety_ratings": getattr(response, 'safety_ratings', [])
                }
            )
            
            # Create usage information (Gemini doesn't provide detailed usage by default)
            usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = AgentUsage(
                    prompt_tokens=getattr(response.usage_metadata, 'prompt_token_count', 0),
                    completion_tokens=getattr(response.usage_metadata, 'candidates_token_count', 0),
                    total_tokens=getattr(response.usage_metadata, 'total_token_count', 0),
                    model=config.model,
                    cost_estimate=self._estimate_cost(response.usage_metadata, config.model)
                )
            
            return AgentResponse.success_response(
                content=content,
                message=agent_message,  # Pass the detailed message object
                usage=usage,
                execution_time=execution_time,
                model=config.model,
                finish_reason=getattr(response, 'finish_reason', 'stop'),
                provider="gemini",
                safety_ratings=getattr(response, 'safety_ratings', [])
            )
            
        except Exception as e:
            logger.error(f"Error processing Gemini response: {e}")
            return AgentResponse.error_response(e)
    
    async def _process_gemini_stream(
        self, 
        stream: Any, 
        start_time: float,
        config: IAgentConfiguration
    ) -> AsyncIterator[AgentResponse]:
        """Process Gemini streaming response"""
        collected_content = ""
        collected_tool_calls = []
        
        try:
            for chunk in stream:
                # Handle text content
                if hasattr(chunk, 'text') and chunk.text:
                    collected_content += chunk.text
                    
                    # Yield content chunk
                    yield AgentResponse.success_response(
                        content=chunk.text,
                        streaming=True,
                        chunk_index=len(collected_content),
                        execution_time=time.time() - start_time,
                        model=config.model,
                        provider="gemini"
                    )
                
                # Handle function calls in parts
                if hasattr(chunk, 'parts'):
                    for part in chunk.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            # Gemini provides complete function calls in parts, not deltas
                            fc = part.function_call
                            
                            # Convert to standard tool call format
                            tool_call = {
                                "id": f"call_{int(time.time())}_{len(collected_tool_calls)}",
                                "name": fc.name,
                                "arguments": dict(fc.args),
                                "type": "function"
                            }
                            collected_tool_calls.append(tool_call)
            
            # Final chunk signals completion - EMPTY content since all content already sent
            # This prevents duplication when applications concatenate all chunks
            
            # Create final message with tool calls
            final_message = AgentMessage(
                role="assistant",
                content="",
                tool_calls=collected_tool_calls if collected_tool_calls else None,
                metadata={
                    "model": config.model,
                    "provider": "gemini",
                    "stream_complete": True,
                    "total_content": collected_content
                }
            )
            
            yield AgentResponse.success_response(
                content="",  # Empty - prevents duplication
                message=final_message,
                streaming=False,
                stream_complete=True,
                execution_time=time.time() - start_time,
                model=config.model,
                provider="gemini",
                total_collected_content=collected_content  # Available in metadata if needed
            )
            
        except Exception as e:
            logger.error(f"Error processing Gemini stream: {e}")
            yield AgentResponse.error_response(e)
    
    def _estimate_cost(self, usage: Any, model: str) -> float:
        """Estimate cost for Gemini API usage (prices per 1K tokens, updated Nov 2024)"""
        # Pricing from https://ai.google.dev/pricing
        # Note: Gemini has free tier for low usage, these are pay-as-you-go rates
        rates = {
            # Gemini 2.0 (experimental, pricing TBD - using flash estimates)
            "gemini-2.0-flash-exp": {"input": 0.000075, "output": 0.0003},
            "gemini-2.0-flash-thinking-exp-1219": {"input": 0.000075, "output": 0.0003},
            
            # Gemini 1.5 Pro (up to 128K context)
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-pro-latest": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-pro-002": {"input": 0.00125, "output": 0.005},
            
            # Gemini 1.5 Flash (fast & efficient)
            "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
            "gemini-1.5-flash-latest": {"input": 0.000075, "output": 0.0003},
            "gemini-1.5-flash-002": {"input": 0.000075, "output": 0.0003},
            "gemini-1.5-flash-8b": {"input": 0.0000375, "output": 0.00015},
            
            # Gemini 1.0 (legacy)
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-pro-vision": {"input": 0.0005, "output": 0.0015},
            
            # Experimental
            "gemini-exp-1206": {"input": 0.00125, "output": 0.005},
            "learnlm-1.5-pro-experimental": {"input": 0.00125, "output": 0.005},
        }
        
        if not hasattr(usage, 'prompt_token_count'):
            return 0.0
        
        # Try exact match first, then prefix match
        model_rates = rates.get(model)
        if not model_rates:
            for rate_model in rates:
                if model.startswith(rate_model.split("-latest")[0].split("-002")[0]):
                    model_rates = rates[rate_model]
                    break
        
        if not model_rates:
            return 0.0
        
        input_cost = (getattr(usage, 'prompt_token_count', 0) / 1000) * model_rates["input"]
        output_cost = (getattr(usage, 'candidates_token_count', 0) / 1000) * model_rates["output"]
        
        return input_cost + output_cost
    
    async def get_health(self) -> Dict[str, Any]:
        """Get Gemini provider health status"""
        return {
            "provider": "gemini",
            "status": "healthy",
            "supported_models": self.supported_models,
            "capabilities": [cap.value for cap in self.supported_capabilities],
            "api_available": True,  # Would check actual API in real implementation
            "safety_settings": "enabled",
            "timestamp": datetime.now().isoformat()
        }


class GeminiAgent(BaseAgent):
    """
    Gemini-specific agent implementation.
    
    Extends BaseAgent with Gemini-specific optimizations and features.
    """
    
    def __init__(self, name: str, configuration: 'AgentConfiguration', agent_id: Optional[str] = None):
        # Create Gemini provider
        provider = GeminiProvider()
        
        # Initialize base agent
        super().__init__(name, configuration, provider, agent_id)
        
        # Gemini-specific initialization
        self._gemini_features = {
            "supports_vision": "vision" in configuration.model.lower(),
            "supports_function_calling": True,
            "supports_streaming": True,
            "supports_multimodal": True,
            "supports_safety_settings": True,
            "max_context_tokens": self._get_context_limit(configuration.model),
            "system_instruction_support": True
        }
    
    def _get_context_limit(self, model: str) -> int:
        """Get context limit for Gemini model"""
        limits = {
            "gemini-pro": 32768,
            "gemini-pro-vision": 16384,
            "gemini-ultra": 32768,
            "gemini-1.5-pro": 2097152,  # 2M tokens
            "gemini-1.5-flash": 1048576   # 1M tokens
        }
        return limits.get(model, 32768)
    
    async def health_check(self) -> Dict[str, Any]:
        """Enhanced health check with Gemini-specific information"""
        base_health = await super().health_check()
        
        base_health.update({
            "gemini_features": self._gemini_features,
            "context_limit": self._gemini_features["max_context_tokens"],
            "api_available": await self._check_api_availability()
        })
        
        return base_health
    
    async def _check_api_availability(self) -> bool:
        """Check if Gemini API is available"""
        try:
            # Test API connectivity
            await self._provider.validate_configuration(self._configuration)
            return True
        except Exception:
            return False
    
    # Gemini-specific methods can be added here
    async def analyze_image(self, image_data: str, prompt: str = "Describe this image") -> AgentResponse:
        """Analyze image using Gemini's vision capabilities"""
        # This would integrate with Gemini's vision API
        # For now, return a placeholder
        return AgentResponse.success_response(
            content=f"Image analysis requested: {prompt}",
            vision_analysis=True,
            image_prompt=prompt,
            gemini_vision=True
        )
