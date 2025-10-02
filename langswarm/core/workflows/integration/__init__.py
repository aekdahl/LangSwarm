"""
Advanced Tool & Agent Integration for V2 Workflows

This module provides enhanced integration capabilities between workflows and V2 tool/agent systems:
- Dynamic tool discovery and integration
- Agent workflow orchestration and coordination  
- Tool result caching and optimization
- Agent conversation context preservation
- Load balancing for tools and agents
"""

from .interfaces import (
    # Core interfaces
    IToolDiscovery,
    IAgentCoordinator, 
    IWorkflowCache,
    IContextPreserver,
    ILoadBalancer,
    
    # Data structures
    ToolDescriptor,
    AgentSession,
    CacheEntry,
    ContextSnapshot,
    LoadBalancerConfig,
    
    # Enums
    DiscoveryStrategy,
    CoordinationMode,
    CacheStrategy,
    ContextScope,
    LoadBalancingStrategy,
    
    # Events
    ToolDiscoveryEvent,
    AgentCoordinationEvent,
    CacheEvent,
    ContextEvent,
    LoadBalancingEvent
)

from .implementations import (
    DynamicToolDiscovery,
    AgentCoordinator,
    WorkflowCache,
    ContextPreserver,
    LoadBalancer
)

from .steps import (
    AdvancedAgentStep,
    CachedToolStep,
    CoordinatedAgentStep,
    LoadBalancedStep,
    ContextAwareStep
)

from .factory import create_integration_manager

__all__ = [
    # Interfaces
    "IToolDiscovery",
    "IAgentCoordinator", 
    "IWorkflowCache",
    "IContextPreserver",
    "ILoadBalancer",
    
    # Data structures
    "ToolDescriptor",
    "AgentSession",
    "CacheEntry", 
    "ContextSnapshot",
    "LoadBalancerConfig",
    
    # Enums
    "DiscoveryStrategy",
    "CoordinationMode",
    "CacheStrategy",
    "ContextScope",
    "LoadBalancingStrategy",
    
    # Events
    "ToolDiscoveryEvent",
    "AgentCoordinationEvent",
    "CacheEvent",
    "ContextEvent",
    "LoadBalancingEvent",
    
    # Implementations
    "DynamicToolDiscovery",
    "AgentCoordinator",
    "WorkflowCache",
    "ContextPreserver", 
    "LoadBalancer",
    
    # Enhanced workflow steps
    "AdvancedAgentStep",
    "CachedToolStep",
    "CoordinatedAgentStep",
    "LoadBalancedStep",
    "ContextAwareStep",
    
    # Factory
    "create_integration_manager"
]