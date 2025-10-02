"""
Integration Manager Factory for V2 Workflows

Factory functions to create and configure integration components
for enhanced tool and agent integration within workflows.
"""

import logging
from typing import Dict, Any, Optional

from .interfaces import (
    IIntegrationManager, DiscoveryStrategy, CoordinationMode,
    CacheStrategy, ContextScope, LoadBalancingStrategy,
    LoadBalancerConfig
)
from .implementations import (
    DynamicToolDiscovery, AgentCoordinator, WorkflowCache,
    ContextPreserver, LoadBalancer
)

logger = logging.getLogger(__name__)


class IntegrationManager(IIntegrationManager):
    """Concrete implementation of integration manager"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._tool_discovery: Optional[DynamicToolDiscovery] = None
        self._agent_coordinator: Optional[AgentCoordinator] = None
        self._workflow_cache: Optional[WorkflowCache] = None
        self._context_preserver: Optional[ContextPreserver] = None
        self._load_balancer: Optional[LoadBalancer] = None
        self._initialized = False
    
    @property
    def tool_discovery(self) -> DynamicToolDiscovery:
        """Get tool discovery component"""
        if not self._tool_discovery:
            raise RuntimeError("Integration manager not initialized")
        return self._tool_discovery
    
    @property
    def agent_coordinator(self) -> AgentCoordinator:
        """Get agent coordinator component"""
        if not self._agent_coordinator:
            raise RuntimeError("Integration manager not initialized")
        return self._agent_coordinator
    
    @property
    def workflow_cache(self) -> WorkflowCache:
        """Get workflow cache component"""
        if not self._workflow_cache:
            raise RuntimeError("Integration manager not initialized")
        return self._workflow_cache
    
    @property
    def context_preserver(self) -> ContextPreserver:
        """Get context preserver component"""
        if not self._context_preserver:
            raise RuntimeError("Integration manager not initialized")
        return self._context_preserver
    
    @property
    def load_balancer(self) -> LoadBalancer:
        """Get load balancer component"""
        if not self._load_balancer:
            raise RuntimeError("Integration manager not initialized")
        return self._load_balancer
    
    async def initialize(self) -> bool:
        """Initialize all integration components"""
        if self._initialized:
            return True
        
        try:
            # Initialize tool discovery
            discovery_config = self.config.get("tool_discovery", {})
            self._tool_discovery = DynamicToolDiscovery(discovery_config)
            await self._tool_discovery.initialize()
            
            # Initialize agent coordinator
            coordinator_config = self.config.get("agent_coordinator", {})
            self._agent_coordinator = AgentCoordinator(coordinator_config)
            await self._agent_coordinator.initialize()
            
            # Initialize workflow cache
            cache_config = self.config.get("workflow_cache", {})
            self._workflow_cache = WorkflowCache(cache_config)
            await self._workflow_cache.initialize()
            
            # Initialize context preserver
            context_config = self.config.get("context_preserver", {})
            self._context_preserver = ContextPreserver(context_config)
            await self._context_preserver.initialize()
            
            # Initialize load balancer
            load_balancer_config = self.config.get("load_balancer", {})
            balancer_config = LoadBalancerConfig(
                strategy=LoadBalancingStrategy(
                    load_balancer_config.get("strategy", "round_robin")
                ),
                weights=load_balancer_config.get("weights", {}),
                health_check_interval=load_balancer_config.get("health_check_interval", 30),
                failure_threshold=load_balancer_config.get("failure_threshold", 3),
                recovery_time=load_balancer_config.get("recovery_time", 60)
            )
            self._load_balancer = LoadBalancer(balancer_config)
            await self._load_balancer.initialize()
            
            self._initialized = True
            logger.info("Integration manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize integration manager: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown all integration components"""
        if not self._initialized:
            return True
        
        try:
            shutdown_results = []
            
            # Shutdown all components
            if self._tool_discovery:
                shutdown_results.append(await self._tool_discovery.shutdown())
            
            if self._agent_coordinator:
                shutdown_results.append(await self._agent_coordinator.shutdown())
            
            if self._workflow_cache:
                shutdown_results.append(await self._workflow_cache.shutdown())
            
            if self._context_preserver:
                shutdown_results.append(await self._context_preserver.shutdown())
            
            if self._load_balancer:
                shutdown_results.append(await self._load_balancer.shutdown())
            
            # Check if all shutdowns were successful
            success = all(shutdown_results)
            
            if success:
                self._initialized = False
                logger.info("Integration manager shutdown successfully")
            else:
                logger.warning("Some components failed to shutdown properly")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to shutdown integration manager: {e}")
            return False
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get health status of all integration components"""
        if not self._initialized:
            return {
                "status": "not_initialized",
                "components": {}
            }
        
        health_status = {
            "status": "healthy",
            "components": {},
            "timestamp": "timestamp_placeholder"
        }
        
        try:
            # Get health from each component
            components = {
                "tool_discovery": self._tool_discovery,
                "agent_coordinator": self._agent_coordinator,
                "workflow_cache": self._workflow_cache,
                "context_preserver": self._context_preserver,
                "load_balancer": self._load_balancer
            }
            
            for name, component in components.items():
                if component:
                    try:
                        component_health = await component.get_health_status()
                        health_status["components"][name] = component_health
                        
                        # Update overall status if any component is unhealthy
                        if component_health.get("status") != "healthy":
                            health_status["status"] = "degraded"
                    
                    except Exception as e:
                        health_status["components"][name] = {
                            "status": "error",
                            "error": str(e)
                        }
                        health_status["status"] = "degraded"
                else:
                    health_status["components"][name] = {
                        "status": "not_available"
                    }
        
        except Exception as e:
            health_status["status"] = "error"
            health_status["error"] = str(e)
        
        return health_status


def create_integration_manager(
    config: Optional[Dict[str, Any]] = None
) -> IntegrationManager:
    """
    Create and configure an integration manager for V2 workflows
    
    Args:
        config: Configuration dictionary for integration components
    
    Returns:
        Configured IntegrationManager instance
    """
    # Default configuration
    default_config = {
        "tool_discovery": {
            "default_strategy": DiscoveryStrategy.AUTOMATIC.value,
            "cache_discoveries": True,
            "discovery_timeout": 30,
            "max_concurrent_discoveries": 5,
            "enable_semantic_search": True,
            "similarity_threshold": 0.8,
            "auto_register_tools": True,
            "tool_health_check_interval": 60
        },
        "agent_coordinator": {
            "default_coordination_mode": CoordinationMode.COLLABORATIVE.value,
            "coordination_timeout": 300,
            "failure_retry_count": 3,
            "sync_checkpoint_interval": 60,
            "session_cleanup_interval": 3600,
            "max_concurrent_sessions": 50,
            "enable_session_persistence": True,
            "session_timeout": 1800
        },
        "workflow_cache": {
            "backend": "memory",  # Options: memory, redis, sqlite
            "default_ttl": 3600,
            "max_cache_size": 10000,
            "default_strategy": CacheStrategy.SEMANTIC.value,
            "enable_compression": True,
            "compression_threshold": 1024,
            "similarity_threshold": 0.9,
            "auto_cleanup_interval": 300,
            "cache_hit_tracking": True
        },
        "context_preserver": {
            "storage_backend": "sqlite",
            "compression_enabled": True,
            "max_context_age_hours": 24,
            "auto_cleanup_interval": 3600,
            "max_snapshots_per_session": 100,
            "compression_ratio_target": 0.5,
            "enable_semantic_compression": True,
            "context_quality_threshold": 0.7
        },
        "load_balancer": {
            "strategy": LoadBalancingStrategy.ROUND_ROBIN.value,
            "weights": {},
            "health_check_interval": 30,
            "failure_threshold": 3,
            "recovery_time": 60,
            "performance_window": 300,
            "resource_weight": 0.5,
            "latency_weight": 0.3,
            "success_rate_weight": 0.2,
            "enable_auto_scaling": False,
            "target_utilization": 0.8
        }
    }
    
    # Merge provided config with defaults
    if config:
        merged_config = {}
        for section, section_config in default_config.items():
            merged_config[section] = {**section_config}
            if section in config:
                merged_config[section].update(config[section])
        final_config = merged_config
    else:
        final_config = default_config
    
    logger.info("Creating integration manager with configuration")
    return IntegrationManager(final_config)


def create_default_integration_manager() -> IntegrationManager:
    """
    Create an integration manager with sensible defaults for most use cases
    
    Returns:
        IntegrationManager with default configuration
    """
    return create_integration_manager()


def create_performance_optimized_integration_manager() -> IntegrationManager:
    """
    Create an integration manager optimized for high-performance scenarios
    
    Returns:
        IntegrationManager optimized for performance
    """
    performance_config = {
        "tool_discovery": {
            "cache_discoveries": True,
            "max_concurrent_discoveries": 10,
            "discovery_timeout": 15
        },
        "agent_coordinator": {
            "max_concurrent_sessions": 100,
            "coordination_timeout": 180,
            "sync_checkpoint_interval": 30
        },
        "workflow_cache": {
            "backend": "redis",
            "max_cache_size": 50000,
            "auto_cleanup_interval": 60,
            "enable_compression": True
        },
        "context_preserver": {
            "compression_enabled": True,
            "compression_ratio_target": 0.3,
            "auto_cleanup_interval": 1800
        },
        "load_balancer": {
            "strategy": LoadBalancingStrategy.PERFORMANCE.value,
            "health_check_interval": 15,
            "enable_auto_scaling": True,
            "target_utilization": 0.7
        }
    }
    
    return create_integration_manager(performance_config)


def create_development_integration_manager() -> IntegrationManager:
    """
    Create an integration manager suitable for development environments
    
    Returns:
        IntegrationManager configured for development
    """
    dev_config = {
        "tool_discovery": {
            "auto_register_tools": True,
            "tool_health_check_interval": 300
        },
        "agent_coordinator": {
            "enable_session_persistence": False,
            "session_cleanup_interval": 600
        },
        "workflow_cache": {
            "backend": "memory",
            "max_cache_size": 1000,
            "default_ttl": 600
        },
        "context_preserver": {
            "storage_backend": "sqlite",
            "max_context_age_hours": 4,
            "auto_cleanup_interval": 600
        },
        "load_balancer": {
            "health_check_interval": 60,
            "failure_threshold": 5
        }
    }
    
    return create_integration_manager(dev_config)


def create_resource_constrained_integration_manager() -> IntegrationManager:
    """
    Create an integration manager for resource-constrained environments
    
    Returns:
        IntegrationManager optimized for low resource usage
    """
    constrained_config = {
        "tool_discovery": {
            "max_concurrent_discoveries": 2,
            "cache_discoveries": False,
            "enable_semantic_search": False
        },
        "agent_coordinator": {
            "max_concurrent_sessions": 10,
            "enable_session_persistence": False,
            "coordination_timeout": 120
        },
        "workflow_cache": {
            "backend": "memory",
            "max_cache_size": 500,
            "enable_compression": False,
            "auto_cleanup_interval": 120
        },
        "context_preserver": {
            "compression_enabled": False,
            "max_context_age_hours": 2,
            "max_snapshots_per_session": 20
        },
        "load_balancer": {
            "health_check_interval": 120,
            "enable_auto_scaling": False
        }
    }
    
    return create_integration_manager(constrained_config)


# Factory function registry for easy access
FACTORY_FUNCTIONS = {
    "default": create_default_integration_manager,
    "performance": create_performance_optimized_integration_manager,
    "development": create_development_integration_manager,
    "constrained": create_resource_constrained_integration_manager
}


def get_integration_manager_factory(profile: str = "default") -> Callable[[], IntegrationManager]:
    """
    Get a factory function for creating integration managers
    
    Args:
        profile: Configuration profile name
    
    Returns:
        Factory function for the specified profile
    """
    if profile not in FACTORY_FUNCTIONS:
        available_profiles = ", ".join(FACTORY_FUNCTIONS.keys())
        raise ValueError(f"Unknown profile '{profile}'. Available profiles: {available_profiles}")
    
    return FACTORY_FUNCTIONS[profile]