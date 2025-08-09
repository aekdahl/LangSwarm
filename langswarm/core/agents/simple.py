"""
Simplified Agent Architecture for LangSwarm

This module provides a simplified agent system that replaces the complex 
5-mixin inheritance pattern with a clean composition-based approach.

Key benefits:
- Single configuration object instead of 15+ constructor parameters
- Composition instead of multiple inheritance  
- Focused responsibilities with clear separation of concerns
- Clean, intuitive API for common use cases
- Backward compatibility with existing agents
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

# Import necessary components for composition
from langswarm.core.base.log import GlobalLogger
from langswarm.memory.adapters.database_adapter import DatabaseAdapter


@dataclass
class AgentConfig:
    """
    Simplified agent configuration object.
    
    Replaces 15+ constructor parameters with a single, clear configuration.
    """
    # Essential configuration
    id: str
    model: str = "gpt-4o"
    behavior: str = "helpful"
    
    # Agent behavior
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: int = 60
    
    # Features (simple toggles)
    memory_enabled: bool = False
    logging_enabled: bool = True  
    streaming_enabled: bool = False
    middleware_enabled: bool = True
    
    # Advanced configuration (optional)
    memory_config: Optional[Dict[str, Any]] = None
    logging_config: Optional[Dict[str, Any]] = None
    streaming_config: Optional[Dict[str, Any]] = None
    middleware_config: Optional[Dict[str, Any]] = None
    
    # Tools and integrations
    tools: List[str] = field(default_factory=list)
    registries: Dict[str, Any] = field(default_factory=dict)
    
    # Session management  
    session_config: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "id": self.id,
            "model": self.model,
            "behavior": self.behavior,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "memory_enabled": self.memory_enabled,
            "logging_enabled": self.logging_enabled,
            "streaming_enabled": self.streaming_enabled,
            "middleware_enabled": self.middleware_enabled,
            "tools": self.tools,
            "memory_config": self.memory_config,
            "logging_config": self.logging_config,
            "streaming_config": self.streaming_config,
            "middleware_config": self.middleware_config,
            "registries": self.registries,
            "session_config": self.session_config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create configuration from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []
        
        if not self.id:
            errors.append("Agent ID is required")
        
        if not self.model:
            errors.append("Model is required")
        
        if self.temperature is not None and (self.temperature < 0 or self.temperature > 2):
            errors.append("Temperature must be between 0 and 2")
        
        if self.max_tokens is not None and self.max_tokens <= 0:
            errors.append("Max tokens must be positive")
        
        if self.timeout <= 0:
            errors.append("Timeout must be positive")
        
        return errors


class AgentComponent(ABC):
    """
    Base class for agent components.
    
    Components implement specific functionality like memory, logging, etc.
    using composition instead of inheritance.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = True
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the component. Return True if successful."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup resources when agent is destroyed"""
        pass
    
    def is_enabled(self) -> bool:
        """Check if component is enabled"""
        return self.enabled
    
    def disable(self):
        """Disable the component"""
        self.enabled = False
    
    def enable(self):
        """Enable the component"""
        self.enabled = True


class MemoryComponent(AgentComponent):
    """Memory management component"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.adapter = None
        self.memory_store = {}
        
    def initialize(self) -> bool:
        """Initialize memory adapter"""
        try:
            if self.config.get("adapter_type") == "sqlite":
                from langswarm.memory.adapters.langswarm import SQLiteAdapter
                self.adapter = SQLiteAdapter(
                    db_path=self.config.get("db_path", ":memory:")
                )
            elif self.config.get("adapter_type") == "redis":
                from langswarm.memory.adapters.langswarm import RedisAdapter
                self.adapter = RedisAdapter(
                    redis_url=self.config.get("redis_url", "redis://localhost:6379")
                )
            else:
                # In-memory fallback
                self.adapter = None
            
            return True
        except Exception as e:
            print(f"Memory component initialization failed: {e}")
            return False
    
    def store(self, key: str, value: Any):
        """Store value in memory"""
        if not self.enabled:
            return
        
        if self.adapter:
            # Use external adapter
            self.adapter.store(key, value)
        else:
            # Use in-memory store
            self.memory_store[key] = value
    
    def retrieve(self, key: str) -> Any:
        """Retrieve value from memory"""
        if not self.enabled:
            return None
        
        if self.adapter:
            return self.adapter.retrieve(key)
        else:
            return self.memory_store.get(key)
    
    def cleanup(self):
        """Cleanup memory resources"""
        if self.adapter and hasattr(self.adapter, 'close'):
            self.adapter.close()
        self.memory_store.clear()


class LoggingComponent(AgentComponent):
    """Logging management component"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = None
        
    def initialize(self) -> bool:
        """Initialize logger"""
        try:
            agent_id = self.config.get("agent_id", "unknown")
            langsmith_api_key = self.config.get("langsmith_api_key")
            
            # Initialize global logger
            GlobalLogger.initialize(
                name=agent_id,
                langsmith_api_key=langsmith_api_key
            )
            self.logger = GlobalLogger._logger
            return True
        except Exception as e:
            print(f"Logging component initialization failed: {e}")
            return False
    
    def log(self, level: str, message: str, **kwargs):
        """Log a message"""
        if not self.enabled:
            return
        
        # Use print as fallback if logger not available
        if self.logger and hasattr(self.logger, level.lower()):
            getattr(self.logger, level.lower())(message, **kwargs)
        else:
            print(f"[{level.upper()}] {message}")
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log("error", message, **kwargs)
    
    def cleanup(self):
        """Cleanup logging resources"""
        # Logger cleanup if needed
        pass


class StreamingComponent(AgentComponent):
    """Streaming response component"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.stream_mode = config.get("mode", "disabled")
        
    def initialize(self) -> bool:
        """Initialize streaming"""
        # Streaming initialization logic
        return True
    
    def supports_streaming(self) -> bool:
        """Check if current model supports streaming"""
        model = self.config.get("model", "")
        
        # Define streaming-capable models
        streaming_models = [
            "gpt-4", "gpt-4o", "gpt-3.5-turbo", "claude-3", "gemini-pro"
        ]
        
        return any(model.startswith(sm) for sm in streaming_models)
    
    def should_stream(self) -> bool:
        """Determine if response should be streamed"""
        return (
            self.enabled and 
            self.stream_mode != "disabled" and 
            self.supports_streaming()
        )
    
    def cleanup(self):
        """Cleanup streaming resources"""
        pass


class MiddlewareComponent(AgentComponent):
    """Middleware and tool management component"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tool_registry = {}
        self.plugin_registry = {}
        
    def initialize(self) -> bool:
        """Initialize middleware and registries"""
        # Initialize registries from config
        self.tool_registry = self.config.get("tool_registry", {})
        self.plugin_registry = self.config.get("plugin_registry", {})
        return True
    
    def has_tools(self) -> bool:
        """Check if agent has tools available"""
        return len(self.tool_registry) > 0
    
    def get_tool(self, tool_id: str):
        """Get tool by ID"""
        return self.tool_registry.get(tool_id)
    
    def cleanup(self):
        """Cleanup middleware resources"""
        self.tool_registry.clear()
        self.plugin_registry.clear()


class SimpleAgent:
    """
    Simplified Agent using composition instead of complex inheritance.
    
    This replaces the complex AgentWrapper with a clean, focused interface.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize agent with simple configuration object.
        
        Args:
            config: AgentConfig object containing all necessary settings
        """
        self.config = config
        self.id = config.id
        self.model = config.model
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid agent configuration: {', '.join(errors)}")
        
        # Initialize components using composition
        self.components = {}
        self._initialize_components()
        
        # Core agent state
        self.system_prompt = config.system_prompt or self._generate_behavior_prompt()
        self.conversation_history = []
        self.current_session = None
        
        # Initialize the underlying LLM
        self._initialize_llm()
    
    def _initialize_components(self):
        """Initialize agent components based on configuration"""
        
        # Memory component
        if self.config.memory_enabled:
            memory_config = self.config.memory_config or {"adapter_type": "memory"}
            memory_config["agent_id"] = self.config.id
            self.components["memory"] = MemoryComponent(memory_config)
            
        # Logging component
        if self.config.logging_enabled:
            logging_config = self.config.logging_config or {}
            logging_config["agent_id"] = self.config.id
            self.components["logging"] = LoggingComponent(logging_config)
            
        # Streaming component
        if self.config.streaming_enabled:
            streaming_config = self.config.streaming_config or {"mode": "real_time"}
            streaming_config["model"] = self.config.model
            self.components["streaming"] = StreamingComponent(streaming_config)
            
        # Middleware component
        if self.config.middleware_enabled:
            middleware_config = self.config.middleware_config or {}
            self.components["middleware"] = MiddlewareComponent(middleware_config)
        
        # Initialize all components
        for name, component in self.components.items():
            if not component.initialize():
                print(f"Warning: Failed to initialize {name} component")
    
    def _initialize_llm(self):
        """Initialize the underlying LLM"""
        # This would integrate with the actual LLM implementations
        # For now, we'll use a placeholder
        self.llm = None
        
        # In a real implementation, this would be:
        # if self.model.startswith("gpt"):
        #     self.llm = OpenAIAgent(model=self.model, **self.config.to_dict())
        # elif self.model.startswith("claude"):
        #     self.llm = ClaudeAgent(model=self.model, **self.config.to_dict())
        # etc.
    
    def _generate_behavior_prompt(self) -> str:
        """Generate system prompt based on behavior"""
        behavior_prompts = {
            "helpful": "You are a helpful assistant that provides clear, accurate, and useful responses.",
            "analytical": "You are an analytical assistant that provides detailed analysis and data-driven insights.",
            "creative": "You are a creative assistant that provides innovative and imaginative responses.",
            "coding": "You are a coding assistant that helps with programming tasks and technical solutions.",
            "research": "You are a research assistant that provides thorough, well-sourced information.",
            "support": "You are a customer support assistant that provides helpful and professional assistance."
        }
        
        base_prompt = behavior_prompts.get(self.config.behavior, behavior_prompts["helpful"])
        
        # Add tool information if available
        if self.has_tools():
            tool_list = ", ".join(self.config.tools)
            base_prompt += f"\n\nYou have access to these tools: {tool_list}"
        
        return base_prompt
    
    # Simple, clean API methods
    
    def chat(self, message: str, **kwargs) -> str:
        """
        Simple chat interface - the main method users will call.
        
        Args:
            message: User message
            **kwargs: Additional parameters
            
        Returns:
            Agent response
        """
        self._log("info", f"Processing message: {message[:50]}...")
        
        # Store in conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Check if streaming is enabled
        if self._should_stream():
            return self._chat_stream(message, **kwargs)
        else:
            return self._chat_standard(message, **kwargs)
    
    def _chat_standard(self, message: str, **kwargs) -> str:
        """Standard (non-streaming) chat"""
        # This would integrate with the actual LLM
        # For demo purposes, return a simple response
        response = f"[{self.config.behavior} agent {self.id}] Processed: {message}"
        
        # Store response in history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Store in memory if enabled
        self._store_memory("last_interaction", {"user": message, "assistant": response})
        
        self._log("info", f"Generated response: {response[:50]}...")
        return response
    
    def _chat_stream(self, message: str, **kwargs):
        """Streaming chat (generator)"""
        # This would implement actual streaming
        response = f"[Streaming {self.config.behavior} agent {self.id}] Processed: {message}"
        
        # Simulate streaming by yielding chunks
        words = response.split()
        for word in words:
            yield word + " "
            
        # Store complete response
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})
    
    def chat_stream(self, message: str, **kwargs):
        """Public streaming interface"""
        if not self._should_stream():
            # Fallback to standard chat
            response = self.chat(message, **kwargs)
            yield response
        else:
            yield from self._chat_stream(message, **kwargs)
    
    # Component access methods
    
    def has_memory(self) -> bool:
        """Check if memory is enabled"""
        return "memory" in self.components and self.components["memory"].is_enabled()
    
    def has_tools(self) -> bool:
        """Check if tools are available"""
        return "middleware" in self.components and self.components["middleware"].has_tools()
    
    def _should_stream(self) -> bool:
        """Determine if response should be streamed"""
        streaming_component = self.components.get("streaming")
        return streaming_component and streaming_component.should_stream()
    
    def _log(self, level: str, message: str, **kwargs):
        """Log message using logging component"""
        logging_component = self.components.get("logging")
        if logging_component:
            logging_component.log(level, message, **kwargs)
    
    def _store_memory(self, key: str, value: Any):
        """Store value in memory"""
        memory_component = self.components.get("memory")
        if memory_component:
            memory_component.store(key, value)
    
    def _retrieve_memory(self, key: str) -> Any:
        """Retrieve value from memory"""
        memory_component = self.components.get("memory")
        if memory_component:
            return memory_component.retrieve(key)
        return None
    
    # Utility methods
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "id": self.id,
            "model": self.model,
            "behavior": self.config.behavior,
            "components": list(self.components.keys()),
            "tools": self.config.tools,
            "conversation_length": len(self.conversation_history),
            "memory_enabled": self.has_memory(),
            "streaming_enabled": self._should_stream()
        }
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        self._log("info", "Conversation history reset")
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update agent configuration (limited updates)"""
        # Only allow safe updates
        safe_updates = ["temperature", "max_tokens", "timeout"]
        
        for key, value in new_config.items():
            if key in safe_updates:
                setattr(self.config, key, value)
                self._log("info", f"Updated {key} to {value}")
    
    def cleanup(self):
        """Cleanup agent resources"""
        self._log("info", "Cleaning up agent resources")
        
        for component in self.components.values():
            component.cleanup()
        
        self.components.clear()
        self.conversation_history.clear()


# Factory function for easy agent creation
def create_agent(config: Union[AgentConfig, Dict[str, Any]]) -> SimpleAgent:
    """
    Factory function for creating agents with simple configuration.
    
    Args:
        config: AgentConfig object or dictionary
        
    Returns:
        SimpleAgent instance
    """
    if isinstance(config, dict):
        config = AgentConfig.from_dict(config)
    
    return SimpleAgent(config)


# Convenience functions for common agent types
def create_chat_agent(agent_id: str, model: str = "gpt-4o", **kwargs) -> SimpleAgent:
    """Create a simple chat agent"""
    config = AgentConfig(
        id=agent_id,
        model=model,
        behavior="helpful",
        **kwargs
    )
    return SimpleAgent(config)


def create_coding_agent(agent_id: str, model: str = "gpt-4o", **kwargs) -> SimpleAgent:
    """Create a coding assistant agent"""
    # Extract tools parameter to avoid conflict
    tools = kwargs.pop("tools", ["filesystem"])
    
    config = AgentConfig(
        id=agent_id,
        model=model,
        behavior="coding",
        tools=tools,
        **kwargs
    )
    return SimpleAgent(config)


def create_research_agent(agent_id: str, model: str = "gpt-4o", **kwargs) -> SimpleAgent:
    """Create a research assistant agent"""
    config = AgentConfig(
        id=agent_id,
        model=model,
        behavior="research",
        memory_enabled=True,
        **kwargs
    )
    return SimpleAgent(config) 