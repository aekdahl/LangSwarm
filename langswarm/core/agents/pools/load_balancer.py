"""
LangSwarm V2 Connection Load Balancer

Sophisticated load balancing strategies for connection pools with:
- Multiple load balancing algorithms
- Health-based routing
- Performance-aware selection
- API key rotation and failover
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque

from .interfaces import (
    ILoadBalancer, IConnectionPool, PoolStrategy, LoadBalancingMode,
    ConnectionStatus, LoadBalancingError
)


class ConnectionLoadBalancer(ILoadBalancer):
    """
    Advanced connection load balancer with multiple strategies.
    
    Supports round-robin, weighted, health-based, and performance-based routing.
    Includes automatic failover and API key rotation capabilities.
    """
    
    def __init__(self, strategy: PoolStrategy = PoolStrategy.ROUND_ROBIN):
        """
        Initialize connection load balancer.
        
        Args:
            strategy: Default load balancing strategy
        """
        self._strategy = strategy
        self._pools: Dict[str, IConnectionPool] = {}
        self._connection_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._round_robin_counters: Dict[str, int] = defaultdict(int)
        self._connection_health: Dict[str, Dict[str, ConnectionStatus]] = defaultdict(dict)
        self._performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._last_selection: Dict[str, datetime] = {}
        
        logging.info(f"Initialized Connection Load Balancer with strategy: {strategy.value}")
    
    async def register_pool(self, provider: str, pool: IConnectionPool) -> None:
        """Register a connection pool with the load balancer"""
        self._pools[provider] = pool
        logging.info(f"Registered pool for provider: {provider}")
    
    async def unregister_pool(self, provider: str) -> None:
        """Unregister a connection pool"""
        if provider in self._pools:
            self._pools.pop(provider)
            self._connection_metrics.pop(provider, None)
            self._round_robin_counters.pop(provider, None)
            self._connection_health.pop(provider, None)
            self._performance_history.pop(provider, None)
            logging.info(f"Unregistered pool for provider: {provider}")
    
    async def select_connection(self, available_connections: List[Any], 
                              request_context: Dict[str, Any] = None) -> Any:
        """
        Select the best connection for a request.
        
        Args:
            available_connections: List of available connections
            request_context: Context about the request for optimization
            
        Returns:
            Selected connection
        """
        if not available_connections:
            raise LoadBalancingError("No available connections")
        
        if len(available_connections) == 1:
            return available_connections[0]
        
        context = request_context or {}
        strategy = PoolStrategy(context.get("strategy", self._strategy.value))
        
        # Select connection based on strategy
        if strategy == PoolStrategy.ROUND_ROBIN:
            return await self._round_robin_selection(available_connections, context)
        elif strategy == PoolStrategy.WEIGHTED_ROUND_ROBIN:
            return await self._weighted_round_robin_selection(available_connections, context)
        elif strategy == PoolStrategy.LEAST_CONNECTIONS:
            return await self._least_connections_selection(available_connections, context)
        elif strategy == PoolStrategy.HEALTH_BASED:
            return await self._health_based_selection(available_connections, context)
        elif strategy == PoolStrategy.PERFORMANCE_BASED:
            return await self._performance_based_selection(available_connections, context)
        elif strategy == PoolStrategy.RANDOM:
            return await self._random_selection(available_connections, context)
        else:
            # Default to round-robin
            return await self._round_robin_selection(available_connections, context)
    
    async def _round_robin_selection(self, connections: List[Any], context: Dict[str, Any]) -> Any:
        """Round-robin connection selection"""
        provider = context.get("provider", "default")
        
        # Filter healthy connections
        healthy_connections = [conn for conn in connections if self._is_connection_healthy(conn)]
        if not healthy_connections:
            healthy_connections = connections  # Fallback to all if none are marked healthy
        
        # Round-robin selection
        counter = self._round_robin_counters[provider]
        selected = healthy_connections[counter % len(healthy_connections)]
        self._round_robin_counters[provider] = (counter + 1) % len(healthy_connections)
        
        logging.debug(f"Round-robin selected connection {getattr(selected, 'connection_id', 'unknown')}")
        return selected
    
    async def _weighted_round_robin_selection(self, connections: List[Any], context: Dict[str, Any]) -> Any:
        """Weighted round-robin connection selection"""
        # Filter healthy connections with weights
        weighted_connections = []
        for conn in connections:
            if self._is_connection_healthy(conn):
                weight = getattr(conn, 'weight', 1.0)
                for _ in range(int(weight * 10)):  # Convert weight to selection frequency
                    weighted_connections.append(conn)
        
        if not weighted_connections:
            return connections[0]  # Fallback
        
        provider = context.get("provider", "default")
        counter = self._round_robin_counters[provider]
        selected = weighted_connections[counter % len(weighted_connections)]
        self._round_robin_counters[provider] = (counter + 1) % len(weighted_connections)
        
        logging.debug(f"Weighted round-robin selected connection {getattr(selected, 'connection_id', 'unknown')}")
        return selected
    
    async def _least_connections_selection(self, connections: List[Any], context: Dict[str, Any]) -> Any:
        """Least connections selection"""
        # Find connection with least active requests
        min_connections = float('inf')
        best_connection = connections[0]
        
        for conn in connections:
            if self._is_connection_healthy(conn):
                active_requests = self._get_active_requests(conn)
                if active_requests < min_connections:
                    min_connections = active_requests
                    best_connection = conn
        
        logging.debug(f"Least connections selected connection {getattr(best_connection, 'connection_id', 'unknown')} with {min_connections} active requests")
        return best_connection
    
    async def _health_based_selection(self, connections: List[Any], context: Dict[str, Any]) -> Any:
        """Health-based connection selection"""
        # Group connections by health status
        healthy = []
        degraded = []
        
        for conn in connections:
            health = self._get_connection_health_status(conn)
            if health == ConnectionStatus.HEALTHY:
                healthy.append(conn)
            elif health == ConnectionStatus.DEGRADED:
                degraded.append(conn)
        
        # Prefer healthy connections
        if healthy:
            return await self._round_robin_selection(healthy, context)
        elif degraded:
            return await self._round_robin_selection(degraded, context)
        else:
            return connections[0]  # Fallback
    
    async def _performance_based_selection(self, connections: List[Any], context: Dict[str, Any]) -> Any:
        """Performance-based connection selection"""
        best_score = float('-inf')
        best_connection = connections[0]
        
        for conn in connections:
            if self._is_connection_healthy(conn):
                score = self._calculate_performance_score(conn)
                if score > best_score:
                    best_score = score
                    best_connection = conn
        
        logging.debug(f"Performance-based selected connection {getattr(best_connection, 'connection_id', 'unknown')} with score {best_score}")
        return best_connection
    
    async def _random_selection(self, connections: List[Any], context: Dict[str, Any]) -> Any:
        """Random connection selection"""
        healthy_connections = [conn for conn in connections if self._is_connection_healthy(conn)]
        if not healthy_connections:
            healthy_connections = connections
        
        selected = random.choice(healthy_connections)
        logging.debug(f"Random selected connection {getattr(selected, 'connection_id', 'unknown')}")
        return selected
    
    def _is_connection_healthy(self, connection: Any) -> bool:
        """Check if a connection is healthy"""
        connection_id = getattr(connection, 'connection_id', None)
        if not connection_id:
            return True  # Assume healthy if no ID
        
        # Check stored health status
        provider = getattr(connection, 'provider', 'default')
        health_status = self._connection_health.get(provider, {}).get(connection_id, ConnectionStatus.HEALTHY)
        
        return health_status in [ConnectionStatus.HEALTHY, ConnectionStatus.DEGRADED]
    
    def _get_active_requests(self, connection: Any) -> int:
        """Get number of active requests for a connection"""
        connection_id = getattr(connection, 'connection_id', None)
        if not connection_id:
            return 0
        
        provider = getattr(connection, 'provider', 'default')
        return self._connection_metrics.get(provider, {}).get(connection_id, {}).get('active_requests', 0)
    
    def _get_connection_health_status(self, connection: Any) -> ConnectionStatus:
        """Get health status of a connection"""
        connection_id = getattr(connection, 'connection_id', None)
        if not connection_id:
            return ConnectionStatus.HEALTHY
        
        provider = getattr(connection, 'provider', 'default')
        return self._connection_health.get(provider, {}).get(connection_id, ConnectionStatus.HEALTHY)
    
    def _calculate_performance_score(self, connection: Any) -> float:
        """Calculate performance score for a connection"""
        connection_id = getattr(connection, 'connection_id', None)
        if not connection_id:
            return 0.0
        
        provider = getattr(connection, 'provider', 'default')
        metrics = self._connection_metrics.get(provider, {}).get(connection_id, {})
        
        # Calculate score based on response time, success rate, and load
        response_time = metrics.get('avg_response_time', 1000)  # ms
        success_rate = metrics.get('success_rate', 100)  # percentage
        active_requests = metrics.get('active_requests', 0)
        
        # Score formula (higher is better)
        response_score = max(0, 100 - (response_time / 10))  # 100 points for 0ms, 0 for 1000ms+
        success_score = success_rate  # 0-100 points
        load_score = max(0, 100 - (active_requests * 10))  # 100 points for 0 requests, decreases with load
        
        total_score = (response_score + success_score + load_score) / 3
        return total_score
    
    async def update_connection_metrics(self, connection: Any, metrics: Dict[str, Any]) -> None:
        """Update metrics for a connection"""
        connection_id = getattr(connection, 'connection_id', None)
        if not connection_id:
            return
        
        provider = getattr(connection, 'provider', 'default')
        
        # Update connection metrics
        if provider not in self._connection_metrics:
            self._connection_metrics[provider] = {}
        
        if connection_id not in self._connection_metrics[provider]:
            self._connection_metrics[provider][connection_id] = {}
        
        self._connection_metrics[provider][connection_id].update(metrics)
        
        # Update performance history
        if 'response_time' in metrics:
            self._performance_history[f"{provider}:{connection_id}"].append({
                'timestamp': datetime.utcnow(),
                'response_time': metrics['response_time'],
                'success': metrics.get('success', True)
            })
        
        logging.debug(f"Updated metrics for connection {connection_id}: {metrics}")
    
    async def handle_connection_failure(self, connection: Any, error: Exception) -> bool:
        """
        Handle connection failure and determine if retry is needed.
        
        Args:
            connection: Failed connection
            error: Exception that occurred
            
        Returns:
            True if retry should be attempted, False otherwise
        """
        connection_id = getattr(connection, 'connection_id', None)
        if not connection_id:
            return False
        
        provider = getattr(connection, 'provider', 'default')
        
        # Update health status
        if provider not in self._connection_health:
            self._connection_health[provider] = {}
        
        # Determine health status based on error type
        error_type = type(error).__name__
        if error_type in ['TimeoutError', 'ConnectionTimeoutError']:
            self._connection_health[provider][connection_id] = ConnectionStatus.DEGRADED
        elif error_type in ['ConnectionError', 'NetworkError']:
            self._connection_health[provider][connection_id] = ConnectionStatus.UNHEALTHY
        else:
            self._connection_health[provider][connection_id] = ConnectionStatus.DEGRADED
        
        # Update failure metrics
        await self.update_connection_metrics(connection, {
            'last_failure': datetime.utcnow(),
            'failure_count': self._connection_metrics.get(provider, {}).get(connection_id, {}).get('failure_count', 0) + 1,
            'last_error': str(error)
        })
        
        logging.warning(f"Connection {connection_id} failed: {error}")
        
        # Determine if retry should be attempted
        failure_count = self._connection_metrics.get(provider, {}).get(connection_id, {}).get('failure_count', 0)
        
        # Retry if failure count is low and error is potentially recoverable
        should_retry = (
            failure_count < 3 and 
            error_type in ['TimeoutError', 'ConnectionTimeoutError', 'HTTPError']
        )
        
        return should_retry
    
    def get_balancing_strategy(self) -> PoolStrategy:
        """Get the current balancing strategy"""
        return self._strategy
    
    def set_balancing_strategy(self, strategy: PoolStrategy) -> None:
        """Set the balancing strategy"""
        self._strategy = strategy
        logging.info(f"Changed load balancing strategy to: {strategy.value}")
    
    async def get_load_balancing_stats(self) -> Dict[str, Any]:
        """Get load balancing statistics"""
        stats = {
            "strategy": self._strategy.value,
            "total_providers": len(self._pools),
            "connection_metrics": dict(self._connection_metrics),
            "health_status": dict(self._connection_health),
            "selection_counters": dict(self._round_robin_counters),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate aggregate statistics
        total_connections = 0
        healthy_connections = 0
        degraded_connections = 0
        unhealthy_connections = 0
        
        for provider_health in self._connection_health.values():
            for health_status in provider_health.values():
                total_connections += 1
                if health_status == ConnectionStatus.HEALTHY:
                    healthy_connections += 1
                elif health_status == ConnectionStatus.DEGRADED:
                    degraded_connections += 1
                else:
                    unhealthy_connections += 1
        
        stats["summary"] = {
            "total_connections": total_connections,
            "healthy_connections": healthy_connections,
            "degraded_connections": degraded_connections,
            "unhealthy_connections": unhealthy_connections,
            "health_rate": (healthy_connections / total_connections * 100) if total_connections > 0 else 100.0
        }
        
        return stats
    
    async def optimize_routing(self) -> Dict[str, Any]:
        """Optimize routing based on performance history"""
        optimizations = {}
        
        for provider in self._pools.keys():
            provider_metrics = self._connection_metrics.get(provider, {})
            
            if not provider_metrics:
                continue
            
            # Analyze connection performance
            connection_scores = {}
            for connection_id, metrics in provider_metrics.items():
                score = self._calculate_performance_score_from_metrics(metrics)
                connection_scores[connection_id] = score
            
            if connection_scores:
                best_connection = max(connection_scores, key=connection_scores.get)
                worst_connection = min(connection_scores, key=connection_scores.get)
                
                optimizations[provider] = {
                    "best_connection": best_connection,
                    "worst_connection": worst_connection,
                    "score_difference": connection_scores[best_connection] - connection_scores[worst_connection],
                    "recommendation": self._generate_routing_recommendation(connection_scores)
                }
        
        return optimizations
    
    def _calculate_performance_score_from_metrics(self, metrics: Dict[str, Any]) -> float:
        """Calculate performance score from stored metrics"""
        response_time = metrics.get('avg_response_time', 1000)
        success_rate = metrics.get('success_rate', 100)
        failure_count = metrics.get('failure_count', 0)
        
        # Score formula
        response_score = max(0, 100 - (response_time / 10))
        success_score = success_rate
        reliability_score = max(0, 100 - (failure_count * 5))
        
        return (response_score + success_score + reliability_score) / 3
    
    def _generate_routing_recommendation(self, connection_scores: Dict[str, float]) -> str:
        """Generate routing optimization recommendation"""
        if not connection_scores:
            return "No data available for recommendations"
        
        scores = list(connection_scores.values())
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score - min_score > 30:
            return "Consider weighted routing to favor high-performing connections"
        elif avg_score < 50:
            return "Overall performance is low. Check connection health and configuration"
        elif avg_score > 80:
            return "Performance is good. Current routing strategy is working well"
        else:
            return "Performance is moderate. Consider performance-based routing"


# Specific load balancer implementations
class RoundRobinBalancer(ConnectionLoadBalancer):
    """Round-robin load balancer"""
    
    def __init__(self):
        super().__init__(PoolStrategy.ROUND_ROBIN)


class WeightedBalancer(ConnectionLoadBalancer):
    """Weighted round-robin load balancer"""
    
    def __init__(self):
        super().__init__(PoolStrategy.WEIGHTED_ROUND_ROBIN)


class HealthBasedBalancer(ConnectionLoadBalancer):
    """Health-based load balancer"""
    
    def __init__(self):
        super().__init__(PoolStrategy.HEALTH_BASED)
