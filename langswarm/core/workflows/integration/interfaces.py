"""
Advanced Tool & Agent Integration Interfaces for V2 Workflows

Interfaces for enhanced integration capabilities between workflows and V2 systems.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Callable, AsyncIterator, Tuple

from ..interfaces import WorkflowContext, StepResult


class DiscoveryStrategy(Enum):
    """Tool discovery strategies"""
    AUTOMATIC = "automatic"      # Automatic discovery based on context
    ON_DEMAND = "on_demand"     # Discovery when tools are needed
    PRE_LOADED = "pre_loaded"   # Tools loaded at workflow startup
    ADAPTIVE = "adaptive"        # Machine learning-based discovery
    SEMANTIC = "semantic"        # Semantic matching of tool capabilities


class CoordinationMode(Enum):
    """Agent coordination modes"""
    SEQUENTIAL = "sequential"    # Agents execute sequentially
    PARALLEL = "parallel"       # Agents execute in parallel
    HIERARCHICAL = "hierarchical"  # Master-worker coordination
    CONSENSUS = "consensus"      # Consensus-based decision making
    COLLABORATIVE = "collaborative"  # Collaborative problem solving


class CacheStrategy(Enum):
    """Caching strategies for tool results"""
    LRU = "lru"                 # Least recently used
    LFU = "lfu"                 # Least frequently used
    TTL = "ttl"                 # Time-to-live based
    SEMANTIC = "semantic"       # Semantic similarity based
    ADAPTIVE = "adaptive"       # Machine learning-based
    CUSTOM = "custom"           # Custom caching logic


class ContextScope(Enum):
    """Context preservation scope"""
    STEP = "step"               # Single step context
    WORKFLOW = "workflow"       # Entire workflow context
    SESSION = "session"         # Agent session context
    GLOBAL = "global"          # Global context across workflows
    USER = "user"              # User-specific context


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"  # Round robin distribution
    LEAST_CONNECTIONS = "least_connections"  # Least active connections
    WEIGHTED = "weighted"        # Weighted distribution
    PERFORMANCE = "performance"  # Performance-based routing
    RESOURCE_USAGE = "resource_usage"  # Resource usage-based
    GEOGRAPHIC = "geographic"    # Geographic proximity-based


@dataclass
class ToolDescriptor:
    """Descriptor for discovered tools"""
    tool_id: str
    tool_name: str
    tool_type: str
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Performance characteristics
    avg_execution_time: Optional[float] = None
    success_rate: float = 1.0
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    
    # Discovery information
    discovery_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    discovery_method: Optional[str] = None
    confidence_score: float = 1.0
    
    # Integration details
    interface_version: str = "v2"
    compatibility_score: float = 1.0
    health_status: str = "healthy"


@dataclass
class AgentSession:
    """Agent session for coordination"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    user_id: Optional[str] = None
    workflow_id: Optional[str] = None
    
    # Session state
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "active"
    
    # Conversation state
    message_count: int = 0
    context_tokens: int = 0
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Coordination metadata
    coordination_role: Optional[str] = None
    parent_session: Optional[str] = None
    child_sessions: List[str] = field(default_factory=list)
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)


@dataclass
class CacheEntry:
    """Cache entry for tool results"""
    cache_key: str
    tool_id: str
    input_data: Dict[str, Any]
    result_data: Any
    
    # Cache metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    
    # Semantic metadata for similarity matching
    input_hash: Optional[str] = None
    semantic_embedding: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    
    # Quality metrics
    confidence_score: float = 1.0
    freshness_score: float = 1.0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if not self.ttl_seconds:
            return False
        
        elapsed = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds
    
    def update_access(self) -> None:
        """Update access statistics"""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1


@dataclass
class ContextSnapshot:
    """Snapshot of agent conversation context"""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_session_id: str = ""
    workflow_execution_id: str = ""
    step_id: str = ""
    
    # Context data
    messages: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Snapshot metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scope: ContextScope = ContextScope.STEP
    compression_ratio: float = 1.0
    
    # Quality metrics
    completeness_score: float = 1.0
    relevance_score: float = 1.0


@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    weights: Dict[str, float] = field(default_factory=dict)
    health_check_interval: int = 30
    failure_threshold: int = 3
    recovery_time: int = 60
    
    # Performance-based routing
    performance_window: int = 300  # 5 minutes
    resource_weight: float = 0.5
    latency_weight: float = 0.3
    success_rate_weight: float = 0.2


@dataclass
class ToolDiscoveryEvent:
    """Event for tool discovery"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "tool_discovered"
    tool_descriptor: ToolDescriptor = None
    workflow_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCoordinationEvent:
    """Event for agent coordination"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "coordination_update"
    session_id: str = ""
    coordination_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CacheEvent:
    """Event for cache operations"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "cache_hit"  # cache_hit, cache_miss, cache_evict
    cache_key: str = ""
    tool_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextEvent:
    """Event for context operations"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "context_saved"  # context_saved, context_restored
    snapshot_id: str = ""
    agent_session_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class LoadBalancingEvent:
    """Event for load balancing operations"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "route_selected"
    target_id: str = ""
    strategy_used: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    decision_factors: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class IToolDiscovery(ABC):
    """Interface for dynamic tool discovery and integration"""
    
    @abstractmethod
    async def discover_tools(
        self,
        context: WorkflowContext,
        required_capabilities: Optional[List[str]] = None,
        strategy: DiscoveryStrategy = DiscoveryStrategy.AUTOMATIC
    ) -> List[ToolDescriptor]:
        """Discover tools based on workflow context and requirements"""
        pass
    
    @abstractmethod
    async def register_tool(self, tool_descriptor: ToolDescriptor) -> bool:
        """Register a discovered tool for use in workflows"""
        pass
    
    @abstractmethod
    async def unregister_tool(self, tool_id: str) -> bool:
        """Unregister a tool"""
        pass
    
    @abstractmethod
    async def get_tool_descriptor(self, tool_id: str) -> Optional[ToolDescriptor]:
        """Get tool descriptor by ID"""
        pass
    
    @abstractmethod
    async def find_tools_by_capability(self, capability: str) -> List[ToolDescriptor]:
        """Find tools that provide specific capability"""
        pass
    
    @abstractmethod
    async def update_tool_metrics(
        self,
        tool_id: str,
        execution_time: float,
        success: bool,
        resource_usage: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update tool performance metrics"""
        pass
    
    @abstractmethod
    async def get_discovery_metrics(self) -> Dict[str, Any]:
        """Get tool discovery performance metrics"""
        pass


class IAgentCoordinator(ABC):
    """Interface for agent workflow orchestration and coordination"""
    
    @abstractmethod
    async def create_session(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        coordination_mode: CoordinationMode = CoordinationMode.SEQUENTIAL
    ) -> AgentSession:
        """Create a new agent session for workflow coordination"""
        pass
    
    @abstractmethod
    async def coordinate_agents(
        self,
        sessions: List[AgentSession],
        task: Dict[str, Any],
        mode: CoordinationMode = CoordinationMode.COLLABORATIVE
    ) -> Dict[str, Any]:
        """Coordinate multiple agents for a task"""
        pass
    
    @abstractmethod
    async def distribute_work(
        self,
        work_items: List[Dict[str, Any]],
        available_sessions: List[AgentSession],
        distribution_strategy: str = "balanced"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Distribute work items across available agent sessions"""
        pass
    
    @abstractmethod
    async def synchronize_agents(
        self,
        sessions: List[AgentSession],
        checkpoint_data: Dict[str, Any]
    ) -> bool:
        """Synchronize agent states at a checkpoint"""
        pass
    
    @abstractmethod
    async def handle_agent_failure(
        self,
        failed_session: AgentSession,
        recovery_strategy: str = "reassign"
    ) -> bool:
        """Handle agent failure and implement recovery strategy"""
        pass
    
    @abstractmethod
    async def get_coordination_status(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Get coordination status for a workflow"""
        pass


class IWorkflowCache(ABC):
    """Interface for tool result caching and optimization"""
    
    @abstractmethod
    async def get_cached_result(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        similarity_threshold: float = 0.9
    ) -> Optional[CacheEntry]:
        """Get cached result for tool execution"""
        pass
    
    @abstractmethod
    async def store_result(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        result_data: Any,
        ttl_seconds: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Store tool execution result in cache"""
        pass
    
    @abstractmethod
    async def invalidate_cache(
        self,
        cache_key: Optional[str] = None,
        tool_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """Invalidate cache entries"""
        pass
    
    @abstractmethod
    async def optimize_cache(
        self,
        strategy: CacheStrategy = CacheStrategy.LRU,
        target_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Optimize cache based on strategy"""
        pass
    
    @abstractmethod
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        pass
    
    @abstractmethod
    async def warm_cache(
        self,
        tool_id: str,
        common_inputs: List[Dict[str, Any]]
    ) -> int:
        """Warm cache with common tool inputs"""
        pass


class IContextPreserver(ABC):
    """Interface for agent conversation context preservation"""
    
    @abstractmethod
    async def save_context(
        self,
        agent_session_id: str,
        workflow_execution_id: str,
        step_id: str,
        context_data: Dict[str, Any],
        scope: ContextScope = ContextScope.STEP
    ) -> str:
        """Save agent conversation context"""
        pass
    
    @abstractmethod
    async def restore_context(
        self,
        snapshot_id: str,
        merge_strategy: str = "replace"
    ) -> Optional[ContextSnapshot]:
        """Restore agent conversation context"""
        pass
    
    @abstractmethod
    async def get_context_history(
        self,
        agent_session_id: str,
        limit: int = 50
    ) -> List[ContextSnapshot]:
        """Get context history for an agent session"""
        pass
    
    @abstractmethod
    async def compress_context(
        self,
        snapshot_id: str,
        compression_ratio: float = 0.5,
        preserve_important: bool = True
    ) -> str:
        """Compress context to reduce storage size"""
        pass
    
    @abstractmethod
    async def merge_contexts(
        self,
        snapshot_ids: List[str],
        merge_strategy: str = "union"
    ) -> str:
        """Merge multiple context snapshots"""
        pass
    
    @abstractmethod
    async def cleanup_expired_contexts(
        self,
        max_age_hours: int = 24
    ) -> int:
        """Clean up expired context snapshots"""
        pass


class ILoadBalancer(ABC):
    """Interface for tool and agent load balancing"""
    
    @abstractmethod
    async def select_target(
        self,
        targets: List[str],
        request_context: Dict[str, Any],
        config: Optional[LoadBalancerConfig] = None
    ) -> Optional[str]:
        """Select target for load balancing"""
        pass
    
    @abstractmethod
    async def update_target_health(
        self,
        target_id: str,
        health_score: float,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update target health and performance metrics"""
        pass
    
    @abstractmethod
    async def remove_unhealthy_targets(
        self,
        health_threshold: float = 0.5
    ) -> List[str]:
        """Remove unhealthy targets from load balancing pool"""
        pass
    
    @abstractmethod
    async def get_target_statistics(
        self,
        target_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific target"""
        pass
    
    @abstractmethod
    async def get_load_balancing_metrics(self) -> Dict[str, Any]:
        """Get overall load balancing metrics"""
        pass
    
    @abstractmethod
    async def rebalance_load(
        self,
        force_rebalance: bool = False
    ) -> Dict[str, Any]:
        """Trigger load rebalancing"""
        pass


class IIntegrationManager(ABC):
    """Interface for managing all integration components"""
    
    @property
    @abstractmethod
    def tool_discovery(self) -> IToolDiscovery:
        """Get tool discovery component"""
        pass
    
    @property
    @abstractmethod
    def agent_coordinator(self) -> IAgentCoordinator:
        """Get agent coordinator component"""
        pass
    
    @property
    @abstractmethod
    def workflow_cache(self) -> IWorkflowCache:
        """Get workflow cache component"""
        pass
    
    @property
    @abstractmethod
    def context_preserver(self) -> IContextPreserver:
        """Get context preserver component"""
        pass
    
    @property
    @abstractmethod
    def load_balancer(self) -> ILoadBalancer:
        """Get load balancer component"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize all integration components"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown all integration components"""
        pass
    
    @abstractmethod
    async def get_system_health(self) -> Dict[str, Any]:
        """Get health status of all integration components"""
        pass


# Type aliases for convenience
ToolFilter = Callable[[ToolDescriptor], bool]
AgentSelector = Callable[[List[AgentSession]], AgentSession]
CacheKeyGenerator = Callable[[str, Dict[str, Any]], str]
ContextCompressor = Callable[[Dict[str, Any]], Dict[str, Any]]
LoadBalancingDecision = Tuple[str, float]  # (target_id, confidence_score)