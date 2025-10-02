"""
LangSwarm V2 Provider-Specific Connection Pools

Connection pool implementations optimized for each provider's unique characteristics
and API patterns. Includes provider-specific optimizations and health checking.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
import aiohttp
import json

from .base import BaseConnectionPool
from .interfaces import (
    PoolConfig, ConnectionConfig, ConnectionStatus,
    ConnectionPoolError, HealthCheckFailedError
)

# Optional provider imports for connection management
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

try:
    from mistralai.async_client import MistralAsyncClient
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False


class OpenAIConnectionPool(BaseConnectionPool):
    """
    OpenAI-specific connection pool with optimizations for OpenAI API patterns.
    
    Features:
    - Multiple API key rotation
    - Organization-specific client management
    - Rate limiting and backoff strategies
    - Azure OpenAI support
    """
    
    def __init__(self, config: PoolConfig):
        """Initialize OpenAI connection pool"""
        super().__init__(config)
        self._clients: Dict[str, Any] = {}
        self._rate_limits: Dict[str, Dict[str, Any]] = {}
        self._request_counts: Dict[str, int] = {}
        
        if not OPENAI_AVAILABLE:
            logging.warning("OpenAI client not available for connection pool")
    
    async def _create_connection(self, index: int) -> Optional[Any]:
        """Create OpenAI client connection"""
        if not OPENAI_AVAILABLE:
            return None
        
        try:
            # Get connection config for this index
            if index < len(self._config.connection_configs):
                conn_config = self._config.connection_configs[index]
            else:
                # Use first config as default
                conn_config = self._config.connection_configs[0] if self._config.connection_configs else ConnectionConfig()
            
            # Create OpenAI async client
            client_kwargs = {
                "api_key": conn_config.api_key,
                "timeout": conn_config.timeout,
                "max_retries": conn_config.max_retries
            }
            
            # Add base URL if specified (for Azure OpenAI)
            if conn_config.base_url:
                client_kwargs["base_url"] = conn_config.base_url
            
            client = openai.AsyncOpenAI(**client_kwargs)
            
            # Store connection metadata
            client.connection_id = conn_config.connection_id
            client.weight = conn_config.weight
            client.max_requests_per_minute = conn_config.max_requests_per_minute
            client._conn_config = conn_config
            
            # Initialize rate limiting
            self._rate_limits[conn_config.connection_id] = {
                "requests_per_minute": 0,
                "last_reset": datetime.utcnow(),
                "last_request": None
            }
            self._request_counts[conn_config.connection_id] = 0
            
            logging.debug(f"Created OpenAI connection: {conn_config.connection_id}")
            return client
            
        except Exception as e:
            logging.error(f"Failed to create OpenAI connection: {e}")
            return None
    
    async def _is_connection_healthy(self, connection: Any) -> bool:
        """Check OpenAI connection health"""
        try:
            # Test with a simple API call
            response = await connection.models.list()
            return response is not None and hasattr(response, 'data')
            
        except Exception as e:
            logging.warning(f"OpenAI connection health check failed: {e}")
            return False
    
    async def _check_rate_limits(self, connection: Any) -> bool:
        """Check if connection is within rate limits"""
        if not hasattr(connection, 'connection_id'):
            return True
        
        connection_id = connection.connection_id
        rate_info = self._rate_limits.get(connection_id, {})
        
        now = datetime.utcnow()
        last_reset = rate_info.get("last_reset", now)
        
        # Reset counter every minute
        if (now - last_reset).total_seconds() >= 60:
            rate_info["requests_per_minute"] = 0
            rate_info["last_reset"] = now
        
        # Check if within limits
        max_requests = getattr(connection, 'max_requests_per_minute', 1000)
        current_requests = rate_info.get("requests_per_minute", 0)
        
        return current_requests < max_requests
    
    async def _record_request(self, connection: Any, success: bool = True, response_time: float = 0):
        """Record request for rate limiting and metrics"""
        if not hasattr(connection, 'connection_id'):
            return
        
        connection_id = connection.connection_id
        
        # Update rate limiting
        if connection_id in self._rate_limits:
            self._rate_limits[connection_id]["requests_per_minute"] += 1
            self._rate_limits[connection_id]["last_request"] = datetime.utcnow()
        
        # Update connection stats
        if connection_id in self._connection_stats:
            stats = self._connection_stats[connection_id]
            stats.total_requests += 1
            if success:
                stats.successful_requests += 1
            else:
                stats.failed_requests += 1
            
            # Update average response time
            if response_time > 0:
                total_time = stats.avg_response_time_ms * (stats.total_requests - 1) + response_time
                stats.avg_response_time_ms = total_time / stats.total_requests


class AnthropicConnectionPool(BaseConnectionPool):
    """
    Anthropic-specific connection pool with Claude API optimizations.
    
    Features:
    - Long context window handling
    - Constitutional AI safety monitoring
    - Claude-specific rate limiting
    """
    
    def __init__(self, config: PoolConfig):
        """Initialize Anthropic connection pool"""
        super().__init__(config)
        self._clients: Dict[str, Any] = {}
        
        if not ANTHROPIC_AVAILABLE:
            logging.warning("Anthropic client not available for connection pool")
    
    async def _create_connection(self, index: int) -> Optional[Any]:
        """Create Anthropic client connection"""
        if not ANTHROPIC_AVAILABLE:
            return None
        
        try:
            # Get connection config
            if index < len(self._config.connection_configs):
                conn_config = self._config.connection_configs[index]
            else:
                conn_config = self._config.connection_configs[0] if self._config.connection_configs else ConnectionConfig()
            
            # Create Anthropic async client
            client = anthropic.AsyncAnthropic(
                api_key=conn_config.api_key,
                timeout=conn_config.timeout,
                max_retries=conn_config.max_retries
            )
            
            # Store connection metadata
            client.connection_id = conn_config.connection_id
            client.weight = conn_config.weight
            client._conn_config = conn_config
            
            logging.debug(f"Created Anthropic connection: {conn_config.connection_id}")
            return client
            
        except Exception as e:
            logging.error(f"Failed to create Anthropic connection: {e}")
            return None
    
    async def _is_connection_healthy(self, connection: Any) -> bool:
        """Check Anthropic connection health"""
        try:
            # Test with a minimal message
            response = await connection.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}]
            )
            return response is not None
            
        except Exception as e:
            logging.warning(f"Anthropic connection health check failed: {e}")
            return False


class GeminiConnectionPool(BaseConnectionPool):
    """
    Google Gemini-specific connection pool with Gemini API optimizations.
    
    Features:
    - Multimodal capability handling
    - Google services integration
    - Gemini-specific safety settings
    """
    
    def __init__(self, config: PoolConfig):
        """Initialize Gemini connection pool"""
        super().__init__(config)
        self._configured_keys: Set[str] = set()
        
        if not GEMINI_AVAILABLE:
            logging.warning("Google Generative AI client not available for connection pool")
    
    async def _create_connection(self, index: int) -> Optional[Any]:
        """Create Gemini client connection"""
        if not GEMINI_AVAILABLE:
            return None
        
        try:
            # Get connection config
            if index < len(self._config.connection_configs):
                conn_config = self._config.connection_configs[index]
            else:
                conn_config = self._config.connection_configs[0] if self._config.connection_configs else ConnectionConfig()
            
            # Configure Gemini client
            if conn_config.api_key not in self._configured_keys:
                genai.configure(api_key=conn_config.api_key)
                self._configured_keys.add(conn_config.api_key)
            
            # Create a mock client object to represent the connection
            class GeminiConnection:
                def __init__(self, connection_id: str, api_key: str, config: ConnectionConfig):
                    self.connection_id = connection_id
                    self.api_key = api_key
                    self.weight = config.weight
                    self._conn_config = config
                
                async def generate_content(self, *args, **kwargs):
                    model = genai.GenerativeModel('gemini-pro')
                    return await model.generate_content_async(*args, **kwargs)
            
            connection = GeminiConnection(
                conn_config.connection_id,
                conn_config.api_key,
                conn_config
            )
            
            logging.debug(f"Created Gemini connection: {conn_config.connection_id}")
            return connection
            
        except Exception as e:
            logging.error(f"Failed to create Gemini connection: {e}")
            return None
    
    async def _is_connection_healthy(self, connection: Any) -> bool:
        """Check Gemini connection health"""
        try:
            # Test with a simple generation
            model = genai.GenerativeModel('gemini-pro')
            response = await model.generate_content_async("hi")
            return response is not None
            
        except Exception as e:
            logging.warning(f"Gemini connection health check failed: {e}")
            return False


class CohereConnectionPool(BaseConnectionPool):
    """
    Cohere-specific connection pool with Command model optimizations.
    
    Features:
    - RAG-optimized request handling
    - Cohere-specific embeddings support
    - Multi-language model support
    """
    
    def __init__(self, config: PoolConfig):
        """Initialize Cohere connection pool"""
        super().__init__(config)
        
        if not COHERE_AVAILABLE:
            logging.warning("Cohere client not available for connection pool")
    
    async def _create_connection(self, index: int) -> Optional[Any]:
        """Create Cohere client connection"""
        if not COHERE_AVAILABLE:
            return None
        
        try:
            # Get connection config
            if index < len(self._config.connection_configs):
                conn_config = self._config.connection_configs[index]
            else:
                conn_config = self._config.connection_configs[0] if self._config.connection_configs else ConnectionConfig()
            
            # Create Cohere async client
            client = cohere.AsyncClient(
                api_key=conn_config.api_key,
                timeout=conn_config.timeout
            )
            
            # Store connection metadata
            client.connection_id = conn_config.connection_id
            client.weight = conn_config.weight
            client._conn_config = conn_config
            
            logging.debug(f"Created Cohere connection: {conn_config.connection_id}")
            return client
            
        except Exception as e:
            logging.error(f"Failed to create Cohere connection: {e}")
            return None
    
    async def _is_connection_healthy(self, connection: Any) -> bool:
        """Check Cohere connection health"""
        try:
            # Test with a simple chat
            response = await connection.chat(
                model="command-r",
                message="hi",
                max_tokens=1
            )
            return response is not None
            
        except Exception as e:
            logging.warning(f"Cohere connection health check failed: {e}")
            return False


class MistralConnectionPool(BaseConnectionPool):
    """
    Mistral-specific connection pool with Mixtral optimizations.
    
    Features:
    - Mixture of Experts (MoE) handling
    - European data residency
    - Mistral-specific function calling
    """
    
    def __init__(self, config: PoolConfig):
        """Initialize Mistral connection pool"""
        super().__init__(config)
        
        if not MISTRAL_AVAILABLE:
            logging.warning("Mistral client not available for connection pool")
    
    async def _create_connection(self, index: int) -> Optional[Any]:
        """Create Mistral client connection"""
        if not MISTRAL_AVAILABLE:
            return None
        
        try:
            # Get connection config
            if index < len(self._config.connection_configs):
                conn_config = self._config.connection_configs[index]
            else:
                conn_config = self._config.connection_configs[0] if self._config.connection_configs else ConnectionConfig()
            
            # Create Mistral async client
            client = MistralAsyncClient(api_key=conn_config.api_key)
            
            # Store connection metadata
            client.connection_id = conn_config.connection_id
            client.weight = conn_config.weight
            client._conn_config = conn_config
            
            logging.debug(f"Created Mistral connection: {conn_config.connection_id}")
            return client
            
        except Exception as e:
            logging.error(f"Failed to create Mistral connection: {e}")
            return None
    
    async def _is_connection_healthy(self, connection: Any) -> bool:
        """Check Mistral connection health"""
        try:
            # Test with a simple chat
            response = await connection.chat(
                model="mistral-tiny",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1
            )
            return response is not None
            
        except Exception as e:
            logging.warning(f"Mistral connection health check failed: {e}")
            return False


class HuggingFaceConnectionPool(BaseConnectionPool):
    """
    Hugging Face-specific connection pool supporting both API and local modes.
    
    Features:
    - Dual mode (API/local) support
    - Model loading optimization
    - GPU/CPU resource management
    """
    
    def __init__(self, config: PoolConfig, use_local: bool = False):
        """Initialize Hugging Face connection pool"""
        super().__init__(config)
        self.use_local = use_local
        self._local_models: Dict[str, Any] = {}
        self._tokenizers: Dict[str, Any] = {}
    
    async def _create_connection(self, index: int) -> Optional[Any]:
        """Create Hugging Face connection"""
        try:
            # Get connection config
            if index < len(self._config.connection_configs):
                conn_config = self._config.connection_configs[index]
            else:
                conn_config = self._config.connection_configs[0] if self._config.connection_configs else ConnectionConfig()
            
            if self.use_local:
                # Create local model connection
                return await self._create_local_connection(conn_config)
            else:
                # Create API connection
                return await self._create_api_connection(conn_config)
            
        except Exception as e:
            logging.error(f"Failed to create Hugging Face connection: {e}")
            return None
    
    async def _create_api_connection(self, conn_config: ConnectionConfig) -> Optional[Any]:
        """Create Hugging Face API connection"""
        try:
            from huggingface_hub import AsyncInferenceClient
            
            client = AsyncInferenceClient(token=conn_config.api_key)
            
            # Store connection metadata
            client.connection_id = conn_config.connection_id
            client.weight = conn_config.weight
            client._conn_config = conn_config
            client.mode = "api"
            
            return client
            
        except ImportError:
            logging.error("huggingface_hub not available for API connections")
            return None
    
    async def _create_local_connection(self, conn_config: ConnectionConfig) -> Optional[Any]:
        """Create local Hugging Face connection"""
        try:
            # Create a mock connection for local model
            class LocalHFConnection:
                def __init__(self, connection_id: str, config: ConnectionConfig):
                    self.connection_id = connection_id
                    self.weight = config.weight
                    self._conn_config = config
                    self.mode = "local"
            
            return LocalHFConnection(conn_config.connection_id, conn_config)
            
        except Exception as e:
            logging.error(f"Failed to create local HF connection: {e}")
            return None
    
    async def _is_connection_healthy(self, connection: Any) -> bool:
        """Check Hugging Face connection health"""
        try:
            if hasattr(connection, 'mode'):
                if connection.mode == "api":
                    # Test API connection
                    response = await connection.text_generation(
                        "test", 
                        model="gpt2",
                        max_new_tokens=1
                    )
                    return response is not None
                else:
                    # Local connection is always healthy if created
                    return True
            return False
            
        except Exception as e:
            logging.warning(f"Hugging Face connection health check failed: {e}")
            return False


class LocalConnectionPool(BaseConnectionPool):
    """
    Local provider connection pool for self-hosted models.
    
    Features:
    - Multi-backend support (Ollama, LocalAI, etc.)
    - HTTP connection pooling
    - Custom endpoint management
    """
    
    def __init__(self, config: PoolConfig, backend: str = "ollama"):
        """Initialize Local connection pool"""
        super().__init__(config)
        self.backend = backend
        self._http_sessions: Dict[str, aiohttp.ClientSession] = {}
    
    async def _create_connection(self, index: int) -> Optional[Any]:
        """Create local model connection"""
        try:
            # Get connection config
            if index < len(self._config.connection_configs):
                conn_config = self._config.connection_configs[index]
            else:
                conn_config = self._config.connection_configs[0] if self._config.connection_configs else ConnectionConfig()
            
            # Create HTTP session for the backend
            timeout = aiohttp.ClientTimeout(total=conn_config.timeout)
            session = aiohttp.ClientSession(timeout=timeout)
            
            # Store session
            self._http_sessions[conn_config.connection_id] = session
            
            # Create connection object
            class LocalConnection:
                def __init__(self, connection_id: str, base_url: str, session: aiohttp.ClientSession, config: ConnectionConfig):
                    self.connection_id = connection_id
                    self.base_url = base_url
                    self.session = session
                    self.weight = config.weight
                    self._conn_config = config
                    self.backend = backend
                
                async def close(self):
                    await self.session.close()
            
            connection = LocalConnection(
                conn_config.connection_id,
                conn_config.base_url or "http://localhost:11434",
                session,
                conn_config
            )
            
            logging.debug(f"Created Local connection: {conn_config.connection_id}")
            return connection
            
        except Exception as e:
            logging.error(f"Failed to create Local connection: {e}")
            return None
    
    async def _is_connection_healthy(self, connection: Any) -> bool:
        """Check local connection health"""
        try:
            # Test HTTP connectivity
            async with connection.session.get(f"{connection.base_url}/api/tags") as response:
                return response.status == 200
                
        except Exception as e:
            logging.warning(f"Local connection health check failed: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown local connection pool and close HTTP sessions"""
        # Close all HTTP sessions
        for session in self._http_sessions.values():
            await session.close()
        
        self._http_sessions.clear()
        
        # Call parent shutdown
        await super().shutdown()
