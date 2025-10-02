"""
LangSwarm V2 Connection Pool Interfaces

Core interfaces and data structures for the sophisticated connection pooling system.
Provides abstractions for connection management, load balancing, and monitoring.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, AsyncContextManager
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid


class ConnectionStatus(Enum):
    """Connection status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    MAINTENANCE = "maintenance"


class PoolStrategy(Enum):
    """Connection pool strategy enumeration"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    HEALTH_BASED = "health_based"
    PERFORMANCE_BASED = "performance_based"
    RANDOM = "random"


class LoadBalancingMode(Enum):
    """Load balancing mode enumeration"""
    DISABLED = "disabled"
    API_KEY_ROTATION = "api_key_rotation"
    ENDPOINT_ROTATION = "endpoint_rotation"
    WEIGHTED_DISTRIBUTION = "weighted_distribution"
    FAILOVER = "failover"


@dataclass
class ConnectionConfig:
    """Configuration for individual connections"""
    connection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    api_key: str = ""
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: int = 60
    max_requests_per_minute: int = 1000
    weight: float = 1.0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.connection_id:
            self.connection_id = str(uuid.uuid4())


@dataclass
class PoolConfig:
    """Configuration for connection pools"""
    pool_name: str
    provider: str
    min_connections: int = 1
    max_connections: int = 10
    connection_timeout: int = 30
    idle_timeout: int = 300
    max_lifetime: int = 3600
    health_check_interval: int = 60
    pool_strategy: PoolStrategy = PoolStrategy.ROUND_ROBIN
    load_balancing_mode: LoadBalancingMode = LoadBalancingMode.API_KEY_ROTATION
    auto_scaling_enabled: bool = True
    auto_scaling_threshold: float = 0.8
    connection_configs: List[ConnectionConfig] = field(default_factory=list)
    monitoring_enabled: bool = True
    metrics_retention_days: int = 7
    
    def __post_init__(self):
        if not self.connection_configs:
            # Create default connection config
            self.connection_configs = [ConnectionConfig()]


@dataclass
class ConnectionStats:
    """Statistics for individual connections"""
    connection_id: str
    status: ConnectionStatus
    created_at: datetime
    last_used: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    current_active_requests: int = 0
    last_health_check: Optional[datetime] = None
    health_check_failures: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    error_rate: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    @property
    def requests_per_minute(self) -> float:
        """Calculate requests per minute"""
        if not self.created_at:
            return 0.0
        
        duration = datetime.utcnow() - self.created_at
        minutes = max(duration.total_seconds() / 60.0, 1.0)
        return self.total_requests / minutes


@dataclass
class PoolStats:
    """Statistics for connection pools"""
    pool_name: str
    provider: str
    total_connections: int
    active_connections: int
    idle_connections: int
    healthy_connections: int
    degraded_connections: int
    unhealthy_connections: int
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    peak_active_connections: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    connection_stats: List[ConnectionStats] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate overall pool success rate"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100.0
    
    @property
    def utilization_rate(self) -> float:
        """Calculate pool utilization rate"""
        if self.total_connections == 0:
            return 0.0
        return (self.active_connections / self.total_connections) * 100.0
    
    @property
    def health_rate(self) -> float:
        """Calculate pool health rate"""
        if self.total_connections == 0:
            return 100.0
        return (self.healthy_connections / self.total_connections) * 100.0


class IConnectionPool(ABC):
    """Interface for connection pools"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the connection pool"""
        pass
    
    @abstractmethod
    async def get_connection(self, **kwargs) -> AsyncContextManager[Any]:
        """Get a connection from the pool"""
        pass
    
    @abstractmethod
    async def release_connection(self, connection: Any, **kwargs) -> None:
        """Release a connection back to the pool"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the pool"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> PoolStats:
        """Get pool statistics"""
        pass
    
    @abstractmethod
    async def scale_pool(self, target_size: int) -> None:
        """Scale the pool to target size"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the connection pool"""
        pass
    
    @property
    @abstractmethod
    def config(self) -> PoolConfig:
        """Get pool configuration"""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """Get provider name"""
        pass


class IConnectionManager(ABC):
    """Interface for connection managers"""
    
    @abstractmethod
    async def register_pool(self, pool: IConnectionPool) -> None:
        """Register a connection pool"""
        pass
    
    @abstractmethod
    async def unregister_pool(self, provider: str) -> None:
        """Unregister a connection pool"""
        pass
    
    @abstractmethod
    async def get_connection(self, provider: str, **kwargs) -> AsyncContextManager[Any]:
        """Get a connection from the appropriate pool"""
        pass
    
    @abstractmethod
    async def release_connection(self, provider: str, connection: Any, **kwargs) -> None:
        """Release a connection back to the appropriate pool"""
        pass
    
    @abstractmethod
    async def get_pool_stats(self, provider: Optional[str] = None) -> Dict[str, PoolStats]:
        """Get statistics for one or all pools"""
        pass
    
    @abstractmethod
    async def health_check_all_pools(self) -> Dict[str, Any]:
        """Perform health check on all pools"""
        pass
    
    @abstractmethod
    async def configure_pool(self, provider: str, config: PoolConfig) -> None:
        """Configure a specific pool"""
        pass
    
    @abstractmethod
    async def shutdown_all_pools(self) -> None:
        """Shutdown all connection pools"""
        pass


class IPoolMetrics(ABC):
    """Interface for pool metrics collection"""
    
    @abstractmethod
    async def record_request(self, provider: str, connection_id: str, 
                           response_time_ms: float, success: bool) -> None:
        """Record a request metric"""
        pass
    
    @abstractmethod
    async def record_connection_event(self, provider: str, connection_id: str, 
                                    event: str, metadata: Dict[str, Any] = None) -> None:
        """Record a connection event"""
        pass
    
    @abstractmethod
    async def get_metrics(self, provider: Optional[str] = None, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metrics for analysis"""
        pass
    
    @abstractmethod
    async def get_performance_insights(self, provider: str) -> Dict[str, Any]:
        """Get performance insights and recommendations"""
        pass
    
    @abstractmethod
    async def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        pass


class ILoadBalancer(ABC):
    """Interface for load balancing connections"""
    
    @abstractmethod
    async def select_connection(self, available_connections: List[Any], 
                              request_context: Dict[str, Any] = None) -> Any:
        """Select the best connection for a request"""
        pass
    
    @abstractmethod
    async def update_connection_metrics(self, connection: Any, 
                                      metrics: Dict[str, Any]) -> None:
        """Update metrics for a connection"""
        pass
    
    @abstractmethod
    async def handle_connection_failure(self, connection: Any, 
                                      error: Exception) -> bool:
        """Handle connection failure and determine if retry is needed"""
        pass
    
    @abstractmethod
    def get_balancing_strategy(self) -> PoolStrategy:
        """Get the current balancing strategy"""
        pass


class IHealthChecker(ABC):
    """Interface for connection health checking"""
    
    @abstractmethod
    async def check_connection_health(self, connection: Any) -> ConnectionStatus:
        """Check the health of a specific connection"""
        pass
    
    @abstractmethod
    async def check_pool_health(self, pool: IConnectionPool) -> Dict[str, Any]:
        """Check the health of an entire pool"""
        pass
    
    @abstractmethod
    async def get_health_recommendations(self, pool: IConnectionPool) -> List[str]:
        """Get health improvement recommendations"""
        pass


# Exception classes for connection pool management
class ConnectionPoolError(Exception):
    """Base exception for connection pool errors"""
    pass


class PoolExhaustedError(ConnectionPoolError):
    """Raised when connection pool is exhausted"""
    pass


class ConnectionTimeoutError(ConnectionPoolError):
    """Raised when connection timeout occurs"""
    pass


class HealthCheckFailedError(ConnectionPoolError):
    """Raised when health check fails"""
    pass


class LoadBalancingError(ConnectionPoolError):
    """Raised when load balancing fails"""
    pass


class PoolConfigurationError(ConnectionPoolError):
    """Raised when pool configuration is invalid"""
    pass
