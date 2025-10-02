"""
Workflow Request Router

Advanced routing component for workflow requests based on type, complexity,
and resource requirements with load balancing and optimization.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from langswarm.core.middleware import IRequestContext
from .interceptors import WorkflowComplexity, WorkflowRequestType

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Routing strategies for workflow execution"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    COMPLEXITY_BASED = "complexity_based"
    PRIORITY_BASED = "priority_based"
    GEOGRAPHIC = "geographic"
    COST_OPTIMIZED = "cost_optimized"


@dataclass
class ExecutionLane:
    """Execution lane configuration"""
    name: str
    max_concurrent: int
    current_load: int = 0
    avg_execution_time: float = 0.0
    success_rate: float = 100.0
    cost_per_execution: float = 0.0
    geographic_region: Optional[str] = None
    specialized_for: Optional[List[WorkflowComplexity]] = None
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def load_percentage(self) -> float:
        """Calculate current load percentage"""
        return (self.current_load / max(self.max_concurrent, 1)) * 100
    
    @property
    def available_capacity(self) -> int:
        """Calculate available capacity"""
        return max(0, self.max_concurrent - self.current_load)


@dataclass
class RouteConfiguration:
    """Configuration for workflow routing"""
    default_strategy: RoutingStrategy = RoutingStrategy.COMPLEXITY_BASED
    enable_load_balancing: bool = True
    enable_failover: bool = True
    max_queue_size: int = 1000
    routing_timeout: timedelta = timedelta(seconds=30)
    health_check_interval: timedelta = timedelta(minutes=1)
    auto_scaling: bool = True
    cost_optimization: bool = False


class WorkflowRequestRouter:
    """
    Advanced router for workflow requests with intelligent routing strategies.
    
    Features:
    - Multiple routing strategies (round-robin, least-loaded, complexity-based)
    - Load balancing across execution lanes
    - Automatic failover and health monitoring
    - Cost optimization and resource management
    """
    
    def __init__(self, config: Optional[RouteConfiguration] = None):
        """
        Initialize workflow request router.
        
        Args:
            config: Router configuration
        """
        self.config = config or RouteConfiguration()
        self.execution_lanes: Dict[str, ExecutionLane] = {}
        self.routing_stats = {
            "total_routes": 0,
            "successful_routes": 0,
            "failed_routes": 0,
            "avg_routing_time": 0.0
        }
        self._round_robin_index = 0
        self._setup_default_lanes()
        
        logger.info("Initialized WorkflowRequestRouter")
    
    def _setup_default_lanes(self):
        """Setup default execution lanes"""
        
        self.execution_lanes = {
            "fast_lane": ExecutionLane(
                name="fast_lane",
                max_concurrent=100,
                specialized_for=[WorkflowComplexity.SIMPLE],
                resource_limits={"memory": "256MB", "cpu": "0.5"}
            ),
            "standard_lane": ExecutionLane(
                name="standard_lane", 
                max_concurrent=50,
                specialized_for=[WorkflowComplexity.MEDIUM],
                resource_limits={"memory": "512MB", "cpu": "1.0"}
            ),
            "heavy_lane": ExecutionLane(
                name="heavy_lane",
                max_concurrent=20,
                specialized_for=[WorkflowComplexity.COMPLEX],
                resource_limits={"memory": "2GB", "cpu": "2.0"}
            ),
            "enterprise_lane": ExecutionLane(
                name="enterprise_lane",
                max_concurrent=10,
                specialized_for=[WorkflowComplexity.ENTERPRISE],
                resource_limits={"memory": "4GB", "cpu": "4.0"}
            )
        }
    
    async def route_request(
        self, 
        context: IRequestContext,
        complexity: WorkflowComplexity,
        strategy: Optional[RoutingStrategy] = None
    ) -> str:
        """
        Route workflow request to appropriate execution lane.
        
        Args:
            context: Request context
            complexity: Workflow complexity
            strategy: Optional routing strategy override
            
        Returns:
            Name of selected execution lane
        """
        
        start_time = time.time()
        
        try:
            strategy = strategy or self.config.default_strategy
            
            # Get candidate lanes
            candidate_lanes = self._get_candidate_lanes(complexity)
            
            if not candidate_lanes:
                raise ValueError(f"No available lanes for complexity {complexity.value}")
            
            # Apply routing strategy
            selected_lane = await self._apply_routing_strategy(
                candidate_lanes, strategy, context
            )
            
            # Update routing statistics
            routing_time = time.time() - start_time
            await self._update_routing_stats(routing_time, True)
            
            logger.info(f"Routed request to {selected_lane} using {strategy.value} strategy")
            return selected_lane
            
        except Exception as e:
            routing_time = time.time() - start_time
            await self._update_routing_stats(routing_time, False)
            logger.error(f"Failed to route request: {e}")
            raise
    
    def _get_candidate_lanes(self, complexity: WorkflowComplexity) -> List[str]:
        """Get candidate execution lanes for given complexity"""
        
        candidates = []
        
        for lane_name, lane in self.execution_lanes.items():
            # Check if lane is specialized for this complexity
            if lane.specialized_for and complexity in lane.specialized_for:
                candidates.append(lane_name)
            # Or if lane has available capacity and no specialization
            elif not lane.specialized_for and lane.available_capacity > 0:
                candidates.append(lane_name)
        
        # If no specialized lanes, use any available lane
        if not candidates:
            candidates = [
                name for name, lane in self.execution_lanes.items() 
                if lane.available_capacity > 0
            ]
        
        return candidates
    
    async def _apply_routing_strategy(
        self, 
        candidate_lanes: List[str], 
        strategy: RoutingStrategy,
        context: IRequestContext
    ) -> str:
        """Apply routing strategy to select best lane"""
        
        if not candidate_lanes:
            raise ValueError("No candidate lanes available")
        
        if len(candidate_lanes) == 1:
            return candidate_lanes[0]
        
        if strategy == RoutingStrategy.ROUND_ROBIN:
            return self._route_round_robin(candidate_lanes)
        elif strategy == RoutingStrategy.LEAST_LOADED:
            return self._route_least_loaded(candidate_lanes)
        elif strategy == RoutingStrategy.COMPLEXITY_BASED:
            return self._route_complexity_based(candidate_lanes, context)
        elif strategy == RoutingStrategy.PRIORITY_BASED:
            return self._route_priority_based(candidate_lanes, context)
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            return self._route_cost_optimized(candidate_lanes)
        else:
            # Default to least loaded
            return self._route_least_loaded(candidate_lanes)
    
    def _route_round_robin(self, candidate_lanes: List[str]) -> str:
        """Round-robin routing"""
        
        self._round_robin_index = (self._round_robin_index + 1) % len(candidate_lanes)
        return candidate_lanes[self._round_robin_index]
    
    def _route_least_loaded(self, candidate_lanes: List[str]) -> str:
        """Route to least loaded lane"""
        
        best_lane = candidate_lanes[0]
        best_load = self.execution_lanes[best_lane].load_percentage
        
        for lane_name in candidate_lanes[1:]:
            lane_load = self.execution_lanes[lane_name].load_percentage
            if lane_load < best_load:
                best_lane = lane_name
                best_load = lane_load
        
        return best_lane
    
    def _route_complexity_based(self, candidate_lanes: List[str], context: IRequestContext) -> str:
        """Route based on workflow complexity and requirements"""
        
        # Prefer specialized lanes
        for lane_name in candidate_lanes:
            lane = self.execution_lanes[lane_name]
            if lane.specialized_for:
                return lane_name
        
        # Fall back to least loaded
        return self._route_least_loaded(candidate_lanes)
    
    def _route_priority_based(self, candidate_lanes: List[str], context: IRequestContext) -> str:
        """Route based on request priority"""
        
        priority = context.metadata.get("priority", "normal")
        
        if priority == "high":
            # Prefer lanes with better performance
            best_lane = candidate_lanes[0]
            best_performance = self.execution_lanes[best_lane].success_rate
            
            for lane_name in candidate_lanes[1:]:
                lane_performance = self.execution_lanes[lane_name].success_rate
                if lane_performance > best_performance:
                    best_lane = lane_name
                    best_performance = lane_performance
            
            return best_lane
        else:
            # Use least loaded for normal priority
            return self._route_least_loaded(candidate_lanes)
    
    def _route_cost_optimized(self, candidate_lanes: List[str]) -> str:
        """Route to most cost-effective lane"""
        
        best_lane = candidate_lanes[0]
        best_cost = self.execution_lanes[best_lane].cost_per_execution
        
        for lane_name in candidate_lanes[1:]:
            lane_cost = self.execution_lanes[lane_name].cost_per_execution
            if lane_cost < best_cost:
                best_lane = lane_name
                best_cost = lane_cost
        
        return best_lane
    
    async def _update_routing_stats(self, routing_time: float, success: bool):
        """Update routing statistics"""
        
        self.routing_stats["total_routes"] += 1
        
        if success:
            self.routing_stats["successful_routes"] += 1
        else:
            self.routing_stats["failed_routes"] += 1
        
        # Update average routing time
        total_time = (self.routing_stats["avg_routing_time"] * 
                     (self.routing_stats["total_routes"] - 1) + routing_time)
        self.routing_stats["avg_routing_time"] = total_time / self.routing_stats["total_routes"]
    
    def add_execution_lane(self, lane: ExecutionLane):
        """Add new execution lane"""
        
        self.execution_lanes[lane.name] = lane
        logger.info(f"Added execution lane: {lane.name}")
    
    def remove_execution_lane(self, lane_name: str):
        """Remove execution lane"""
        
        if lane_name in self.execution_lanes:
            del self.execution_lanes[lane_name]
            logger.info(f"Removed execution lane: {lane_name}")
    
    def update_lane_load(self, lane_name: str, load_delta: int):
        """Update lane load (positive for increase, negative for decrease)"""
        
        if lane_name in self.execution_lanes:
            lane = self.execution_lanes[lane_name]
            lane.current_load = max(0, lane.current_load + load_delta)
    
    def update_lane_metrics(
        self, 
        lane_name: str, 
        execution_time: float, 
        success: bool
    ):
        """Update lane performance metrics"""
        
        if lane_name not in self.execution_lanes:
            return
        
        lane = self.execution_lanes[lane_name]
        
        # Update average execution time
        if lane.avg_execution_time == 0:
            lane.avg_execution_time = execution_time
        else:
            lane.avg_execution_time = (lane.avg_execution_time * 0.9 + execution_time * 0.1)
        
        # Update success rate
        if success:
            lane.success_rate = min(100.0, lane.success_rate * 0.99 + 1.0)
        else:
            lane.success_rate = max(0.0, lane.success_rate * 0.99)
    
    def get_router_stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        
        lane_stats = {}
        for name, lane in self.execution_lanes.items():
            lane_stats[name] = {
                "max_concurrent": lane.max_concurrent,
                "current_load": lane.current_load,
                "load_percentage": lane.load_percentage,
                "available_capacity": lane.available_capacity,
                "avg_execution_time": lane.avg_execution_time,
                "success_rate": lane.success_rate,
                "cost_per_execution": lane.cost_per_execution
            }
        
        return {
            "routing_stats": self.routing_stats,
            "execution_lanes": lane_stats,
            "total_capacity": sum(lane.max_concurrent for lane in self.execution_lanes.values()),
            "total_load": sum(lane.current_load for lane in self.execution_lanes.values()),
            "overall_load_percentage": (
                sum(lane.current_load for lane in self.execution_lanes.values()) /
                max(sum(lane.max_concurrent for lane in self.execution_lanes.values()), 1)
            ) * 100
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on router and lanes"""
        
        health_status = {
            "router_healthy": True,
            "total_lanes": len(self.execution_lanes),
            "healthy_lanes": 0,
            "lane_health": {}
        }
        
        for name, lane in self.execution_lanes.items():
            lane_healthy = (
                lane.success_rate > 50.0 and
                lane.load_percentage < 95.0
            )
            
            health_status["lane_health"][name] = {
                "healthy": lane_healthy,
                "success_rate": lane.success_rate,
                "load_percentage": lane.load_percentage,
                "available_capacity": lane.available_capacity
            }
            
            if lane_healthy:
                health_status["healthy_lanes"] += 1
        
        # Router is healthy if at least one lane is healthy
        health_status["router_healthy"] = health_status["healthy_lanes"] > 0
        
        return health_status


def create_workflow_router(config: Optional[RouteConfiguration] = None) -> WorkflowRequestRouter:
    """Create workflow request router with configuration"""
    
    return WorkflowRequestRouter(config)


def create_development_router() -> WorkflowRequestRouter:
    """Create development-friendly router with relaxed limits"""
    
    config = RouteConfiguration(
        default_strategy=RoutingStrategy.ROUND_ROBIN,
        enable_load_balancing=True,
        enable_failover=False,
        max_queue_size=100,
        auto_scaling=False
    )
    
    router = WorkflowRequestRouter(config)
    
    # Add development-friendly lanes
    router.add_execution_lane(ExecutionLane(
        name="dev_fast",
        max_concurrent=20,
        specialized_for=[WorkflowComplexity.SIMPLE, WorkflowComplexity.MEDIUM]
    ))
    
    router.add_execution_lane(ExecutionLane(
        name="dev_standard", 
        max_concurrent=10,
        specialized_for=[WorkflowComplexity.COMPLEX, WorkflowComplexity.ENTERPRISE]
    ))
    
    return router


def create_production_router() -> WorkflowRequestRouter:
    """Create production-ready router with high availability"""
    
    config = RouteConfiguration(
        default_strategy=RoutingStrategy.LEAST_LOADED,
        enable_load_balancing=True,
        enable_failover=True,
        max_queue_size=5000,
        auto_scaling=True,
        cost_optimization=True
    )
    
    return WorkflowRequestRouter(config)
