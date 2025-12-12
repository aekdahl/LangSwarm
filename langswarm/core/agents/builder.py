"""
LangSwarm V2 Agent Builder

Provides a fluent builder pattern for creating agents with smart defaults
and simplified configuration. This replaces the complex AgentWrapper
constructor with an intuitive, type-safe building experience.
"""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
import os
import logging
import inspect

logger = logging.getLogger(__name__)

from .interfaces import ProviderType, AgentCapability
from .base import AgentConfiguration, BaseAgent

# Type hint for memory manager without importing (avoid circular imports)
if TYPE_CHECKING:
    from langswarm.core.memory import IMemoryManager
    from langswarm.tools.registry import IToolRegistry
# STRICT MODE: Import real providers - fail if required providers are missing
# No graceful fallbacks to None - providers must be available when requested
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.gemini import GeminiProvider
from .providers.cohere import CohereProvider
from .providers.mistral import MistralProvider
from .providers.huggingface import HuggingFaceProvider
from .providers.local import LocalProvider
from .providers.litellm import LiteLLMProvider

# Mock provider removed - agent builder now fails fast with clear error messages


class AgentBuilder:
    """
    Fluent builder for creating V2 agents with smart defaults.
    
    Usage:
        # Simple agent
        agent = AgentBuilder().openai().model("gpt-4o").build()
        
        # Advanced agent
        agent = (AgentBuilder()
                 .anthropic()
                 .model("claude-3-5-sonnet-20241022")
                 .system_prompt("You are a helpful assistant")
                 .tools(["calculator", "web_search"])
                 .memory_enabled(True)
                 .streaming(True)
                 .build())
    """
    
    def __init__(self, name: Optional[str] = None, registry: Optional["IToolRegistry"] = None):
        self._name = name or "langswarm-agent"
        self._registry = registry
        self._provider: Optional[ProviderType] = None
        self._model: Optional[str] = None
        self._api_key: Optional[str] = None
        self._base_url: Optional[str] = None
        self._system_prompt: Optional[str] = None
        self._max_tokens: Optional[int] = None
        self._temperature: Optional[float] = None
        self._timeout: int = 30
        
        # Advanced settings
        self._top_p: Optional[float] = None
        self._frequency_penalty: Optional[float] = None
        self._presence_penalty: Optional[float] = None
        self._stop_sequences: Optional[List[str]] = None
        
        # Features
        self._tools_enabled: bool = False
        self._available_tools: List[str] = []
        self._tool_choice: Optional[str] = None
        self._max_tool_iterations: int = 3
        self._memory_enabled: bool = False
        self._max_memory_messages: int = 50
        self._streaming_enabled: bool = False
        
        # External memory manager for persistent sessions
        self._memory_manager: Optional["IMemoryManager"] = None
        
        # Provider-specific config
        self._provider_config: Dict[str, Any] = {}
    
    # Provider selection
    def openai(self, api_key: Optional[str] = None) -> 'AgentBuilder':
        """Configure for OpenAI provider - STRICT MODE"""
        import warnings
        warnings.warn(
            "The .openai() method is deprecated and will be removed in a future version. "
            "Please use .litellm().model('gpt-4o') instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._provider = ProviderType.OPENAI
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # STRICT MODE: API key must be available
        if not self._api_key:
            raise ValueError(
                "OpenAI API key is required. Provide it via api_key parameter or set OPENAI_API_KEY environment variable."
            )
        
        # Set smart defaults for OpenAI
        if not self._model:
            self._model = "gpt-4o"  # Default to latest model
        
        return self
    
    def anthropic(self, api_key: Optional[str] = None) -> 'AgentBuilder':
        """Configure for Anthropic provider - STRICT MODE"""
        import warnings
        warnings.warn(
            "The .anthropic() method is deprecated and will be removed in a future version. "
            "Please use .litellm().model('claude-3-5-sonnet') instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._provider = ProviderType.ANTHROPIC
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        # STRICT MODE: API key must be available
        if not self._api_key:
            raise ValueError(
                "Anthropic API key is required. Provide it via api_key parameter or set ANTHROPIC_API_KEY environment variable."
            )
        
        # Set smart defaults for Anthropic
        if not self._model:
            self._model = "claude-3-5-sonnet-20241022"
        
        return self
    
    def gemini(self, api_key: Optional[str] = None) -> 'AgentBuilder':
        """Configure for Google Gemini provider - STRICT MODE"""
        import warnings
        warnings.warn(
            "The .gemini() method is deprecated and will be removed in a future version. "
            "Please use .litellm().model('gemini/gemini-pro') instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._provider = ProviderType.GEMINI
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        # STRICT MODE: API key must be available
        if not self._api_key:
            raise ValueError(
                "Gemini API key is required. Provide it via api_key parameter or set GEMINI_API_KEY/GOOGLE_API_KEY environment variable."
            )
        
        # Set smart defaults for Gemini
        if not self._model:
            self._model = "gemini-pro"
        
        return self
    
    def cohere(self, api_key: Optional[str] = None) -> 'AgentBuilder':
        """Configure for Cohere provider - STRICT MODE"""
        import warnings
        warnings.warn(
            "The .cohere() method is deprecated and will be removed in a future version. "
            "Please use .litellm().model('command-r-plus') instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._provider = ProviderType.COHERE
        self._api_key = api_key or os.getenv("COHERE_API_KEY")
        
        # STRICT MODE: API key must be available
        if not self._api_key:
            raise ValueError(
                "Cohere API key is required. Provide it via api_key parameter or set COHERE_API_KEY environment variable."
            )
        
        # Set smart defaults for Cohere
        if not self._model:
            self._model = "command-r-plus"
        
        return self
    
    def mistral(self, api_key: Optional[str] = None) -> 'AgentBuilder':
        """Configure for Mistral provider - STRICT MODE"""
        import warnings
        warnings.warn(
            "The .mistral() method is deprecated and will be removed in a future version. "
            "Please use .litellm().model('mistral/mistral-large') instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._provider = ProviderType.MISTRAL
        self._api_key = api_key or os.getenv("MISTRAL_API_KEY")
        
        # STRICT MODE: API key must be available
        if not self._api_key:
            raise ValueError(
                "Mistral API key is required. Provide it via api_key parameter or set MISTRAL_API_KEY environment variable."
            )
        
        # Set smart defaults for Mistral
        if not self._model:
            self._model = "mistral-large"
        
        return self
    
    def huggingface(self, api_key: Optional[str] = None, use_local: bool = False) -> 'AgentBuilder':
        """Configure for Hugging Face provider - STRICT MODE"""
        import warnings
        warnings.warn(
            "The .huggingface() method is deprecated and will be removed in a future version. "
            "Please use .litellm().model('huggingface/...') instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._provider = ProviderType.HUGGINGFACE
        self._api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self._use_local = use_local
        
        # STRICT MODE: API key must be available unless using local models
        if not use_local and not self._api_key:
            raise ValueError(
                "Hugging Face API key is required for remote models. Provide it via api_key parameter, "
                "set HUGGINGFACE_API_KEY environment variable, or use use_local=True for local models."
            )
        
        # Set smart defaults for Hugging Face
        if not self._model:
            if use_local:
                self._model = "meta-llama/Llama-2-7b-chat-hf"
            else:
                self._model = "microsoft/DialoGPT-medium"
        
        return self
    
    def local(self, base_url: str, model: str) -> 'AgentBuilder':
        """Configure for local model provider"""
        import warnings
        warnings.warn(
            "The .local() method is deprecated and will be removed in a future version. "
            "Please use .litellm().model('openai/...') with base_url instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._provider = ProviderType.LOCAL
        self._base_url = base_url
        self._model = model
        return self
    
    def custom(self, provider_config: Dict[str, Any]) -> 'AgentBuilder':
        """Configure custom provider"""
        self._provider = ProviderType.CUSTOM
        self._provider_config = provider_config
        return self
    
    def litellm(self, model: Optional[str] = None) -> 'AgentBuilder':
        """Configure for LiteLLM provider (Unified Interface)"""
        self._provider = ProviderType.LITELLM
        if model:
            self._model = model
        return self
    
    def observability(self, provider: str = "langfuse", disable_tracing: Optional[bool] = None, **kwargs) -> 'AgentBuilder':
        """
        Enable observability (e.g. LangFuse) via LiteLLM.
        
        Note: LangFuse is automatically enabled when LANGFUSE_PUBLIC_KEY and 
        LANGFUSE_SECRET_KEY environment variables are set. Use this method to:
        - Explicitly configure LangFuse with different credentials
        - Override environment variable settings
        - Configure observability programmatically
        
        Args:
            provider: Observability provider (currently only "langfuse" supported)
            disable_tracing: If True, disables sending traces/data to the provider.
                           If None, checks OBSERVABILITY_DISABLE_TRACING env var.
                           (default: None)
            **kwargs: Provider-specific configuration:
                - public_key: LangFuse public key (overrides LANGFUSE_PUBLIC_KEY)
                - secret_key: LangFuse secret key (overrides LANGFUSE_SECRET_KEY)
                - host: LangFuse host URL (overrides LANGFUSE_HOST)
        
        Returns:
            Self for method chaining
        """
        if provider == "langfuse":
            try:
                import litellm
                # Verify langfuse is installed
                try:
                    import langfuse
                except ImportError:
                    logger.warning("LangFuse not installed. Run 'pip install langfuse' to enable observability.")
                    return self

                # Set callbacks
                if "langfuse" not in litellm.success_callback:
                    litellm.success_callback.append("langfuse")
                if "langfuse" not in litellm.failure_callback:
                    litellm.failure_callback.append("langfuse")
                
                # Set env vars if provided
                if "public_key" in kwargs:
                    os.environ["LANGFUSE_PUBLIC_KEY"] = kwargs["public_key"]
                if "secret_key" in kwargs:
                    os.environ["LANGFUSE_SECRET_KEY"] = kwargs["secret_key"]
                if "host" in kwargs:
                    os.environ["LANGFUSE_HOST"] = kwargs["host"]
                
                # Determine disable_tracing value
                if disable_tracing is None:
                    # Check env var if not explicitly set
                    env_val = os.getenv("OBSERVABILITY_DISABLE_TRACING", "false").lower()
                    should_disable = env_val in ("true", "1", "yes", "on")
                else:
                    should_disable = disable_tracing

                # Store disable_tracing preference in provider config
                self._provider_config["observability_disable_tracing"] = should_disable
                
                if should_disable:
                    logger.info("Enabled LangFuse observability (tracing DISABLED by config)")
                else:
                    logger.info("Enabled LangFuse observability for LiteLLM")
                    
            except ImportError:
                logger.warning("LiteLLM not installed, cannot enable observability")
                
        return self
        
    def failover(self, models: List[str]) -> 'AgentBuilder':
        """Set failover models for LiteLLM (e.g. ['gpt-4o', 'claude-3-5-sonnet'])"""
        self._provider_config["fallbacks"] = models
        return self
    
    # Basic configuration
    def name(self, name: str) -> 'AgentBuilder':
        """Set agent name"""
        self._name = name
        return self
    
    def model(self, model: str) -> 'AgentBuilder':
        """Set model name"""
        self._model = model
        return self
    
    def api_key(self, api_key: str) -> 'AgentBuilder':
        """Set API key"""
        self._api_key = api_key
        return self
    
    def base_url(self, base_url: str) -> 'AgentBuilder':
        """Set base URL for API calls"""
        self._base_url = base_url
        return self
    
    def system_prompt(self, prompt: str) -> 'AgentBuilder':
        """Set system prompt"""
        self._system_prompt = prompt
        return self
    
    def max_tokens(self, tokens: int) -> 'AgentBuilder':
        """Set maximum tokens for responses"""
        self._max_tokens = tokens
        return self
    
    def temperature(self, temp: float) -> 'AgentBuilder':
        """Set temperature (0.0 to 2.0)"""
        self._temperature = temp
        return self
    
    def timeout(self, seconds: int) -> 'AgentBuilder':
        """Set request timeout in seconds"""
        self._timeout = seconds
        return self
    
    # Advanced parameters
    def top_p(self, value: float) -> 'AgentBuilder':
        """Set top_p for nucleus sampling"""
        self._top_p = value
        return self
    
    def frequency_penalty(self, value: float) -> 'AgentBuilder':
        """Set frequency penalty"""
        self._frequency_penalty = value
        return self
    
    def presence_penalty(self, value: float) -> 'AgentBuilder':
        """Set presence penalty"""
        self._presence_penalty = value
        return self
    
    def stop_sequences(self, sequences: List[str]) -> 'AgentBuilder':
        """Set stop sequences"""
        self._stop_sequences = sequences
        return self
    
    # Feature configuration
    def tools(self, tool_names: List[str], tool_choice: str = "auto") -> 'AgentBuilder':
        """Enable tools with specified names - automatic injection will occur at build time"""
        self._tools_enabled = True
        self._available_tools = tool_names
        self._tool_choice = tool_choice
        return self
    
    def tools_enabled(self, enabled: bool = True) -> 'AgentBuilder':
        """Enable or disable tool support"""
        self._tools_enabled = enabled
        return self
    
    def max_tool_iterations(self, iterations: int) -> 'AgentBuilder':
        """Set maximum tool call iterations for self-correction loop (default: 3)"""
        if iterations < 1:
            raise ValueError("max_tool_iterations must be at least 1")
        self._max_tool_iterations = iterations
        return self
    
    def memory_enabled(self, enabled: bool = True, max_messages: int = 50) -> 'AgentBuilder':
        """Enable conversation memory"""
        self._memory_enabled = enabled
        self._max_memory_messages = max_messages
        return self
    
    def memory(self, config: Union[bool, "IMemoryManager"] = True, max_messages: int = 50) -> 'AgentBuilder':
        """
        Smart alias for memory configuration.
        
        Args:
            config: Either a boolean to enable/disable default memory, 
                   or an IMemoryManager instance for external memory.
            max_messages: Max messages to keep in memory (only used if config is bool)
        """
        if isinstance(config, bool):
            return self.memory_enabled(config, max_messages)
        else:
            # Assume it's a memory manager instance
            return self.memory_manager(config)
    
    def registry(self, registry: "IToolRegistry") -> 'AgentBuilder':
        """Set custom tool registry"""
        self._registry = registry
        return self

    def memory_manager(self, manager: "IMemoryManager") -> 'AgentBuilder':
        """
        Set external memory manager for persistent session storage.
        
        When a memory manager is set:
        - Sessions are automatically restored from external storage when accessed
        - Messages are persisted to external storage (write-through caching)
        - Local in-memory cache is used for fast access
        
        Args:
            manager: IMemoryManager instance (e.g., from create_memory_manager())
            
        Returns:
            Self for method chaining
            
        Example:
            manager = create_memory_manager("sqlite", db_path="conversations.db")
            await manager.backend.connect()
            
            agent = await (AgentBuilder()
                .openai()
                .memory_manager(manager)
                .build())
        """
        self._memory_manager = manager
        # Also enable memory if not already enabled
        if not self._memory_enabled:
            self._memory_enabled = True
        return self
    
    def streaming(self, enabled: bool = True) -> 'AgentBuilder':
        """Enable streaming responses"""
        self._streaming_enabled = enabled
        return self
    
    def provider_config(self, config: Dict[str, Any]) -> 'AgentBuilder':
        """Set provider-specific configuration"""
        self._provider_config.update(config)
        return self
    
    # Aliases for convenience
    def provider(self, provider_type: ProviderType) -> 'AgentBuilder':
        """Set provider type directly with intelligent defaults"""
        self._provider = provider_type
        
        # Apply provider-specific defaults
        if provider_type == ProviderType.OPENAI:
            if not self._api_key:
                self._api_key = os.getenv("OPENAI_API_KEY")
        elif provider_type == ProviderType.ANTHROPIC:
            if not self._api_key:
                self._api_key = os.getenv("ANTHROPIC_API_KEY")
        elif provider_type == ProviderType.GEMINI:
            if not self._api_key:
                self._api_key = os.getenv("GOOGLE_API_KEY")
        elif provider_type == ProviderType.MISTRAL:
            if not self._api_key:
                self._api_key = os.getenv("MISTRAL_API_KEY")
        elif provider_type == ProviderType.COHERE:
            if not self._api_key:
                self._api_key = os.getenv("COHERE_API_KEY")
        elif provider_type == ProviderType.HUGGINGFACE:
            if not self._api_key:
                self._api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        return self
    
    def enable_tools(self, tool_names: List[str], tool_choice: str = "auto") -> 'AgentBuilder':
        """Alias for tools() method"""
        return self.tools(tool_names, tool_choice)
    
    def enable_memory(self, max_messages: int = 50) -> 'AgentBuilder':
        """Alias for memory_enabled() method"""
        return self.memory_enabled(True, max_messages)
    
    def enable_streaming(self) -> 'AgentBuilder':
        """Alias for streaming() method"""
        return self.streaming(True)
    
    # Convenience methods for common configurations
    def coding_assistant(self) -> 'AgentBuilder':
        """Configure as a coding assistant"""
        return (self
                .system_prompt("You are an expert software developer and coding assistant. "
                              "Provide clear, accurate, and helpful programming guidance.")
                .tools(["code_execution", "file_operations", "web_search"])
                .memory_enabled(True)
                .temperature(0.1))  # Lower temperature for more deterministic code
    
    def creative_writer(self) -> 'AgentBuilder':
        """Configure as a creative writer"""
        return (self
                .system_prompt("You are a creative and imaginative writer. "
                              "Help with storytelling, creative writing, and content creation.")
                .temperature(0.8)  # Higher temperature for creativity
                .memory_enabled(True))
    
    def research_assistant(self) -> 'AgentBuilder':
        """Configure as a research assistant"""
        return (self
                .system_prompt("You are a thorough research assistant. "
                              "Help find information, analyze data, and provide well-sourced insights.")
                .tools(["web_search", "document_analysis", "data_processing"])
                .memory_enabled(True)
                .temperature(0.3))
    
    def customer_support(self) -> 'AgentBuilder':
        """Configure for customer support"""
        return (self
                .system_prompt("You are a helpful and professional customer support agent. "
                              "Be polite, empathetic, and solution-focused.")
                .tools(["knowledge_base", "ticket_system"])
                .memory_enabled(True)
                .temperature(0.4))
    
    # Build methods
    def build_config(self) -> AgentConfiguration:
        """Build just the configuration object"""
        # Validate required fields
        if not self._provider:
            raise ValueError("Provider must be specified")
        
        if not self._model:
            raise ValueError("Model must be specified")
        
        # Validate temperature range
        if self._temperature is not None and not (0.0 <= self._temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        
        # Validate max_tokens
        if self._max_tokens is not None and self._max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        
        # Validate timeout
        if self._timeout is not None and self._timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        # Validate provider-specific constraints
        self._validate_provider_specific()
        
        # Inject agent name into provider config for observability
        self._provider_config["agent_name"] = self._name
        
        return AgentConfiguration(
            provider=self._provider,
            model=self._model,
            api_key=self._api_key,
            base_url=self._base_url,
            system_prompt=self._system_prompt,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            timeout=self._timeout,
            top_p=self._top_p,
            frequency_penalty=self._frequency_penalty,
            presence_penalty=self._presence_penalty,
            stop_sequences=self._stop_sequences,
            tools_enabled=self._tools_enabled,
            available_tools=self._available_tools,
            tool_choice=self._tool_choice,
            max_tool_iterations=self._max_tool_iterations,
            memory_enabled=self._memory_enabled,
            max_memory_messages=self._max_memory_messages,
            streaming_enabled=self._streaming_enabled,
            provider_config=self._provider_config
        )
    
    def _validate_provider_specific(self):
        """Validate provider-specific constraints (Deprecated)"""
        # Validation is now handled by the provider or LiteLLM at runtime.
        # We skip static validation to allow for new models without code changes.
        pass
    
    async def build(self) -> BaseAgent:
        """Build the complete agent with automatic tool injection"""
        config = self.build_config()
        
        # Create provider based on type and availability
        provider = self._create_provider(config)
        agent = BaseAgent(
            self._name, 
            config, 
            provider,
            memory_manager=self._memory_manager
        )
        
        # Automatic tool injection if tools are specified
        if config.tools_enabled and config.available_tools:
            await self._auto_inject_tools(agent, config.available_tools)
        
        return agent
    
    def build_sync(self) -> BaseAgent:
        """Build agent synchronously (without automatic tool injection)"""
        config = self.build_config()
        provider = self._create_provider(config)
        return BaseAgent(
            self._name, 
            config, 
            provider,
            memory_manager=self._memory_manager
        )
    
    def tool_configs(self, configs: Dict[str, Dict[str, Any]]) -> 'AgentBuilder':
        """Set configuration for specific tools"""
        self._tool_configs = configs
        return self

    async def _auto_inject_tools(self, agent: BaseAgent, tool_names: List[str]) -> None:
        """Pass tools to agent - let provider handle tool integration"""
        try:
            # Use custom registry if provided, otherwise default
            if self._registry:
                registry = self._registry
            else:
                from langswarm.tools.registry import ToolRegistry
                registry = ToolRegistry()
                
                # Auto-populate registry with adapted MCP tools if empty and using default registry
                if not registry._tools:
                    registry.auto_populate_with_mcp_tools()
            
            missing_tools = []
            
            for tool_name in tool_names:
                tool = registry.get_tool(tool_name)
                
                if tool:
                    # Try injection methods in order of preference
                    injected = False
                    
                    # 1. register_tool (Preferred V2 interface)
                    if hasattr(agent, 'register_tool'):
                        if inspect.iscoroutinefunction(agent.register_tool):
                            await agent.register_tool(tool)
                        else:
                            agent.register_tool(tool)
                        injected = True
                        
                    # 2. add_tools (List based)
                    elif hasattr(agent, 'add_tools'):
                        if inspect.iscoroutinefunction(agent.add_tools):
                            await agent.add_tools([tool])
                        else:
                            agent.add_tools([tool])
                        injected = True
                        
                    # 3. add_tool (Single tool)
                    elif hasattr(agent, 'add_tool'):
                        if inspect.iscoroutinefunction(agent.add_tool):
                            await agent.add_tool(tool)
                        else:
                            agent.add_tool(tool)
                        injected = True
                        
                    if injected:
                        logger.info(f"✅ Injected tool '{tool_name}' into agent '{agent.name}'")
                    else:
                        # Fallback for agents without explicit tool methods (e.g. some legacy wrappers)
                        # We just hope the provider picks it up from config later if we set it here
                        if not hasattr(agent, '_available_tools'):
                            agent._available_tools = []
                        if isinstance(agent._available_tools, list):
                            agent._available_tools.append(tool_name)
                            logger.warning(f"⚠️ Agent '{agent.name}' has no injection method. Added '{tool_name}' to _available_tools list.")
                        else:
                            logger.warning(f"⚠️ Could not inject tool '{tool_name}' into agent '{agent.name}': No compatible method found.")
                            
                    # Apply tool configurations if provided
                    if hasattr(self, '_tool_configs') and self._tool_configs:
                        if tool_name in self._tool_configs:
                            config = self._tool_configs[tool_name]
                            await tool.initialize(config)
                            logger.info(f"🔧 Configured tool '{tool_name}' with provided settings")
                            
                else:
                    missing_tools.append(tool_name)
                    logger.warning(f"❌ Tool '{tool_name}' not found in registry")

            if missing_tools:
                logger.warning(f"⚠️ The following tools were requested but not found: {missing_tools}")
                # We do NOT raise an error here to allow partial startup as requested
                
        except Exception as e:
            # Log error but don't crash unless critical
            logger.error(f"Tool injection error for agent '{agent.name}': {e}")
            raise RuntimeError(f"Tool injection failed for agent '{agent.name}': {e}") from e
    
    def _create_provider(self, config: AgentConfiguration):
        """Create the appropriate provider based on configuration - STRICT MODE"""
        # STRICT MODE: All providers are imported directly, no fallback checks needed
        if config.provider == ProviderType.OPENAI:
            return OpenAIProvider()
        elif config.provider == ProviderType.ANTHROPIC:
            return AnthropicProvider()
        elif config.provider == ProviderType.GEMINI:
            return GeminiProvider()
        elif config.provider == ProviderType.COHERE:
            return CohereProvider()
        elif config.provider == ProviderType.MISTRAL:
            return MistralProvider()
        elif config.provider == ProviderType.HUGGINGFACE:
            return HuggingFaceProvider(
                use_local=getattr(config, 'use_local', False),
                device=getattr(config, 'device', 'auto')
            )
        elif config.provider == ProviderType.LOCAL:
            return LocalProvider(
                backend=getattr(config, 'backend', 'ollama'),
                base_url=getattr(config, 'base_url', None)
            )
        elif config.provider == ProviderType.LITELLM:
            return LiteLLMProvider()
        else:
            raise ValueError(
                f"Unknown provider type '{config.provider}'. "
                f"Supported providers: OPENAI, ANTHROPIC, GEMINI, COHERE, MISTRAL, HUGGINGFACE, LOCAL"
            )


# Convenience factory functions
def create_agent(name: str = "langswarm-agent") -> AgentBuilder:
    """Create a new agent builder"""
    return AgentBuilder(name)


async def create_openai_agent(
    name: str = "openai-agent",
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs: Any
) -> BaseAgent:
    """Create an OpenAI agent with smart defaults.
    
    Args:
        name: Unique identifier for the agent
        model: OpenAI model name (e.g., "gpt-4o", "gpt-3.5-turbo")
        api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        system_prompt: System instructions for the agent
        temperature: Sampling temperature (0.0 to 2.0)
        **kwargs: Additional configuration options
        
    Returns:
        BaseAgent: Configured OpenAI agent ready for use
        
    Raises:
        ValueError: If API key is not provided or found in environment
        
    Example:
        >>> agent = await create_openai_agent(
        ...     name="researcher",
        ...     model="gpt-3.5-turbo",
        ...     system_prompt="You are a research specialist"
        ... )
        >>> response = await agent.execute("What is quantum computing?")
    """
    builder = (AgentBuilder(name)
               .openai(api_key)
               .model(model))
    
    # Apply explicit parameters
    if system_prompt:
        builder.system_prompt(system_prompt)
    
    if temperature != 0.7:
        builder.temperature(temperature)
    
    # Handle tool_configs specifically
    if 'tool_configs' in kwargs:
        builder.tool_configs(kwargs.pop('tool_configs'))
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(builder, key) and callable(getattr(builder, key)):
            getattr(builder, key)(value)
    
    return await builder.build()


def create_openai_agent_sync(
    name: str = "openai-agent",
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs: Any
) -> BaseAgent:
    """Create an OpenAI agent synchronously (without automatic tool injection).
    
    Args:
        name: Unique identifier for the agent
        model: OpenAI model name (e.g., "gpt-4o", "gpt-3.5-turbo")
        api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        system_prompt: System instructions for the agent
        temperature: Sampling temperature (0.0 to 2.0)
        **kwargs: Additional configuration options
        
    Returns:
        BaseAgent: Configured OpenAI agent ready for use
        
    Note:
        This synchronous version does not automatically inject tools.
        Use the async version for full functionality.
    """
    builder = (AgentBuilder(name)
               .openai(api_key)
               .model(model))
    
    if system_prompt:
        builder.system_prompt(system_prompt)
    
    if temperature != 0.7:
        builder.temperature(temperature)
    
    for key, value in kwargs.items():
        if hasattr(builder, key) and callable(getattr(builder, key)):
            getattr(builder, key)(value)
    
    return builder.build_sync()


def create_anthropic_agent(
    name: str = "anthropic-agent", 
    model: str = "claude-3-5-sonnet-20241022",
    api_key: Optional[str] = None,
    **kwargs
) -> BaseAgent:
    """Create an Anthropic agent with smart defaults"""
    builder = (AgentBuilder(name)
               .anthropic(api_key)
               .model(model))
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()


def create_gemini_agent(
    name: str = "gemini-agent",
    model: str = "gemini-pro",
    api_key: Optional[str] = None,
    **kwargs
) -> BaseAgent:
    """Create a Gemini agent with smart defaults"""
    builder = (AgentBuilder(name)
               .gemini(api_key)
               .model(model))
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()


def create_cohere_agent(
    name: str = "cohere-agent",
    model: str = "command-r-plus",
    api_key: Optional[str] = None,
    **kwargs
) -> BaseAgent:
    """Create a Cohere agent with smart defaults"""
    builder = (AgentBuilder(name)
               .cohere(api_key)
               .model(model))
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()


def create_mistral_agent(
    name: str = "mistral-agent",
    model: str = "mistral-large",
    api_key: Optional[str] = None,
    **kwargs
) -> BaseAgent:
    """Create a Mistral agent with smart defaults"""
    builder = (AgentBuilder(name)
               .mistral(api_key)
               .model(model))
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()


def create_huggingface_agent(
    name: str = "huggingface-agent",
    model: str = "microsoft/DialoGPT-medium",
    api_key: Optional[str] = None,
    use_local: bool = False,
    **kwargs
) -> BaseAgent:
    """Create a Hugging Face agent with smart defaults"""
    builder = (AgentBuilder(name)
               .huggingface(api_key, use_local)
               .model(model))
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()


def create_local_agent(
    name: str = "local-agent", 
    model: str = "llama2:7b",
    backend: str = "ollama",
    base_url: Optional[str] = None,
    **kwargs
) -> BaseAgent:
    """Create a Local agent with smart defaults"""
    builder = (AgentBuilder(name)
               .local(base_url or f"http://localhost:{'11434' if backend == 'ollama' else '8080'}", model))
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()


def create_coding_assistant(
    provider: str = "openai",
    model: Optional[str] = None,
    **kwargs
) -> BaseAgent:
    """Create a coding assistant agent"""
    builder = AgentBuilder("coding-assistant").coding_assistant()
    
    if provider == "openai":
        builder = builder.openai().model(model or "gpt-4o")
    elif provider == "anthropic":
        builder = builder.anthropic().model(model or "claude-3-5-sonnet-20241022")
    elif provider == "gemini":
        builder = builder.gemini().model(model or "gemini-pro")
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()


def create_research_assistant(
    provider: str = "openai",
    model: Optional[str] = None,
    **kwargs
) -> BaseAgent:
    """Create a research assistant agent"""
    builder = AgentBuilder("research-assistant").research_assistant()
    
    if provider == "openai":
        builder = builder.openai().model(model or "gpt-4o")
    elif provider == "anthropic":
        builder = builder.anthropic().model(model or "claude-3-5-sonnet-20241022")
    elif provider == "gemini":
        builder = builder.gemini().model(model or "gemini-pro")
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # Apply additional kwargs
    for key, value in kwargs.items():
        if hasattr(builder, key):
            getattr(builder, key)(value)
    
    return builder.build()
