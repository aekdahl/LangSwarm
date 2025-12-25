"""
Hugging Face Provider Implementation for LangSwarm V2

Native Hugging Face integration supporting both local and remote models
with custom tool calling implementation.
"""

import asyncio
import json
import logging
import time
from typing import List, AsyncIterator, Dict, Any, Optional

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    from huggingface_hub import AsyncInferenceClient
    import torch
except ImportError:
    AutoTokenizer = None
    AutoModelForCausalLM = None
    pipeline = None
    AsyncInferenceClient = None
    torch = None

from ..interfaces import (
    IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, ProviderType
)
from ..base import AgentResponse, AgentSession

logger = logging.getLogger(__name__)


class HuggingFaceProvider(IAgentProvider):
    """Hugging Face provider with local and remote model support"""
    
    def __init__(self):
        if not AutoTokenizer:
            raise ImportError("Transformers package not installed. Run: pip install transformers torch")
        
        self._model_cache: Dict[str, Any] = {}
        self._tokenizer_cache: Dict[str, Any] = {}
        self._client_cache: Dict[str, AsyncInferenceClient] = {}
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.HUGGINGFACE
    
    @property
    def supported_models(self) -> List[str]:
        return [
            # Popular instruction-tuned models
            "microsoft/DialoGPT-large",
            "microsoft/DialoGPT-medium",
            "facebook/blenderbot-400M-distill",
            "facebook/blenderbot-1B-distill",
            "huggingface/CodeBERTa-small-v1",
            "codellama/CodeLlama-7b-Instruct-hf",
            "codellama/CodeLlama-13b-Instruct-hf",
            "meta-llama/Llama-2-7b-chat-hf",
            "meta-llama/Llama-2-13b-chat-hf",
            "mistralai/Mistral-7B-Instruct-v0.1",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "HuggingFaceH4/zephyr-7b-beta",
            # Custom models (any HF model ID)
            "custom"
        ]
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.FUNCTION_CALLING,  # Custom implementation
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.CONVERSATION_HISTORY
        ]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate Hugging Face configuration"""
        # For remote inference, check API key
        if config.base_url and not config.api_key:
            logger.warning("No API key provided for remote inference")
        
        # Test model loading/access
        try:
            if config.base_url:
                # Remote inference
                client = self._get_client(config)
                # Simple test
                return True
            else:
                # Local model - try to load tokenizer
                tokenizer = self._get_tokenizer(config.model)
                return tokenizer is not None
        except Exception as e:
            raise ValueError(f"Hugging Face model validation failed: {e}")
    
    async def create_session(self, config: IAgentConfiguration) -> IAgentSession:
        """Create a new session"""
        return AgentSession(max_messages=config.max_memory_messages)
    
    async def send_message(
        self, 
        message: AgentMessage, 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Send message to Hugging Face model"""
        try:
            start_time = time.time()
            
            if config.base_url:
                # Remote inference
                response = await self._remote_inference(message, session, config)
            else:
                # Local inference
                response = await self._local_inference(message, session, config)
            
            execution_time = time.time() - start_time
            return self._process_response(response, execution_time, config, message)
            
        except Exception as e:
            logger.error(f"Hugging Face error: {e}")
            return AgentResponse.error_response(e)
    
    async def stream_message(
        self,
        message: AgentMessage,
        session: IAgentSession, 
        config: IAgentConfiguration
    ) -> AsyncIterator[IAgentResponse]:
        """Stream response (simulated for local models)"""
        try:
            # For local models, simulate streaming by chunking response
            response = await self.send_message(message, session, config)
            
            if response.message and response.message.content:
                content = response.message.content
                chunk_size = 50  # Characters per chunk
                
                for i in range(0, len(content), chunk_size):
                    chunk = content[:i+chunk_size]
                    
                    agent_message = AgentMessage(
                        role="assistant",
                        content=chunk,
                        metadata={
                            "provider": "huggingface",
                            "streaming": True,
                            "model": config.model
                        }
                    )
                    
                    yield AgentResponse(
                        message=agent_message,
                        execution_time=response.execution_time,
                        provider_response=response.provider_response
                    )
                    
                    # Small delay to simulate streaming
                    await asyncio.sleep(0.1)
            else:
                yield response
                
        except Exception as e:
            logger.error(f"Hugging Face streaming error: {e}")
            yield AgentResponse.error_response(e)
    
    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Execute tool call with custom implementation"""
        # Create a structured prompt for tool calling
        tool_prompt = self._create_tool_prompt(tool_name, tool_parameters, config)
        
        tool_message = AgentMessage(
            role="user",
            content=tool_prompt,
            metadata={
                "tool_call": {
                    "name": tool_name,
                    "parameters": tool_parameters
                }
            }
        )
        
        return await self.send_message(tool_message, session, config)
    
    def _get_client(self, config: IAgentConfiguration) -> AsyncInferenceClient:
        """Get Hugging Face inference client"""
        client_key = f"{config.base_url}_{config.api_key[:10] if config.api_key else 'none'}"
        
        if client_key not in self._client_cache:
            self._client_cache[client_key] = AsyncInferenceClient(
                model=config.base_url,
                token=config.api_key
            )
        
        return self._client_cache[client_key]
    
    def _get_tokenizer(self, model_name: str):
        """Get or load tokenizer"""
        if model_name not in self._tokenizer_cache:
            try:
                self._tokenizer_cache[model_name] = AutoTokenizer.from_pretrained(model_name)
            except Exception as e:
                logger.error(f"Failed to load tokenizer for {model_name}: {e}")
                return None
        
        return self._tokenizer_cache[model_name]
    
    def _get_model(self, model_name: str):
        """Get or load model"""
        if model_name not in self._model_cache:
            try:
                # Load model with appropriate settings
                self._model_cache[model_name] = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None,
                    low_cpu_mem_usage=True
                )
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                return None
        
        return self._model_cache[model_name]
    
    async def _remote_inference(
        self, 
        message: AgentMessage, 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> str:
        """Perform remote inference"""
        client = self._get_client(config)
        
        # Build prompt from conversation
        prompt = self._build_conversation_prompt(session, message, config)
        
        # Make inference call
        response = await client.text_generation(
            prompt,
            max_new_tokens=config.max_tokens or 512,
            temperature=config.temperature or 0.7,
            top_p=config.top_p or 0.9,
            repetition_penalty=1.1,
            do_sample=True,
            return_full_text=False
        )
        
        return response
    
    async def _local_inference(
        self, 
        message: AgentMessage, 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> str:
        """Perform local inference"""
        model = self._get_model(config.model)
        tokenizer = self._get_tokenizer(config.model)
        
        if not model or not tokenizer:
            raise ValueError(f"Failed to load model {config.model}")
        
        # Build prompt
        prompt = self._build_conversation_prompt(session, message, config)
        
        # Tokenize
        inputs = tokenizer.encode(prompt, return_tensors="pt")
        
        # Generate
        with torch.no_grad():
            outputs = await asyncio.to_thread(
                model.generate,
                inputs,
                max_new_tokens=config.max_tokens or 512,
                temperature=config.temperature or 0.7,
                top_p=config.top_p or 0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode only the new tokens
        new_tokens = outputs[0][inputs.shape[-1]:]
        response = tokenizer.decode(new_tokens, skip_special_tokens=True)
        
        return response
    
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
    
    def _build_conversation_prompt(
        self, 
        session: IAgentSession, 
        new_message: AgentMessage,
        config: IAgentConfiguration
    ) -> str:
        """Build conversation prompt"""
        prompt_parts = []
        
        # Build system prompt with tool instructions
        system_content = config.system_prompt or ""
        if config.tools_enabled and config.available_tools:
            tool_instructions = self._get_tool_instructions(config.available_tools)
            if tool_instructions:
                system_content += f"\n\n# Available Tools\n{tool_instructions}"
        
        # System prompt
        if system_content:
            prompt_parts.append(f"System: {system_content}")
        
        # Conversation history
        for msg in session.messages[-10:]:  # Last 10 messages
            # Skip None messages
            if msg is None:
                continue
            if msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
        
        # New message
        prompt_parts.append(f"User: {new_message.content}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def _create_tool_prompt(
        self, 
        tool_name: str, 
        tool_parameters: Dict[str, Any],
        config: IAgentConfiguration
    ) -> str:
        """Create a structured prompt for tool calling"""
        # Get tool information
        try:
            from langswarm.tools.registry import ToolRegistry
            registry = ToolRegistry()
            
            if not registry._tools:
                registry.auto_populate_with_mcp_tools()
            
            tool_info = registry.get_tool(tool_name)
            if tool_info:
                tool_desc = getattr(tool_info.metadata, 'description', f"Tool: {tool_name}")
            else:
                tool_desc = f"Tool: {tool_name}"
                
        except Exception:
            tool_desc = f"Tool: {tool_name}"
        
        # Create structured prompt
        prompt = f"""You need to use the {tool_name} tool to help answer this request.

Tool: {tool_name}
Description: {tool_desc}
Parameters: {json.dumps(tool_parameters, indent=2)}

Please execute this tool and provide the results in a helpful response."""
        
        return prompt
    
    def _process_response(
        self, 
        response: str, 
        execution_time: float,
        config: IAgentConfiguration,
        original_message: AgentMessage
    ) -> AgentResponse:
        """Process model response"""
        try:
            # Estimate token usage (rough approximation)
            prompt_tokens = len(original_message.content.split()) * 1.3  # Rough token estimate
            completion_tokens = len(response.split()) * 1.3
            
            agent_message = AgentMessage(
                role="assistant",
                content=response.strip(),
                metadata={
                    "model": config.model,
                    "provider": "huggingface",
                    "inference_type": "remote" if config.base_url else "local"
                }
            )
            
            usage = AgentUsage(
                prompt_tokens=int(prompt_tokens),
                completion_tokens=int(completion_tokens),
                total_tokens=int(prompt_tokens + completion_tokens),
                model=config.model,
                cost_estimate=0.0  # Free for local models
            )
            
            return AgentResponse(
                message=agent_message,
                usage=usage,
                execution_time=execution_time,
                provider_response={"response": response}
            )
            
        except Exception as e:
            logger.error(f"Failed to process Hugging Face response: {e}")
            return AgentResponse.error_response(e)