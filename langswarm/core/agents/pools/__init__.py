"""
LangSwarm V2 Connection Pool Management

Sophisticated connection pooling system for all V2 agent providers with:
- Shared connection pools with configurable limits
- Provider-specific pool optimization strategies  
- Connection health monitoring and automatic replacement
- Load balancing across multiple API keys
- Connection metrics and performance monitoring
"""

from typing import Optional, Dict, Any

from .interfaces import (
    # Core interfaces
    IConnectionPool, IConnectionManager, IPoolMetrics,
    
    # Data structures
    ConnectionConfig, PoolConfig, ConnectionStats, PoolStats,
    
    # Enums
    ConnectionStatus, PoolStrategy, LoadBalancingMode
)

from .base import (
    BaseConnectionPool, BaseConnectionManager, PoolMetrics
)

from .providers import (
    OpenAIConnectionPool, AnthropicConnectionPool, GeminiConnectionPool,
    CohereConnectionPool, MistralConnectionPool, HuggingFaceConnectionPool,
    LocalConnectionPool
)

from .manager import (
    GlobalConnectionManager, create_connection_manager,
    get_connection_manager, configure_pools
)

from .load_balancer import (
    ConnectionLoadBalancer, RoundRobinBalancer, WeightedBalancer,
    HealthBasedBalancer
)

from .monitoring import (
    ConnectionMonitor, PoolHealthChecker, MetricsCollector
)

# Version info
__version__ = "2.0.0"

# Public API
__all__ = [
    # Core interfaces
    'IConnectionPool',
    'IConnectionManager', 
    'IPoolMetrics',
    
    # Data structures
    'ConnectionConfig',
    'PoolConfig',
    'ConnectionStats',
    'PoolStats',
    
    # Enums
    'ConnectionStatus',
    'PoolStrategy',
    'LoadBalancingMode',
    
    # Base implementations
    'BaseConnectionPool',
    'BaseConnectionManager',
    'PoolMetrics',
    
    # Provider pools
    'OpenAIConnectionPool',
    'AnthropicConnectionPool',
    'GeminiConnectionPool',
    'CohereConnectionPool',
    'MistralConnectionPool',
    'HuggingFaceConnectionPool',
    'LocalConnectionPool',
    
    # Manager
    'GlobalConnectionManager',
    'create_connection_manager',
    'get_connection_manager',
    'configure_pools',
    
    # Load balancing
    'ConnectionLoadBalancer',
    'RoundRobinBalancer',
    'WeightedBalancer',
    'HealthBasedBalancer',
    
    # Monitoring
    'ConnectionMonitor',
    'PoolHealthChecker',
    'MetricsCollector'
]

# Global connection manager instance
_global_manager: Optional[GlobalConnectionManager] = None


def get_global_connection_manager() -> Optional[GlobalConnectionManager]:
    """Get the global connection manager"""
    return _global_manager


def set_global_connection_manager(manager: GlobalConnectionManager):
    """Set the global connection manager"""
    global _global_manager
    _global_manager = manager


def initialize_connection_pools(config: Optional[Dict[str, Any]] = None):
    """Initialize global connection pools with configuration"""
    if not get_global_connection_manager():
        manager = create_connection_manager(config or {})
        set_global_connection_manager(manager)


# Convenience functions for quick access
async def get_connection(provider: str, **kwargs):
    """Get a connection from the appropriate provider pool"""
    manager = get_global_connection_manager()
    if manager:
        return await manager.get_connection(provider, **kwargs)
    else:
        raise RuntimeError("Connection manager not initialized")


async def release_connection(provider: str, connection, **kwargs):
    """Release a connection back to the provider pool"""
    manager = get_global_connection_manager()
    if manager:
        await manager.release_connection(provider, connection, **kwargs)


async def get_pool_stats(provider: str = None) -> Dict[str, Any]:
    """Get connection pool statistics"""
    manager = get_global_connection_manager()
    if manager:
        return await manager.get_pool_stats(provider)
    else:
        return {}


async def health_check_pools() -> Dict[str, Any]:
    """Perform health check on all connection pools"""
    manager = get_global_connection_manager()
    if manager:
        return await manager.health_check_all_pools()
    else:
        return {"status": "not_initialized"}
