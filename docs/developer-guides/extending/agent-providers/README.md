# Building Custom Agent Providers for LangSwarm V2

**Complete guide for developing new LLM provider integrations**

## 🎯 Overview

LangSwarm V2's modular agent system makes it easy to add support for new LLM providers. Each provider is a self-contained implementation that integrates natively with the provider's API while maintaining the consistent LangSwarm interface.

**Provider Examples:**
- **OpenAI**: GPT models with function calling and vision
- **Anthropic**: Claude models with enhanced reasoning
- **Gemini**: Google's multimodal capabilities
- **Custom**: Your own LLM or API integration

---

## 🏗️ Provider Architecture

### **Provider Interface**

Every provider must implement the `ProviderInterface`:

```python
from langswarm.core.agents.interfaces import ProviderInterface, AgentInterface
from typing import List, Dict, Any

class CustomProvider(ProviderInterface):
    """Custom LLM provider implementation"""
    
    provider_name: str = "custom"
    supported_models: List[str] = ["custom-model-1", "custom-model-2"]
    
    async def create_agent(self, model: str, config: Dict[str, Any]) -> AgentInterface:
        """Create an agent instance for this provider"""
        return CustomAgent(model=model, config=config)
    
    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate provider-specific configuration"""
        required_keys = ["api_key", "endpoint"]
        return all(key in config for key in required_keys)
    
    async def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information and capabilities"""
        return {
            "name": self.provider_name,
            "supported_models": self.supported_models,
            "capabilities": ["chat", "streaming"],
            "version": "1.0.0"
        }
```

### **Agent Implementation**

Each provider creates agents that implement `AgentInterface`:

```python
from langswarm.core.agents.interfaces import AgentInterface
from langswarm.core.errors import AgentError, ErrorContext
import httpx
import json

class CustomAgent(AgentInterface):
    """Custom provider agent implementation"""
    
    def __init__(self, model: str, config: Dict[str, Any]):
        self.agent_id = f"custom_{model}_{id(self)}"
        self.provider = "custom"
        self.model = model
        self.config = config
        self.client = httpx.AsyncClient()
        
        # Provider-specific initialization
        self.api_key = config.get("api_key")
        self.endpoint = config.get("endpoint")
        self.timeout = config.get("timeout", 30)
    
    async def configure(self, config: Dict[str, Any]) -> None:
        """Configure agent with provider-specific settings"""
        self.config.update(config)
        if "api_key" in config:
            self.api_key = config["api_key"]
    
    async def chat(self, message: str, **kwargs) -> str:
        """Send a message and get a response"""
        try:
            # Build request payload
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": message}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 1000)
            }
            
            # Make API request
            response = await self.client.post(
                f"{self.endpoint}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise AgentError(
                message=f"Custom provider chat failed: {str(e)}",
                context=ErrorContext("custom_agent", "chat"),
                suggestion="Check API key and endpoint configuration"
            )
    
    async def chat_stream(self, message: str, **kwargs) -> AsyncIterator[str]:
        """Send a message and get streaming response"""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": message}],
                "stream": True,
                **kwargs
            }
            
            async with self.client.stream(
                "POST",
                f"{self.endpoint}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            content = data["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            raise AgentError(
                message=f"Custom provider streaming failed: {str(e)}",
                context=ErrorContext("custom_agent", "chat_stream")
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health and connectivity"""
        try:
            start_time = time.time()
            
            # Simple health check request
            response = await self.client.get(
                f"{self.endpoint}/health",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return {
                    "status": "online",
                    "latency_ms": latency_ms,
                    "last_success": datetime.now().isoformat(),
                    "error_rate": 0.0
                }
            else:
                return {
                    "status": "degraded",
                    "latency_ms": latency_ms,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "offline",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and features"""
        return {
            "provider": self.provider,
            "model": self.model,
            "max_tokens": 4000,  # Provider-specific limit
            "streaming": True,
            "function_calling": False,  # If your provider supports it
            "vision": False,           # If your provider supports it
            "supported_formats": ["text"],
            "languages": ["en", "es", "fr"]  # If multilingual
        }
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics and cost information"""
        # Implementation depends on your provider's API
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_cost": 0.0,
            "avg_cost_per_request": 0.0
        }
```

---

## 🔧 Builder Integration

### **Extend AgentBuilder**

Add your provider to the builder pattern:

```python
from langswarm.core.agents.builder import AgentBuilder

# Extend AgentBuilder for your provider
class CustomAgentBuilder:
    def __init__(self, builder: AgentBuilder):
        self.builder = builder
        self.builder._provider = "custom"
        self.builder._provider_config = {}
    
    def model(self, model: str):
        """Set the model for this provider"""
        self.builder._model = model
        return self
    
    def api_key(self, api_key: str):
        """Set API key for custom provider"""
        self.builder._provider_config["api_key"] = api_key
        return self
    
    def endpoint(self, endpoint: str):
        """Set API endpoint for custom provider"""
        self.builder._provider_config["endpoint"] = endpoint
        return self
    
    def timeout(self, timeout: int):
        """Set request timeout"""
        self.builder._provider_config["timeout"] = timeout
        return self
    
    def custom_parameter(self, value: Any):
        """Provider-specific parameter"""
        self.builder._provider_config["custom_param"] = value
        return self
    
    def build(self) -> CustomAgent:
        """Build the custom agent"""
        provider = CustomProvider()
        return await provider.create_agent(
            model=self.builder._model,
            config=self.builder._provider_config
        )

# Add to AgentBuilder
def custom(self) -> CustomAgentBuilder:
    """Create custom provider builder"""
    return CustomAgentBuilder(self)

# Monkey patch for now (better: extend the class)
AgentBuilder.custom = custom
```

### **Usage with Builder**

```python
# Now users can create custom agents
agent = (AgentBuilder()
    .custom()
    .model("custom-model-1")
    .api_key("your-api-key")
    .endpoint("https://api.custom-provider.com")
    .timeout(30)
    .custom_parameter("special_value")
    .build())
```

---

## 🌐 Advanced Provider Features

### **Function Calling Support**

If your provider supports function calling:

```python
class CustomAgent(AgentInterface):
    async def chat_with_tools(self, message: str, tools: List[Dict], **kwargs) -> str:
        """Chat with function calling support"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": message}],
            "tools": tools,  # Provider-specific tool format
            "tool_choice": kwargs.get("tool_choice", "auto")
        }
        
        response = await self._make_request(payload)
        
        # Handle tool calls if present
        if "tool_calls" in response:
            return await self._handle_tool_calls(response["tool_calls"])
        else:
            return response["content"]
    
    async def _handle_tool_calls(self, tool_calls: List[Dict]) -> str:
        """Handle function calls from the provider"""
        # Execute tools and get responses
        tool_responses = []
        for tool_call in tool_calls:
            result = await self._execute_tool(tool_call)
            tool_responses.append(result)
        
        # Send tool responses back to provider
        return await self._continue_with_tool_results(tool_responses)
```

### **Vision/Multimodal Support**

For providers with vision capabilities:

```python
class CustomAgent(AgentInterface):
    async def chat_with_image(self, message: str, image_url: str, **kwargs) -> str:
        """Chat with image understanding"""
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }]
        }
        
        response = await self._make_request(payload)
        return response["content"]
    
    async def analyze_video(self, video_url: str, prompt: str, **kwargs) -> str:
        """Analyze video content (if provider supports it)"""
        # Provider-specific video analysis implementation
        pass
```

### **Custom Safety Controls**

```python
class CustomAgent(AgentInterface):
    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        
        # Custom safety configuration
        self.safety_level = config.get("safety_level", "medium")
        self.content_filters = config.get("content_filters", [])
    
    async def chat(self, message: str, **kwargs) -> str:
        """Chat with safety controls"""
        # Pre-process message for safety
        if not await self._safety_check(message):
            raise AgentError(
                message="Message violates safety guidelines",
                suggestion="Please rephrase your request"
            )
        
        response = await self._make_request(message, **kwargs)
        
        # Post-process response for safety
        safe_response = await self._filter_response(response)
        return safe_response
    
    async def _safety_check(self, message: str) -> bool:
        """Check message against safety guidelines"""
        # Implement provider-specific safety checks
        return True
    
    async def _filter_response(self, response: str) -> str:
        """Filter response content"""
        # Implement response filtering
        return response
```

---

## 🧪 Testing Your Provider

### **Unit Tests**

```python
import pytest
from unittest.mock import AsyncMock, patch
from langswarm.core.agents.testing import AgentTestCase

class TestCustomProvider(AgentTestCase):
    async def test_provider_creation(self):
        """Test provider can create agents"""
        provider = CustomProvider()
        
        config = {
            "api_key": "test-key",
            "endpoint": "https://api.test.com"
        }
        
        agent = await provider.create_agent("custom-model-1", config)
        
        assert agent.provider == "custom"
        assert agent.model == "custom-model-1"
    
    async def test_config_validation(self):
        """Test configuration validation"""
        provider = CustomProvider()
        
        # Valid config
        valid_config = {"api_key": "test", "endpoint": "https://api.test.com"}
        assert await provider.validate_config(valid_config) is True
        
        # Invalid config
        invalid_config = {"api_key": "test"}  # Missing endpoint
        assert await provider.validate_config(invalid_config) is False
    
    @patch('httpx.AsyncClient.post')
    async def test_chat(self, mock_post):
        """Test chat functionality"""
        # Mock API response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello from custom provider!"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Create agent and test
        agent = CustomAgent("custom-model-1", {
            "api_key": "test",
            "endpoint": "https://api.test.com"
        })
        
        response = await agent.chat("Hello")
        assert response == "Hello from custom provider!"
    
    async def test_health_check(self):
        """Test health check functionality"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            agent = CustomAgent("custom-model-1", {
                "api_key": "test",
                "endpoint": "https://api.test.com"
            })
            
            health = await agent.health_check()
            assert health["status"] == "online"
            assert "latency_ms" in health
```

### **Integration Tests**

```python
class TestCustomProviderIntegration:
    async def test_full_workflow(self):
        """Test complete provider workflow"""
        # Create agent using builder
        agent = (AgentBuilder()
            .custom()
            .model("custom-model-1")
            .api_key("real-test-key")
            .endpoint("https://api.custom-provider.com")
            .build())
        
        # Test health
        health = await agent.health_check()
        assert health["status"] in ["online", "degraded"]
        
        # Test capabilities
        capabilities = await agent.get_capabilities()
        assert "streaming" in capabilities
        
        # Test chat (if health is good)
        if health["status"] == "online":
            response = await agent.chat("Hello")
            assert isinstance(response, str)
            assert len(response) > 0
```

---

## 📊 Provider Registration

### **Register with LangSwarm**

```python
from langswarm.core.agents.registry import AgentRegistry

# Register your provider
registry = AgentRegistry()
registry.register_provider("custom", CustomProvider())

# Now available in builder
agent = AgentBuilder().custom().model("custom-model-1").build()
```

### **Auto-Discovery**

For automatic discovery, create a plugin:

```python
# custom_provider_plugin.py
from langswarm.core.agents.plugins import ProviderPlugin

class CustomProviderPlugin(ProviderPlugin):
    provider_name = "custom"
    provider_class = CustomProvider
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if provider dependencies are available"""
        try:
            import custom_provider_sdk
            return True
        except ImportError:
            return False
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "timeout": 30,
            "max_retries": 3
        }

# Register plugin
registry.register_plugin(CustomProviderPlugin)
```

---

## 🚀 Production Considerations

### **Error Handling**

```python
class CustomAgent(AgentInterface):
    async def chat(self, message: str, **kwargs) -> str:
        """Robust chat with comprehensive error handling"""
        try:
            return await self._chat_with_retries(message, **kwargs)
        except httpx.TimeoutException:
            raise AgentError(
                message="Request timed out",
                context=ErrorContext("custom_agent", "chat"),
                suggestion="Try reducing message length or increasing timeout"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AgentError(
                    message="Authentication failed",
                    suggestion="Check your API key configuration"
                )
            elif e.response.status_code == 429:
                raise AgentError(
                    message="Rate limit exceeded",
                    suggestion="Wait before retrying or upgrade your plan"
                )
            else:
                raise AgentError(f"HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise AgentError(f"Unexpected error: {str(e)}")
```

### **Performance Optimization**

```python
class CustomAgent(AgentInterface):
    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        
        # Connection pooling
        self.client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            timeout=httpx.Timeout(30.0)
        )
        
        # Response caching
        self.response_cache = {}
        self.cache_ttl = config.get("cache_ttl", 300)  # 5 minutes
    
    async def chat(self, message: str, **kwargs) -> str:
        """Chat with caching and optimization"""
        # Check cache first
        cache_key = self._get_cache_key(message, kwargs)
        if cache_key in self.response_cache:
            cached_response, timestamp = self.response_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_response
        
        # Make request
        response = await self._make_request(message, **kwargs)
        
        # Cache response
        self.response_cache[cache_key] = (response, time.time())
        
        return response
```

### **Monitoring Integration**

```python
class CustomAgent(AgentInterface):
    def __init__(self, model: str, config: Dict[str, Any]):
        super().__init__(model, config)
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0.0
        }
    
    async def chat(self, message: str, **kwargs) -> str:
        """Chat with metrics collection"""
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        try:
            response = await self._make_request(message, **kwargs)
            self.metrics["successful_requests"] += 1
            return response
        except Exception as e:
            self.metrics["failed_requests"] += 1
            raise
        finally:
            latency = time.time() - start_time
            self.metrics["total_latency"] += latency
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get detailed usage statistics"""
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0 else 0
        )
        
        success_rate = (
            self.metrics["successful_requests"] / self.metrics["total_requests"]
            if self.metrics["total_requests"] > 0 else 0
        )
        
        return {
            **self.metrics,
            "average_latency": avg_latency,
            "success_rate": success_rate,
            "error_rate": 1.0 - success_rate
        }
```

---

## 📚 Best Practices

### **Provider Development**
- Implement all required interface methods
- Follow LangSwarm error handling patterns
- Include comprehensive health checks
- Support both sync and async operations where possible

### **API Integration**
- Use connection pooling for performance
- Implement proper retry logic with exponential backoff
- Handle rate limiting gracefully
- Cache responses when appropriate

### **Error Handling**
- Provide specific, actionable error messages
- Use LangSwarm error types consistently
- Include context and suggestions in errors
- Log errors appropriately for debugging

### **Testing**
- Write comprehensive unit tests
- Include integration tests with real API
- Mock external dependencies properly
- Test error conditions and edge cases

### **Documentation**
- Document all provider-specific features
- Include usage examples
- Explain configuration options
- Provide troubleshooting guidance

---

**Building custom providers extends LangSwarm's capabilities while maintaining the consistent, powerful interface that makes multi-provider applications possible.**
