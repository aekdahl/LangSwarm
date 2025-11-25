"""
Simple API for LangSwarm examples.

This provides a clean, beginner-friendly interface for the most common use cases.
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator, Union, TYPE_CHECKING
from pathlib import Path

# Type hint for memory manager without importing (avoid circular imports)
if TYPE_CHECKING:
    from langswarm.core.memory import IMemoryManager

# Import error handling
def require_package(package_name: str, feature_desc: str):
    """Simple package requirement checker."""
    try:
        if package_name == "openai":
            import openai
            return openai
        elif package_name == "yaml":
            import yaml
            return yaml
        else:
            exec(f"import {package_name}")
            return eval(package_name)
    except ImportError:
        raise ImportError(
            f"❌ Package '{package_name}' is required for {feature_desc} but not installed.\n\n"
            f"📦 Install with: pip install {package_name}\n"
            f"💡 Or install all dependencies: pip install langswarm[full]"
        )


class Agent:
    """Simple agent wrapper for examples."""
    
    def __init__(self, model: str, provider: Optional[str] = None, 
                 system_prompt: Optional[str] = None, memory: bool = False,
                 tools: Optional[List[str]] = None, stream: bool = False,
                 track_costs: bool = False, 
                 memory_manager: Optional["IMemoryManager"] = None,
                 **kwargs):
        self.model = model
        self.provider = provider or self._detect_provider(model)
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        self.memory_enabled = memory or (memory_manager is not None)
        self.tools = tools or []
        self.stream_enabled = stream
        self.track_costs = track_costs
        self.kwargs = kwargs
        
        # External memory manager for persistent sessions
        self._memory_manager: Optional["IMemoryManager"] = memory_manager
        
        # Usage tracking
        self._usage_stats = {
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "request_count": 0
        }
        
        # Local in-memory conversation history (fast cache)
        self._conversation_history = []
        
        # Session ID for external memory
        self._session_id: Optional[str] = None
        
        # Initialize the actual agent
        self._agent = self._create_agent()
    
    def _detect_provider(self, model: str) -> str:
        """Auto-detect provider from model name."""
        model_lower = model.lower()
        if any(x in model_lower for x in ["gpt", "turbo", "davinci"]):
            return "openai"
        elif any(x in model_lower for x in ["claude", "anthropic"]):
            return "anthropic"
        elif any(x in model_lower for x in ["gemini", "palm", "bard"]):
            return "google"
        elif "command" in model_lower:
            return "cohere"
        elif "mistral" in model_lower or "mixtral" in model_lower:
            return "mistral"
        else:
            return "openai"  # Default fallback
    
    def _create_agent(self):
        """Create the actual agent implementation."""
        if self.provider == "openai":
            openai = require_package("openai", "OpenAI chat completion")
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable required")
            
            client = openai.OpenAI(api_key=api_key)
            return {"client": client, "type": "openai"}
        
        # For other providers, return mock for now
        return {"client": None, "type": self.provider}
    
    async def chat(self, message: str, session_id: Optional[str] = None) -> str:
        """Send a message and get a response.
        
        Args:
            message: The user message to send
            session_id: Optional session ID for external memory persistence
            
        Returns:
            The assistant's response
        """
        # Handle session ID for external memory
        if session_id:
            self._session_id = session_id
        
        # Restore from external memory if needed (session resumption)
        if self._memory_manager and self._session_id and not self._conversation_history:
            await self._restore_from_memory()
        
        if self.memory_enabled:
            self._conversation_history.append({"role": "user", "content": message})
            # Persist to external memory
            await self._persist_message("user", message)
        
        if self._agent["type"] == "openai":
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if self.memory_enabled and self._conversation_history:
                # Add conversation history
                messages.extend(self._conversation_history)
            else:
                # Just this message
                messages.append({"role": "user", "content": message})
            
            # Make API call
            response = self._agent["client"].chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            
            assistant_message = response.choices[0].message.content
            
            # Track usage
            if hasattr(response, 'usage'):
                self._usage_stats["total_tokens"] += response.usage.total_tokens
                # Rough cost estimation for gpt-3.5-turbo
                if "gpt-3.5" in self.model:
                    cost_per_token = 0.000002  # Approximate
                    self._usage_stats["estimated_cost"] += response.usage.total_tokens * cost_per_token
            
            self._usage_stats["request_count"] += 1
            
            if self.memory_enabled:
                self._conversation_history.append({"role": "assistant", "content": assistant_message})
                # Persist to external memory
                await self._persist_message("assistant", assistant_message)
            
            return assistant_message
        
        else:
            # Mock response for non-OpenAI providers
            return f"Mock response from {self.provider} {self.model}: I received your message '{message}'"
    
    async def _restore_from_memory(self) -> None:
        """Restore conversation history from external memory."""
        if not self._memory_manager or not self._session_id:
            return
        
        try:
            external_session = await self._memory_manager.get_session(self._session_id)
            if external_session:
                messages = await external_session.get_messages()
                for msg in messages:
                    role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                    # Skip system messages (we add our own)
                    if role != "system":
                        self._conversation_history.append({
                            "role": role,
                            "content": msg.content
                        })
        except Exception as e:
            # Don't fail if memory restoration fails
            pass
    
    async def _persist_message(self, role: str, content: str) -> None:
        """Persist a message to external memory."""
        if not self._memory_manager:
            return
        
        try:
            # Import Message class from memory module
            from langswarm.core.memory import Message, MessageRole
            
            # Get or create session
            session_id = self._session_id or "default"
            external_session = await self._memory_manager.get_or_create_session(session_id)
            
            # Convert role string to MessageRole enum
            role_map = {
                "user": MessageRole.USER,
                "assistant": MessageRole.ASSISTANT,
                "system": MessageRole.SYSTEM,
            }
            msg_role = role_map.get(role, MessageRole.USER)
            
            # Create and add message
            memory_message = Message(role=msg_role, content=content)
            await external_session.add_message(memory_message)
        except Exception:
            # Don't fail the main operation if persistence fails
            pass
    
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Stream a response as it's generated."""
        if self._agent["type"] == "openai":
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if self.memory_enabled:
                messages.extend(self._conversation_history)
                messages.append({"role": "user", "content": message})
            else:
                messages.append({"role": "user", "content": message})
            
            response = self._agent["client"].chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Update memory and stats
            if self.memory_enabled:
                self._conversation_history.append({"role": "user", "content": message})
                self._conversation_history.append({"role": "assistant", "content": full_response})
            
            self._usage_stats["request_count"] += 1
        
        else:
            # Mock streaming
            mock_response = f"Mock streaming response from {self.provider}"
            for word in mock_response.split():
                yield word + " "
                await asyncio.sleep(0.1)  # Simulate streaming delay
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self._usage_stats.copy()


class Workflow:
    """Simple workflow wrapper."""
    
    def __init__(self, definition: str, agents: List[Dict[str, Any]]):
        self.definition = definition
        self.agents = {agent["id"]: Agent(**agent) for agent in agents}
    
    async def run(self, input_message: str) -> str:
        """Run the workflow with input."""
        # Simple implementation: just use the first agent
        if self.agents:
            first_agent = list(self.agents.values())[0]
            return await first_agent.chat(input_message)
        return "No agents configured"


class Config:
    """Simple configuration wrapper."""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.data = config_data
        self._agents = {}
        
        # Create agents from config
        for agent_config in config_data.get("agents", []):
            agent = Agent(**agent_config)
            self._agents[agent_config["id"]] = agent
    
    def get_agent(self, agent_id: str) -> Agent:
        """Get an agent by ID."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent '{agent_id}' not found")
        return self._agents[agent_id]


def create_agent(
    model: str, 
    memory_manager: Optional["IMemoryManager"] = None,
    **kwargs
) -> Agent:
    """Create a simple agent.
    
    Args:
        model: AI model name (e.g., "gpt-3.5-turbo", "gpt-4")
        memory_manager: Optional external memory manager for persistent sessions.
            When provided, conversations are automatically persisted and can be
            restored across agent restarts.
        **kwargs: Additional agent options:
            - provider: Provider name (auto-detected from model if not specified)
            - system_prompt: System instructions for the agent
            - memory: Enable in-memory conversation history (default: False)
            - tools: List of tool names to enable
            - stream: Enable streaming responses (default: False)
            - track_costs: Track token usage and costs (default: False)
        
    Returns:
        Agent instance
        
    Example:
        # Simple agent
        agent = create_agent(model="gpt-4")
        
        # Agent with persistent memory
        from langswarm.core.memory import create_memory_manager
        manager = create_memory_manager("sqlite", db_path="memory.db")
        await manager.backend.connect()
        
        agent = create_agent(
            model="gpt-4",
            memory_manager=manager,
            system_prompt="You are a helpful assistant"
        )
        
        # Chat with session persistence
        response = await agent.chat("Hello!", session_id="user-123")
    """
    return Agent(model=model, memory_manager=memory_manager, **kwargs)


def create_workflow(definition: str, agents: List[Dict[str, Any]]) -> Workflow:
    """Create a simple workflow.
    
    Args:
        definition: Workflow definition string
        agents: List of agent configurations
        
    Returns:
        Workflow instance
    """
    return Workflow(definition=definition, agents=agents)


def load_config(filepath: str) -> Config:
    """Load configuration from YAML file.
    
    Args:
        filepath: Path to YAML configuration file
        
    Returns:
        Config instance
    """
    yaml = require_package("yaml", "YAML configuration loading")
    
    config_path = Path(filepath)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    
    with open(config_path) as f:
        config_data = yaml.safe_load(f)
    
    return Config(config_data)