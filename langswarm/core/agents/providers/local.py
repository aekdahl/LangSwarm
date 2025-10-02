"""
LangSwarm V2 Local Provider

Native Local provider implementation for V2 agents with support for
self-hosted models using Ollama, LocalAI, OpenAI-compatible APIs, and custom endpoints.
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime

from ..interfaces import (
    IAgentProvider, IAgentSession, AgentMessage, IAgentResponse, 
    AgentUsage, IAgentConfiguration, ProviderType, AgentCapability
)
from ..base import BaseAgent


class LocalProvider(IAgentProvider):
    """
    Native Local provider for V2 agents.
    
    Supports self-hosted models through various backends:
    - Ollama (https://ollama.ai/)
    - LocalAI (https://localai.io/)
    - OpenAI-compatible APIs
    - Custom HTTP APIs
    - Text Generation Inference (TGI)
    - vLLM servers
    """
    
    def __init__(self, backend: str = "ollama", base_url: str = None):
        """
        Initialize Local provider
        
        Args:
            backend: Backend type (ollama, localai, openai-compatible, custom)
            base_url: Base URL for the local API
        """
        self.backend = backend.lower()
        self.base_url = base_url or self._get_default_url(self.backend)
        self._sessions: Dict[str, 'LocalSession'] = {}
        self._client_session: Optional[aiohttp.ClientSession] = None
        
        # Validate backend
        supported_backends = ["ollama", "localai", "openai-compatible", "custom", "tgi", "vllm"]
        if self.backend not in supported_backends:
            raise ValueError(f"Unsupported backend: {self.backend}. Supported: {supported_backends}")
    
    def _get_default_url(self, backend: str) -> str:
        """Get default URL for different backends"""
        defaults = {
            "ollama": "http://localhost:11434",
            "localai": "http://localhost:8080",
            "openai-compatible": "http://localhost:8000",
            "custom": "http://localhost:8000",
            "tgi": "http://localhost:8080",
            "vllm": "http://localhost:8000"
        }
        return defaults.get(backend, "http://localhost:8000")
    
    def supported_models(self) -> List[str]:
        """Get list of supported local models by backend"""
        models = {
            "ollama": [
                # Popular Ollama models
                "llama2", "llama2:7b", "llama2:13b", "llama2:70b",
                "llama2-uncensored", "llama2-uncensored:7b", "llama2-uncensored:70b",
                "codellama", "codellama:7b", "codellama:13b", "codellama:34b",
                "mistral", "mistral:7b", "mistral:latest",
                "mixtral", "mixtral:8x7b",
                "neural-chat", "neural-chat:7b",
                "starcode", "starcode:7b", "starcode:15b",
                "vicuna", "vicuna:7b", "vicuna:13b",
                "orca-mini", "orca-mini:3b", "orca-mini:7b", "orca-mini:13b",
                "dolphin-phi", "dolphin-phi:2.7b",
                "phi", "phi:2.7b",
                "tinyllama", "tinyllama:1.1b",
                "falcon", "falcon:7b", "falcon:40b",
                "wizard-vicuna-uncensored", "wizard-vicuna-uncensored:13b",
                "nous-hermes", "nous-hermes:7b", "nous-hermes:13b",
                "zephyr", "zephyr:7b-beta"
            ],
            "localai": [
                # LocalAI model templates
                "gpt-3.5-turbo", "gpt-4", "text-davinci-003",
                "llama2-chat", "codellama-instruct", "mistral-instruct",
                "vicuna-chat", "alpaca", "stablelm-tuned"
            ],
            "openai-compatible": [
                # OpenAI-compatible servers often use standard names
                "gpt-3.5-turbo", "gpt-4", "text-davinci-003",
                "llama-2-7b-chat", "llama-2-13b-chat", "llama-2-70b-chat",
                "codellama-7b-instruct", "mistral-7b-instruct"
            ],
            "tgi": [
                # Text Generation Inference models
                "microsoft/DialoGPT-medium", "microsoft/DialoGPT-large",
                "meta-llama/Llama-2-7b-chat-hf", "meta-llama/Llama-2-13b-chat-hf",
                "mistralai/Mistral-7B-Instruct-v0.1", "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "HuggingFaceH4/zephyr-7b-beta", "teknium/OpenHermes-2.5-Mistral-7B"
            ],
            "vllm": [
                # vLLM supported models
                "meta-llama/Llama-2-7b-chat-hf", "meta-llama/Llama-2-13b-chat-hf",
                "mistralai/Mistral-7B-Instruct-v0.1", "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "HuggingFaceH4/zephyr-7b-beta", "teknium/OpenHermes-2.5-Mistral-7B",
                "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"
            ]
        }
        
        return models.get(self.backend, ["custom-model"])
    
    def supported_capabilities(self) -> List[AgentCapability]:
        """Get list of supported capabilities"""
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.CONVERSATION,
            AgentCapability.STREAMING,
            AgentCapability.OFFLINE_OPERATION,
            AgentCapability.CUSTOM_MODELS,
            AgentCapability.CODE_GENERATION,
            AgentCapability.LOCAL_DEPLOYMENT
        ]
    
    def validate_configuration(self, config: IAgentConfiguration) -> Dict[str, Any]:
        """Validate Local provider configuration"""
        issues = []
        warnings = []
        
        # Check model availability
        if config.model not in self.supported_models():
            warnings.append(f"Model '{config.model}' not in known {self.backend} models")
        
        # Check temperature range
        if config.temperature is not None and (config.temperature < 0 or config.temperature > 2):
            warnings.append("Temperature outside typical range (0-2) for local models")
        
        # Check max tokens
        if config.max_tokens is not None and config.max_tokens > 8192:
            warnings.append("Max tokens > 8192 may not be supported by all local models")
        
        # Backend-specific validations
        if self.backend == "ollama":
            if ":" not in config.model and config.model not in ["llama2", "mistral", "codellama"]:
                warnings.append("Ollama models typically include tag (e.g., 'llama2:7b')")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    async def create_session(self, config: IAgentConfiguration) -> IAgentSession:
        """Create new Local agent session"""
        # Initialize HTTP client session if needed
        if not self._client_session:
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for local models
            self._client_session = aiohttp.ClientSession(timeout=timeout)
        
        session = LocalSession(self, config)
        self._sessions[session.session_id] = session
        return session
    
    async def send_message(self, session: IAgentSession, messages: List[AgentMessage], 
                          tools: Optional[List[Dict[str, Any]]] = None,
                          **kwargs) -> IAgentResponse:
        """Send message to local model"""
        if not isinstance(session, LocalSession):
            raise ValueError("Session must be LocalSession for Local provider")
        
        return await session.send_message(messages, tools, **kwargs)
    
    async def stream_message(self, session: IAgentSession, messages: List[AgentMessage],
                           tools: Optional[List[Dict[str, Any]]] = None,
                           **kwargs) -> AsyncGenerator[str, None]:
        """Stream message response from local model"""
        if not isinstance(session, LocalSession):
            raise ValueError("Session must be LocalSession for Local provider")
        
        async for chunk in session.stream_message(messages, tools, **kwargs):
            yield chunk
    
    async def call_tool(self, session: IAgentSession, tool_name: str, 
                       parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool call through local model"""
        return {
            "tool_name": tool_name,
            "parameters": parameters,
            "result": "Tool execution support depends on local model capabilities",
            "provider": "local",
            "backend": self.backend
        }
    
    def _format_messages_for_backend(self, messages: List[AgentMessage]) -> Any:
        """Format messages according to backend requirements"""
        if self.backend == "ollama":
            return self._format_ollama_messages(messages)
        elif self.backend == "localai":
            return self._format_localai_messages(messages)
        elif self.backend in ["openai-compatible", "vllm"]:
            return self._format_openai_messages(messages)
        elif self.backend == "tgi":
            return self._format_tgi_messages(messages)
        else:
            return self._format_generic_messages(messages)
    
    def _format_ollama_messages(self, messages: List[AgentMessage]) -> Dict[str, Any]:
        """Format messages for Ollama API"""
        # Ollama uses a simple prompt format for most models
        prompt = ""
        for msg in messages:
            if msg.role == "system":
                prompt += f"System: {msg.content}\n\n"
            elif msg.role == "user":
                prompt += f"User: {msg.content}\n\n"
            elif msg.role == "assistant":
                prompt += f"Assistant: {msg.content}\n\n"
        
        return {"prompt": prompt.strip()}
    
    def _format_localai_messages(self, messages: List[AgentMessage]) -> Dict[str, Any]:
        """Format messages for LocalAI (OpenAI-compatible)"""
        return {
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
        }
    
    def _format_openai_messages(self, messages: List[AgentMessage]) -> Dict[str, Any]:
        """Format messages for OpenAI-compatible APIs"""
        return {
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
        }
    
    def _format_tgi_messages(self, messages: List[AgentMessage]) -> Dict[str, Any]:
        """Format messages for Text Generation Inference"""
        # TGI typically expects a single input string
        prompt = ""
        for msg in messages:
            if msg.role == "system":
                prompt += f"<|system|>\n{msg.content}\n"
            elif msg.role == "user":
                prompt += f"<|user|>\n{msg.content}\n"
            elif msg.role == "assistant":
                prompt += f"<|assistant|>\n{msg.content}\n"
        
        return {"inputs": prompt + "<|assistant|>\n"}
    
    def _format_generic_messages(self, messages: List[AgentMessage]) -> Dict[str, Any]:
        """Generic message format for custom APIs"""
        return {
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
        }
    
    def _get_api_endpoint(self, stream: bool = False) -> str:
        """Get appropriate API endpoint for the backend"""
        endpoints = {
            "ollama": "/api/generate" if not stream else "/api/generate",
            "localai": "/v1/chat/completions",
            "openai-compatible": "/v1/chat/completions",
            "tgi": "/generate" if not stream else "/generate_stream",
            "vllm": "/v1/chat/completions",
            "custom": "/generate"
        }
        
        return endpoints.get(self.backend, "/generate")
    
    async def get_health(self) -> Dict[str, Any]:
        """Get Local provider health status"""
        try:
            if not self._client_session:
                timeout = aiohttp.ClientTimeout(total=30)
                self._client_session = aiohttp.ClientSession(timeout=timeout)
            
            # Try to connect to the local server
            health_endpoints = {
                "ollama": "/api/tags",
                "localai": "/v1/models",
                "openai-compatible": "/v1/models",
                "tgi": "/info",
                "vllm": "/v1/models",
                "custom": "/"
            }
            
            endpoint = health_endpoints.get(self.backend, "/")
            url = f"{self.base_url}{endpoint}"
            
            try:
                async with self._client_session.get(url) as response:
                    if response.status == 200:
                        data = await response.json() if response.content_type == "application/json" else {}
                        
                        return {
                            "status": "healthy",
                            "backend": self.backend,
                            "base_url": self.base_url,
                            "response_status": response.status,
                            "server_info": data,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "backend": self.backend,
                            "base_url": self.base_url,
                            "response_status": response.status,
                            "error": f"Server returned status {response.status}",
                            "timestamp": datetime.utcnow().isoformat()
                        }
            except aiohttp.ClientError as e:
                return {
                    "status": "connection_error",
                    "backend": self.backend,
                    "base_url": self.base_url,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "backend": self.backend,
                "base_url": self.base_url,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close provider resources"""
        if self._client_session:
            await self._client_session.close()
            self._client_session = None


class LocalSession(IAgentSession):
    """Local provider agent session implementation"""
    
    def __init__(self, provider: LocalProvider, config: IAgentConfiguration):
        """Initialize Local session"""
        self.provider = provider
        self.config = config
        self.session_id = f"local_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.message_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0  # Local models typically have no cost
        self.conversation_history: List[AgentMessage] = []
    
    async def send_message(self, messages: List[AgentMessage], 
                          tools: Optional[List[Dict[str, Any]]] = None,
                          **kwargs) -> IAgentResponse:
        """Send message to local model"""
        try:
            self.last_activity = datetime.utcnow()
            
            # Format messages for the specific backend
            formatted_data = self.provider._format_messages_for_backend(messages)
            
            # Add model and parameters
            if self.provider.backend == "ollama":
                formatted_data.update({
                    "model": self.config.model,
                    "stream": False,
                    "options": {
                        "temperature": self.config.temperature or 0.7,
                        "num_predict": self.config.max_tokens or 512,
                        "top_p": self.config.top_p or 0.9
                    }
                })
            else:
                # OpenAI-compatible format
                formatted_data.update({
                    "model": self.config.model,
                    "temperature": self.config.temperature or 0.7,
                    "max_tokens": self.config.max_tokens or 512,
                    "top_p": self.config.top_p or 0.9,
                    "stream": False
                })
            
            # Get API endpoint
            endpoint = self.provider._get_api_endpoint(stream=False)
            url = f"{self.provider.base_url}{endpoint}"
            
            # Make API request
            async with self.provider._client_session.post(url, json=formatted_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Parse response based on backend
                    content, usage_info = self._parse_response(result)
                    
                    # Update session statistics
                    self.message_count += 1
                    self.total_tokens += usage_info.get("total_tokens", 0)
                    
                    # Create usage object
                    usage = AgentUsage(
                        input_tokens=usage_info.get("input_tokens", 0),
                        output_tokens=usage_info.get("output_tokens", 0),
                        total_tokens=usage_info.get("total_tokens", 0),
                        estimated_cost=0.0  # Local models have no API cost
                    )
                    
                    # Create response
                    return IAgentResponse(
                        content=content,
                        usage=usage,
                        finish_reason=usage_info.get("finish_reason", "stop"),
                        tool_calls=[],
                        metadata={
                            "model": self.config.model,
                            "provider": "local",
                            "backend": self.provider.backend,
                            "session_id": self.session_id,
                            "message_count": self.message_count,
                            "base_url": self.provider.base_url
                        }
                    )
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed with status {response.status}: {error_text}")
            
        except Exception as e:
            logging.error(f"Local model API error: {e}")
            return IAgentResponse(
                content=f"Error: {str(e)}",
                usage=AgentUsage(0, 0, 0, 0.0),
                finish_reason="error",
                tool_calls=[],
                metadata={
                    "error": str(e),
                    "provider": "local",
                    "backend": self.provider.backend,
                    "session_id": self.session_id
                }
            )
    
    def _parse_response(self, result: Dict[str, Any]) -> tuple:
        """Parse response based on backend format"""
        if self.provider.backend == "ollama":
            content = result.get("response", "")
            usage_info = {
                "input_tokens": result.get("prompt_eval_count", 0),
                "output_tokens": result.get("eval_count", 0),
                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                "finish_reason": "stop" if result.get("done", False) else "length"
            }
        elif self.provider.backend == "tgi":
            content = result.get("generated_text", "")
            usage_info = {
                "input_tokens": result.get("details", {}).get("prefill", [{}])[0].get("tokens", 0),
                "output_tokens": len(result.get("details", {}).get("tokens", [])),
                "total_tokens": 0,
                "finish_reason": result.get("details", {}).get("finish_reason", "stop")
            }
            usage_info["total_tokens"] = usage_info["input_tokens"] + usage_info["output_tokens"]
        else:
            # OpenAI-compatible format
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                content = choice.get("message", {}).get("content", "")
                finish_reason = choice.get("finish_reason", "stop")
            else:
                content = str(result)
                finish_reason = "stop"
            
            usage_data = result.get("usage", {})
            usage_info = {
                "input_tokens": usage_data.get("prompt_tokens", 0),
                "output_tokens": usage_data.get("completion_tokens", 0),
                "total_tokens": usage_data.get("total_tokens", 0),
                "finish_reason": finish_reason
            }
        
        return content, usage_info
    
    async def stream_message(self, messages: List[AgentMessage],
                           tools: Optional[List[Dict[str, Any]]] = None,
                           **kwargs) -> AsyncGenerator[str, None]:
        """Stream message response from local model"""
        try:
            self.last_activity = datetime.utcnow()
            
            # Format messages for the specific backend
            formatted_data = self.provider._format_messages_for_backend(messages)
            
            # Add model and parameters with streaming enabled
            if self.provider.backend == "ollama":
                formatted_data.update({
                    "model": self.config.model,
                    "stream": True,
                    "options": {
                        "temperature": self.config.temperature or 0.7,
                        "num_predict": self.config.max_tokens or 512,
                        "top_p": self.config.top_p or 0.9
                    }
                })
            else:
                # OpenAI-compatible format
                formatted_data.update({
                    "model": self.config.model,
                    "temperature": self.config.temperature or 0.7,
                    "max_tokens": self.config.max_tokens or 512,
                    "top_p": self.config.top_p or 0.9,
                    "stream": True
                })
            
            # Get API endpoint
            endpoint = self.provider._get_api_endpoint(stream=True)
            url = f"{self.provider.base_url}{endpoint}"
            
            # Stream the response
            async with self.provider._client_session.post(url, json=formatted_data) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            try:
                                if line.startswith("data: "):
                                    line = line[6:]
                                
                                if line == "[DONE]":
                                    break
                                
                                chunk_data = json.loads(line)
                                content = self._extract_stream_content(chunk_data)
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    yield f"Error: API request failed with status {response.status}: {error_text}"
            
            # Update session statistics
            self.message_count += 1
            
        except Exception as e:
            logging.error(f"Local model streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def _extract_stream_content(self, chunk_data: Dict[str, Any]) -> Optional[str]:
        """Extract content from streaming chunk based on backend"""
        if self.provider.backend == "ollama":
            return chunk_data.get("response", "")
        elif self.provider.backend == "tgi":
            return chunk_data.get("token", {}).get("text", "")
        else:
            # OpenAI-compatible format
            if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                delta = chunk_data["choices"][0].get("delta", {})
                return delta.get("content", "")
        
        return None
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "provider": "local",
            "backend": self.provider.backend,
            "model": self.config.model,
            "base_url": self.provider.base_url,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "conversation_length": len(self.conversation_history)
        }


class LocalAgent(BaseAgent):
    """Local provider-specific agent implementation"""
    
    def __init__(self, config: IAgentConfiguration, backend: str = "ollama", base_url: str = None):
        """Initialize Local agent"""
        provider = LocalProvider(backend=backend, base_url=base_url)
        super().__init__(config, provider)
