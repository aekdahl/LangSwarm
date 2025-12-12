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
        metadata: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None
    ) -> bool:
        """
        Register an agent in the registry.
        
        Args:
            agent: The agent instance to register
            metadata: Optional metadata about the agent (description, tags, etc.)
            parent_id: Optional ID of parent agent (for sub-agents/hierarchy)
            
        Returns:
            bool: True if registration was successful
        """
        with self._lock:
            try:
                agent_id = agent.agent_id
                
                # Check if agent is already registered
                if agent_id in self._agents:
                    raise ValueError(f"Agent {agent_id} is already registered")
                
                # Validate parent_id if provided
                effective_parent_id = parent_id or (metadata.get('parent_id') if metadata else None)
                if effective_parent_id and effective_parent_id not in self._agents:
                    raise ValueError(f"Parent agent '{effective_parent_id}' is not registered")
                
                # Store agent and metadata
                self._agents[agent_id] = agent
                
                # Create or update metadata
                if agent_id not in self._metadata:
                    self._metadata[agent_id] = AgentMetadata(
                        agent_id=agent_id,
                        name=agent.name,
                        description=metadata.get('description') if metadata else None,
                        tags=metadata.get('tags', []) if metadata else [],
                        parent_id=effective_parent_id
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
    
    # === Hierarchy Methods ===
    
    def get_children(self, agent_id: str) -> List[IAgent]:
        """
        Get all child agents of a parent agent.
        
        Args:
            agent_id: The parent agent ID
            
        Returns:
            List[IAgent]: List of child agent instances
        """
        with self._lock:
            children = []
            for child_id, metadata in self._metadata.items():
                if metadata.parent_id == agent_id:
                    agent = self._agents.get(child_id)
                    if agent:
                        children.append(agent)
            return children
    
    def get_children_ids(self, agent_id: str) -> List[str]:
        """
        Get IDs of all child agents.
        
        Args:
            agent_id: The parent agent ID
            
        Returns:
            List[str]: List of child agent IDs
        """
        with self._lock:
            return [
                child_id for child_id, metadata in self._metadata.items()
                if metadata.parent_id == agent_id
            ]
    
    def get_parent(self, agent_id: str) -> Optional[IAgent]:
        """
        Get the parent agent of an agent.
        
        Args:
            agent_id: The agent ID
            
        Returns:
            Optional[IAgent]: The parent agent if it exists
        """
        with self._lock:
            metadata = self._metadata.get(agent_id)
            if metadata and metadata.parent_id:
                return self._agents.get(metadata.parent_id)
            return None
    
    def get_ancestors(self, agent_id: str) -> List[IAgent]:
        """
        Get all ancestor agents (parent, grandparent, etc.).
        
        Args:
            agent_id: The agent ID
            
        Returns:
            List[IAgent]: List of ancestor agents from immediate parent to root
        """
        with self._lock:
            ancestors = []
            current_id = agent_id
            visited = set()  # Prevent infinite loops
            
            while current_id and current_id not in visited:
                visited.add(current_id)
                metadata = self._metadata.get(current_id)
                if metadata and metadata.parent_id:
                    parent = self._agents.get(metadata.parent_id)
                    if parent:
                        ancestors.append(parent)
                    current_id = metadata.parent_id
                else:
                    break
            
            return ancestors
    
    def get_descendants(self, agent_id: str) -> List[IAgent]:
        """
        Get all descendant agents (children, grandchildren, etc.).
        
        Args:
            agent_id: The agent ID
            
        Returns:
            List[IAgent]: List of all descendant agents
        """
        with self._lock:
            descendants = []
            queue = [agent_id]
            visited = set()
            
            while queue:
                current_id = queue.pop(0)
                if current_id in visited:
                    continue
                visited.add(current_id)
                
                for child_id, metadata in self._metadata.items():
                    if metadata.parent_id == current_id:
                        agent = self._agents.get(child_id)
                        if agent:
                            descendants.append(agent)
                        queue.append(child_id)
            
            return descendants
    
    def get_root_agents(self) -> List[IAgent]:
        """
        Get all root agents (agents with no parent).
        
        Returns:
            List[IAgent]: List of root agent instances
        """
        with self._lock:
            roots = []
            for agent_id, metadata in self._metadata.items():
                if metadata.parent_id is None:
                    agent = self._agents.get(agent_id)
                    if agent:
                        roots.append(agent)
            return roots
    
    def get_hierarchy(self) -> Dict[str, Any]:
        """
        Get the full agent hierarchy as a tree structure.
        
        Returns:
            Dict[str, Any]: Tree structure with agent info and children
        """
        with self._lock:
            def build_tree(agent_id: str) -> Dict[str, Any]:
                agent = self._agents.get(agent_id)
                metadata = self._metadata.get(agent_id)
                if not agent or not metadata:
                    return {}
                
                children_ids = self.get_children_ids(agent_id)
                
                return {
                    "id": agent_id,
                    "name": agent.name,
                    "provider": agent.configuration.provider.value,
                    "model": agent.configuration.model,
                    "description": metadata.description,
                    "children": [build_tree(child_id) for child_id in children_ids]
                }
            
            # Build trees for all root agents
            roots = []
            for agent_id, metadata in self._metadata.items():
                if metadata.parent_id is None:
                    roots.append(build_tree(agent_id))
            
            return {"agents": roots, "total_agents": len(self._agents)}
    
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
    
    def export_configurations(self) -> List[Dict[str, Any]]:
        """
        Export all agent configurations for persistence.
        
        Returns:
            List[Dict[str, Any]]: List of agent configurations that can be saved
        """
        with self._lock:
            configurations = []
            
            for agent_id, agent in self._agents.items():
                metadata = self._metadata.get(agent_id)
                
                # Extract configuration from agent
                config = agent.configuration
                
                agent_config = {
                    "id": agent_id,
                    "name": agent.name,
                    "provider": config.provider.value,
                    "model": config.model,
                    "system_prompt": config.system_prompt,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "tools_enabled": config.tools_enabled,
                    "available_tools": config.available_tools,
                    "memory_enabled": config.memory_enabled,
                    "streaming_enabled": config.streaming_enabled,
                    "provider_config": config.provider_config,
                }
                
                # Add metadata if available
                if metadata:
                    agent_config["metadata"] = {
                        "description": metadata.description,
                        "tags": metadata.tags,
                    }
                
                configurations.append(agent_config)
            
            return configurations
    
    def save(self, filepath: str) -> bool:
        """
        Save registry configurations to a file.
        
        Args:
            filepath: Path to save the configurations (supports .yaml, .yml, .json)
            
        Returns:
            bool: True if save was successful
        """
        import os
        import json
        
        try:
            configurations = self.export_configurations()
            
            # Determine format based on extension
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext in ['.yaml', '.yml']:
                import yaml
                with open(filepath, 'w') as f:
                    yaml.dump({"agents": configurations}, f, default_flow_style=False, sort_keys=False)
            elif ext == '.json':
                with open(filepath, 'w') as f:
                    json.dump({"agents": configurations}, f, indent=2)
            else:
                # Default to YAML
                import yaml
                with open(filepath, 'w') as f:
                    yaml.dump({"agents": configurations}, f, default_flow_style=False, sort_keys=False)
            
            print(f"✅ Saved {len(configurations)} agent configurations to {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save registry: {e}")
            return False


# Global registry instance
_global_registry = AgentRegistry()


# Convenience functions
def register_agent(
    agent: IAgent, 
    metadata: Optional[Dict[str, Any]] = None,
    parent_id: Optional[str] = None
) -> bool:
    """Register an agent in the global registry for orchestration.
    
    Args:
        agent: Agent instance to register (must have agent_id attribute)
        metadata: Optional metadata about the agent (capabilities, description, etc.)
        parent_id: Optional ID of parent agent for hierarchy
        
    Returns:
        bool: True if registration successful, False if agent_id already exists
        
    Raises:
        ValueError: If agent doesn't have an agent_id attribute
        
    Example:
        >>> # Register a root agent
        >>> supervisor = await AgentBuilder().openai().name("supervisor").build()
        >>> register_agent(supervisor)
        >>> 
        >>> # Register a sub-agent with parent
        >>> worker = await AgentBuilder().openai().name("worker").build()
        >>> register_agent(worker, parent_id="supervisor")
    """
    return _global_registry.register(agent, metadata, parent_id)


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


def export_registry() -> List[Dict[str, Any]]:
    """
    Export all agent configurations as a list of dictionaries.
    
    Use this to persist agents to any storage backend (Firestore, MongoDB, Redis, etc.).
    
    Returns:
        List[Dict[str, Any]]: List of agent configurations ready to be serialized
        
    Example:
        >>> # Export to Firestore
        >>> configs = export_registry()
        >>> for config in configs:
        ...     db.collection('agents').document(config['id']).set(config)
        
        >>> # Export to JSON string
        >>> import json
        >>> json_str = json.dumps(export_registry())
        
        >>> # Export to Redis
        >>> redis.set('agent_configs', json.dumps(export_registry()))
    """
    return _global_registry.export_configurations()


async def import_registry(
    configurations: List[Dict[str, Any]], 
    clear_existing: bool = False
) -> int:
    """
    Import agent configurations from a list of dictionaries.
    
    Use this to restore agents from any storage backend (Firestore, MongoDB, Redis, etc.).
    
    Args:
        configurations: List of agent configuration dictionaries
        clear_existing: If True, clear existing agents before importing
        
    Returns:
        int: Number of agents successfully imported
        
    Example:
        >>> # Import from Firestore
        >>> configs = [doc.to_dict() for doc in db.collection('agents').stream()]
        >>> count = await import_registry(configs)
        
        >>> # Import from Redis
        >>> import json
        >>> configs = json.loads(redis.get('agent_configs'))
        >>> count = await import_registry(configs)
    """
    from .builder import AgentBuilder
    
    if clear_existing:
        _global_registry.clear()
    
    loaded_count = 0
    
    for agent_config in configurations:
        try:
            builder = AgentBuilder()
            
            # Set provider
            provider = agent_config.get('provider', 'litellm')
            if provider == 'openai':
                builder.openai()
            elif provider == 'anthropic':
                builder.anthropic()
            elif provider == 'gemini':
                builder.gemini()
            elif provider == 'mistral':
                builder.mistral()
            else:
                builder.litellm()
            
            if agent_config.get('model'):
                builder.model(agent_config['model'])
            if agent_config.get('name'):
                builder.name(agent_config['name'])
            if agent_config.get('system_prompt'):
                builder.system_prompt(agent_config['system_prompt'])
            if agent_config.get('temperature') is not None:
                builder.temperature(agent_config['temperature'])
            if agent_config.get('max_tokens') is not None:
                builder.max_tokens(agent_config['max_tokens'])
            if agent_config.get('tools_enabled') and agent_config.get('available_tools'):
                builder.tools(agent_config['available_tools'])
            if agent_config.get('memory_enabled'):
                builder.memory()
            if agent_config.get('streaming_enabled'):
                builder.streaming()
            
            agent = await builder.build()
            
            metadata = agent_config.get('metadata', {})
            parent_id = agent_config.get('parent_id') or metadata.get('parent_id')
            
            _global_registry.register(agent, metadata, parent_id)
            loaded_count += 1
            
        except Exception as e:
            print(f"⚠️ Failed to import agent '{agent_config.get('id', 'unknown')}': {e}")
    
    print(f"✅ Imported {loaded_count} agents")
    return loaded_count


def save_registry(filepath: str) -> bool:
    """
    Save all registered agent configurations to a file.
    
    This allows you to persist agents created programmatically and restore
    them on application restart.
    
    Args:
        filepath: Path to save configurations to (supports .yaml, .yml, .json)
        
    Returns:
        bool: True if save was successful
        
    Example:
        >>> # Create agents programmatically
        >>> researcher = await AgentBuilder().openai().name("researcher").build()
        >>> summarizer = await AgentBuilder().anthropic().name("summarizer").build()
        >>> 
        >>> # Register them
        >>> register_agent(researcher)
        >>> register_agent(summarizer)
        >>> 
        >>> # Save for later
        >>> save_registry("my_agents.yaml")
        ✅ Saved 2 agent configurations to my_agents.yaml
    """
    return _global_registry.save(filepath)


async def load_registry(filepath: str, clear_existing: bool = False) -> int:
    """
    Load agent configurations from a file and recreate agents.
    
    This restores agents that were previously saved with save_registry().
    
    Args:
        filepath: Path to load configurations from (supports .yaml, .yml, .json)
        clear_existing: If True, clear existing agents before loading
        
    Returns:
        int: Number of agents successfully loaded
        
    Example:
        >>> # On application startup
        >>> count = await load_registry("my_agents.yaml")
        ✅ Loaded 2 agents from my_agents.yaml
        >>> 
        >>> # Now agents are available
        >>> researcher = get_agent("researcher")
        >>> response = await researcher.chat("Hello!")
    """
    import os
    import json
    
    try:
        if clear_existing:
            _global_registry.clear()
        
        # Determine format based on extension
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext in ['.yaml', '.yml']:
            import yaml
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
        elif ext == '.json':
            with open(filepath, 'r') as f:
                data = json.load(f)
        else:
            # Default to YAML
            import yaml
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
        
        agents_config = data.get('agents', [])
        loaded_count = 0
        
        # Import AgentBuilder here to avoid circular imports
        from .builder import AgentBuilder
        
        for agent_config in agents_config:
            try:
                # Build agent from configuration
                builder = AgentBuilder()
                
                # Set provider
                provider = agent_config.get('provider', 'litellm')
                if provider == 'openai':
                    builder.openai()
                elif provider == 'anthropic':
                    builder.anthropic()
                elif provider == 'gemini':
                    builder.gemini()
                elif provider == 'mistral':
                    builder.mistral()
                else:
                    builder.litellm()
                
                # Set model
                if agent_config.get('model'):
                    builder.model(agent_config['model'])
                
                # Set name
                if agent_config.get('name'):
                    builder.name(agent_config['name'])
                
                # Set system prompt
                if agent_config.get('system_prompt'):
                    builder.system_prompt(agent_config['system_prompt'])
                
                # Set temperature
                if agent_config.get('temperature') is not None:
                    builder.temperature(agent_config['temperature'])
                
                # Set max tokens
                if agent_config.get('max_tokens') is not None:
                    builder.max_tokens(agent_config['max_tokens'])
                
                # Set tools
                if agent_config.get('tools_enabled') and agent_config.get('available_tools'):
                    builder.tools(agent_config['available_tools'])
                
                # Set memory
                if agent_config.get('memory_enabled'):
                    builder.memory()
                
                # Set streaming
                if agent_config.get('streaming_enabled'):
                    builder.streaming()
                
                # Build and register
                agent = await builder.build()
                
                # Get metadata from config
                metadata = agent_config.get('metadata', {})
                
                _global_registry.register(agent, metadata)
                loaded_count += 1
                
            except Exception as e:
                print(f"⚠️ Failed to load agent '{agent_config.get('id', 'unknown')}': {e}")
        
        print(f"✅ Loaded {loaded_count} agents from {filepath}")
        return loaded_count
        
    except Exception as e:
        print(f"❌ Failed to load registry from {filepath}: {e}")
        return 0


# === Hierarchy Convenience Functions ===

def get_agent_children(agent_id: str) -> List[IAgent]:
    """Get all child agents of a parent agent."""
    return _global_registry.get_children(agent_id)


def get_agent_parent(agent_id: str) -> Optional[IAgent]:
    """Get the parent agent of an agent."""
    return _global_registry.get_parent(agent_id)


def get_agent_hierarchy() -> Dict[str, Any]:
    """
    Get the full agent hierarchy as a tree structure.
    
    Example:
        >>> hierarchy = get_agent_hierarchy()
        >>> print(json.dumps(hierarchy, indent=2))
        {
          "agents": [
            {
              "id": "supervisor",
              "name": "Supervisor",
              "children": [
                {"id": "worker1", "name": "Worker 1", "children": []},
                {"id": "worker2", "name": "Worker 2", "children": []}
              ]
            }
          ],
          "total_agents": 3
        }
    """
    return _global_registry.get_hierarchy()


def get_root_agents() -> List[IAgent]:
    """Get all root agents (agents with no parent)."""
    return _global_registry.get_root_agents()
