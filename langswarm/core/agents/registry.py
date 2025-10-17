"""
LangSwarm V2 Agent Registry

Simple, thread-safe registry for managing agent instances. Replaces the complex
V1 agent registry with a clean, modern implementation.
"""

import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from .interfaces import IAgent, AgentStatus
from .base import AgentMetadata


class AgentRegistry:
    """
    Thread-safe registry for managing V2 agent instances.
    
    Features:
    - Thread-safe agent registration and lookup
    - Agent lifecycle management
    - Statistics and monitoring
    - Health checking
    - Cleanup of inactive agents
    """
    
    _instance: Optional['AgentRegistry'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'AgentRegistry':
        """Singleton pattern for global agent registry"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._agents: Dict[str, IAgent] = {}
        self._metadata: Dict[str, AgentMetadata] = {}
        self._lock = threading.RLock()
        self._initialized = True
    
    def register(
        self, 
        agent: IAgent, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register an agent in the registry.
        
        Args:
            agent: The agent instance to register
            metadata: Optional metadata about the agent
            
        Returns:
            bool: True if registration was successful
        """
        with self._lock:
            try:
                agent_id = agent.agent_id
                
                # Check if agent is already registered
                if agent_id in self._agents:
                    raise ValueError(f"Agent {agent_id} is already registered")
                
                # Store agent and metadata
                self._agents[agent_id] = agent
                
                # Create or update metadata
                if agent_id not in self._metadata:
                    self._metadata[agent_id] = AgentMetadata(
                        agent_id=agent_id,
                        name=agent.name,
                        description=metadata.get('description') if metadata else None,
                        tags=metadata.get('tags', []) if metadata else []
                    )
                
                return True
                
            except Exception as e:
                print(f"Failed to register agent: {e}")
                return False
    
    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: The agent ID to unregister
            
        Returns:
            bool: True if unregistration was successful
        """
        with self._lock:
            try:
                if agent_id in self._agents:
                    # Shutdown agent gracefully
                    agent = self._agents[agent_id]
                    if hasattr(agent, 'shutdown'):
                        # Note: This is sync, agent.shutdown() is async
                        # In a real implementation, we'd handle this properly
                        pass
                    
                    del self._agents[agent_id]
                    
                    # Keep metadata for historical purposes but mark as unregistered
                    if agent_id in self._metadata:
                        self._metadata[agent_id].updated_at = datetime.now()
                    
                    return True
                
                return False
                
            except Exception as e:
                print(f"Failed to unregister agent {agent_id}: {e}")
                return False
    
    def get(self, agent_id: str) -> Optional[IAgent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: The agent ID to look up
            
        Returns:
            Optional[IAgent]: The agent instance if found
        """
        with self._lock:
            return self._agents.get(agent_id)
    
    def get_by_name(self, name: str) -> Optional[IAgent]:
        """
        Get an agent by name.
        
        Args:
            name: The agent name to look up
            
        Returns:
            Optional[IAgent]: The agent instance if found
        """
        with self._lock:
            for agent in self._agents.values():
                if agent.name == name:
                    return agent
            return None
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent IDs.
        
        Returns:
            List[str]: List of agent IDs
        """
        with self._lock:
            return list(self._agents.keys())
    
    def list_agent_info(self) -> List[Dict[str, Any]]:
        """
        Get basic information about all registered agents.
        
        Returns:
            List[Dict[str, Any]]: List of agent information
        """
        with self._lock:
            agent_info = []
            for agent_id, agent in self._agents.items():
                metadata = self._metadata.get(agent_id)
                
                info = {
                    "agent_id": agent_id,
                    "name": agent.name,
                    "status": agent.status.value,
                    "provider": agent.configuration.provider.value,
                    "model": agent.configuration.model,
                    "capabilities": [cap.value for cap in agent.capabilities],
                    "created_at": metadata.created_at.isoformat() if metadata else None,
                    "total_messages": metadata.total_messages if metadata else 0
                }
                
                agent_info.append(info)
            
            return agent_info
    
    def get_metadata(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get metadata for an agent.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            Optional[AgentMetadata]: The agent metadata if found
        """
        with self._lock:
            return self._metadata.get(agent_id)
    
    def update_metadata(self, agent_id: str, **updates) -> bool:
        """
        Update metadata for an agent.
        
        Args:
            agent_id: The agent ID
            **updates: Metadata fields to update
            
        Returns:
            bool: True if update was successful
        """
        with self._lock:
            if agent_id in self._metadata:
                metadata = self._metadata[agent_id]
                
                for key, value in updates.items():
                    if hasattr(metadata, key):
                        setattr(metadata, key, value)
                
                metadata.updated_at = datetime.now()
                return True
            
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Get health status of all registered agents.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        with self._lock:
            healthy_count = 0
            error_count = 0
            total_agents = len(self._agents)
            
            agent_statuses = {}
            
            for agent_id, agent in self._agents.items():
                status = agent.status
                agent_statuses[agent_id] = {
                    "name": agent.name,
                    "status": status.value,
                    "provider": agent.configuration.provider.value,
                    "model": agent.configuration.model
                }
                
                if status == AgentStatus.READY:
                    healthy_count += 1
                elif status == AgentStatus.ERROR:
                    error_count += 1
            
            return {
                "registry_status": "healthy",
                "total_agents": total_agents,
                "healthy_agents": healthy_count,
                "error_agents": error_count,
                "agents": agent_statuses,
                "timestamp": datetime.now().isoformat()
            }
    
    def cleanup_inactive(self, max_age_hours: int = 24) -> int:
        """
        Clean up inactive agents.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            int: Number of agents cleaned up
        """
        with self._lock:
            current_time = datetime.now()
            cleanup_count = 0
            agents_to_remove = []
            
            for agent_id, metadata in self._metadata.items():
                if metadata.last_used:
                    age = current_time - metadata.last_used
                    if age.total_seconds() > (max_age_hours * 3600):
                        agents_to_remove.append(agent_id)
            
            for agent_id in agents_to_remove:
                if self.unregister(agent_id):
                    cleanup_count += 1
            
            return cleanup_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dict[str, Any]: Registry statistics
        """
        with self._lock:
            total_messages = sum(meta.total_messages for meta in self._metadata.values())
            total_tokens = sum(meta.total_tokens_used for meta in self._metadata.values())
            
            # Provider distribution
            provider_stats = {}
            for agent in self._agents.values():
                provider = agent.configuration.provider.value
                provider_stats[provider] = provider_stats.get(provider, 0) + 1
            
            # Status distribution
            status_stats = {}
            for agent in self._agents.values():
                status = agent.status.value
                status_stats[status] = status_stats.get(status, 0) + 1
            
            return {
                "total_agents": len(self._agents),
                "total_messages": total_messages,
                "total_tokens": total_tokens,
                "provider_distribution": provider_stats,
                "status_distribution": status_stats,
                "timestamp": datetime.now().isoformat()
            }
    
    def clear(self) -> None:
        """Clear all agents from the registry (for testing)"""
        with self._lock:
            # Shutdown all agents
            for agent in self._agents.values():
                if hasattr(agent, 'shutdown'):
                    # Note: This should be async in real implementation
                    pass
            
            self._agents.clear()
            self._metadata.clear()


# Global registry instance
_global_registry = AgentRegistry()


# Convenience functions
def register_agent(agent: IAgent, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Register an agent in the global registry for orchestration.
    
    Args:
        agent: Agent instance to register (must have agent_id attribute)
        metadata: Optional metadata about the agent (capabilities, description, etc.)
        
    Returns:
        bool: True if registration successful, False if agent_id already exists
        
    Raises:
        ValueError: If agent doesn't have an agent_id attribute
        
    Example:
        >>> researcher = await create_openai_agent(name="researcher")
        >>> register_agent(researcher)
        >>> # Agent is now available for workflows
    """
    return _global_registry.register(agent, metadata)


def get_agent(agent_id: str) -> Optional[IAgent]:
    """Get a registered agent by ID from the global registry.
    
    Args:
        agent_id: Unique identifier of the agent
        
    Returns:
        IAgent: The registered agent, or None if not found
        
    Example:
        >>> agent = get_agent("researcher")
        >>> if agent:
        ...     response = await agent.execute("Research quantum computing")
    """
    return _global_registry.get(agent_id)


def get_agent_by_name(name: str) -> Optional[IAgent]:
    """Get a registered agent by name from the global registry.
    
    Args:
        name: Human-readable name of the agent
        
    Returns:
        IAgent: The first agent with matching name, or None if not found
        
    Note:
        Multiple agents can have the same name. This returns the first match.
        Use get_agent() with agent_id for guaranteed unique lookup.
    """
    return _global_registry.get_by_name(name)


def list_agents() -> List[str]:
    """List all registered agent IDs available for orchestration.
    
    Returns:
        List[str]: List of all registered agent IDs
        
    Example:
        >>> agents = list_agents()
        >>> print(f"Available agents: {agents}")
        Available agents: ['researcher', 'summarizer', 'reviewer']
    """
    return _global_registry.list_agents()


def list_agent_info() -> List[Dict[str, Any]]:
    """List detailed information for all registered agents.
    
    Returns:
        List[Dict[str, Any]]: List of agent information dictionaries
        
    Each dictionary contains:
        - agent_id: Unique identifier
        - name: Human-readable name
        - provider: AI provider (openai, anthropic, etc.)
        - capabilities: List of agent capabilities
        - metadata: Additional agent metadata
        
    Example:
        >>> info = list_agent_info()
        >>> for agent in info:
        ...     print(f"{agent['agent_id']}: {agent['name']} ({agent['provider']})")
    """
    return _global_registry.list_agent_info()


def unregister_agent(agent_id: str) -> bool:
    """Unregister an agent from the global registry"""
    return _global_registry.unregister(agent_id)


def agent_health_check() -> Dict[str, Any]:
    """Get health status of all agents"""
    return _global_registry.health_check()


def get_agent_statistics() -> Dict[str, Any]:
    """Get agent registry statistics"""
    return _global_registry.get_statistics()
