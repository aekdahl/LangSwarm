"""
LangSwarm V2 Base Connection Pool Implementation

Base classes and common functionality for connection pools across all providers.
Provides thread-safe connection management, health monitoring, and metrics collection.
"""

import asyncio
import logging
import time
import weakref
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncContextManager, Set
import threading
from collections import defaultdict

from .interfaces import (
    IConnectionPool, IConnectionManager, IPoolMetrics,
    ConnectionConfig, PoolConfig, ConnectionStats, PoolStats,
    ConnectionStatus, PoolStrategy, LoadBalancingMode,
    ConnectionPoolError, PoolExhaustedError, ConnectionTimeoutError
)


class BaseConnectionPool(IConnectionPool):
    """
    Base implementation for connection pools.
    
    Provides common functionality for connection lifecycle management,
    health monitoring, and metrics collection.
    """
    
    def __init__(self, config: PoolConfig):
        """
        Initialize base connection pool.
        
        Args:
            config: Pool configuration
        """
        self._config = config
        self._connections: Dict[str, Any] = {}
        self._connection_stats: Dict[str, ConnectionStats] = {}
        self._available_connections: asyncio.Queue = asyncio.Queue()
        self._active_connections: Set[str] = set()
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._initialized = False
        
        # Pool statistics
        self._pool_stats = PoolStats(
            pool_name=config.pool_name,
            provider=config.provider,
            total_connections=0,
            active_connections=0,
            idle_connections=0,
            healthy_connections=0,
            degraded_connections=0,
            unhealthy_connections=0
        )
        
        logging.info(f"Initialized connection pool: {config.pool_name} for provider: {config.provider}")
    
    @property
    def config(self) -> PoolConfig:
        """Get pool configuration"""
        return self._config
    
    @property
    def provider(self) -> str:
        """Get provider name"""
        return self._config.provider
    
    async def initialize(self) -> None:
        """Initialize the connection pool"""
        if self._initialized:
            return
        
        async with self._lock:
            if self._initialized:
                return
            
            try:
                # Create minimum connections
                await self._create_initial_connections()
                
                # Start background tasks
                if self._config.monitoring_enabled:
                    self._health_check_task = asyncio.create_task(self._health_check_loop())
                    self._metrics_task = asyncio.create_task(self._metrics_collection_loop())
                
                self._initialized = True
                logging.info(f"Connection pool initialized: {self._config.pool_name}")
                
            except Exception as e:
                logging.error(f"Failed to initialize connection pool {self._config.pool_name}: {e}")
                raise ConnectionPoolError(f"Pool initialization failed: {e}")
    
    async def _create_initial_connections(self) -> None:
        """Create initial connections based on min_connections"""
        for i in range(self._config.min_connections):
            try:
                connection = await self._create_connection(i)
                if connection:
                    await self._add_connection_to_pool(connection)
            except Exception as e:
                logging.warning(f"Failed to create initial connection {i}: {e}")
                # Continue creating other connections
    
    async def _create_connection(self, index: int) -> Optional[Any]:
        """
        Create a new connection (provider-specific implementation).
        
        Args:
            index: Connection index for configuration selection
            
        Returns:
            Connection object or None if creation failed
        """
        # This should be implemented by provider-specific pool classes
        raise NotImplementedError("Subclasses must implement _create_connection")
    
    async def _add_connection_to_pool(self, connection: Any) -> None:
        """Add a connection to the pool"""
        connection_id = getattr(connection, 'connection_id', f"conn_{len(self._connections)}")
        
        # Store connection
        self._connections[connection_id] = connection
        
        # Initialize stats
        self._connection_stats[connection_id] = ConnectionStats(
            connection_id=connection_id,
            status=ConnectionStatus.HEALTHY,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        # Add to available queue
        await self._available_connections.put(connection_id)
        
        # Update pool stats
        self._pool_stats.total_connections += 1
        self._pool_stats.idle_connections += 1
        self._pool_stats.healthy_connections += 1
        
        logging.debug(f"Added connection {connection_id} to pool {self._config.pool_name}")
    
    @asynccontextmanager
    async def get_connection(self, **kwargs) -> AsyncContextManager[Any]:
        """
        Get a connection from the pool.
        
        Returns:
            Async context manager for connection
        """
        if not self._initialized:
            await self.initialize()
        
        connection_id = None
        connection = None
        
        try:
            # Get connection from pool
            connection_id = await self._acquire_connection(**kwargs)
            connection = self._connections.get(connection_id)
            
            if not connection:
                raise ConnectionPoolError(f"Connection {connection_id} not found in pool")
            
            # Mark as active
            async with self._lock:
                self._active_connections.add(connection_id)
                self._pool_stats.active_connections += 1
                self._pool_stats.idle_connections -= 1
                
                # Update connection stats
                stats = self._connection_stats.get(connection_id)
                if stats:
                    stats.last_used = datetime.utcnow()
                    stats.current_active_requests += 1
            
            yield connection
            
        except Exception as e:
            logging.error(f"Error getting connection from pool {self._config.pool_name}: {e}")
            raise
            
        finally:
            # Release connection back to pool
            if connection_id and connection:
                await self._release_connection_internal(connection_id, connection)
    
    async def _acquire_connection(self, **kwargs) -> str:
        """Acquire a connection from the available pool"""
        timeout = kwargs.get('timeout', self._config.connection_timeout)
        
        try:
            # Wait for available connection
            connection_id = await asyncio.wait_for(
                self._available_connections.get(), 
                timeout=timeout
            )
            return connection_id
            
        except asyncio.TimeoutError:
            # Try to create new connection if pool not at max
            if len(self._connections) < self._config.max_connections:
                try:
                    connection = await self._create_connection(len(self._connections))
                    if connection:
                        await self._add_connection_to_pool(connection)
                        return await self._acquire_connection(**kwargs)
                except Exception as e:
                    logging.warning(f"Failed to create new connection: {e}")
            
            raise PoolExhaustedError(f"No connections available in pool {self._config.pool_name}")
    
    async def _release_connection_internal(self, connection_id: str, connection: Any) -> None:
        """Release connection back to the pool"""
        try:
            async with self._lock:
                if connection_id in self._active_connections:
                    self._active_connections.remove(connection_id)
                    self._pool_stats.active_connections -= 1
                    self._pool_stats.idle_connections += 1
                    
                    # Update connection stats
                    stats = self._connection_stats.get(connection_id)
                    if stats:
                        stats.current_active_requests = max(0, stats.current_active_requests - 1)
                
                # Check connection health before returning to pool
                if await self._is_connection_healthy(connection):
                    await self._available_connections.put(connection_id)
                else:
                    # Remove unhealthy connection
                    await self._remove_connection(connection_id)
                    
                    # Create replacement if needed
                    if len(self._connections) < self._config.min_connections:
                        asyncio.create_task(self._create_replacement_connection())
        
        except Exception as e:
            logging.error(f"Error releasing connection {connection_id}: {e}")
    
    async def release_connection(self, connection: Any, **kwargs) -> None:
        """Release a connection back to the pool (public interface)"""
        # Find connection ID
        connection_id = None
        for cid, conn in self._connections.items():
            if conn is connection:
                connection_id = cid
                break
        
        if connection_id:
            await self._release_connection_internal(connection_id, connection)
        else:
            logging.warning(f"Connection not found in pool {self._config.pool_name}")
    
    async def _is_connection_healthy(self, connection: Any) -> bool:
        """Check if a connection is healthy (provider-specific implementation)"""
        # This should be implemented by provider-specific pool classes
        return True
    
    async def _remove_connection(self, connection_id: str) -> None:
        """Remove a connection from the pool"""
        if connection_id in self._connections:
            connection = self._connections.pop(connection_id)
            self._connection_stats.pop(connection_id, None)
            
            if connection_id in self._active_connections:
                self._active_connections.remove(connection_id)
                self._pool_stats.active_connections -= 1
            else:
                self._pool_stats.idle_connections -= 1
            
            self._pool_stats.total_connections -= 1
            
            # Close connection if it has a close method
            if hasattr(connection, 'close'):
                try:
                    await connection.close()
                except Exception as e:
                    logging.warning(f"Error closing connection {connection_id}: {e}")
            
            logging.debug(f"Removed connection {connection_id} from pool {self._config.pool_name}")
    
    async def _create_replacement_connection(self) -> None:
        """Create a replacement connection"""
        try:
            connection = await self._create_connection(len(self._connections))
            if connection:
                await self._add_connection_to_pool(connection)
        except Exception as e:
            logging.error(f"Failed to create replacement connection: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the pool"""
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        
        for connection_id, connection in self._connections.items():
            try:
                if await self._is_connection_healthy(connection):
                    healthy_count += 1
                    self._connection_stats[connection_id].status = ConnectionStatus.HEALTHY
                else:
                    unhealthy_count += 1
                    self._connection_stats[connection_id].status = ConnectionStatus.UNHEALTHY
            except Exception:
                degraded_count += 1
                self._connection_stats[connection_id].status = ConnectionStatus.DEGRADED
        
        # Update pool stats
        self._pool_stats.healthy_connections = healthy_count
        self._pool_stats.degraded_connections = degraded_count
        self._pool_stats.unhealthy_connections = unhealthy_count
        
        return {
            "pool_name": self._config.pool_name,
            "provider": self._config.provider,
            "status": "healthy" if healthy_count > 0 else "unhealthy",
            "total_connections": len(self._connections),
            "healthy_connections": healthy_count,
            "degraded_connections": degraded_count,
            "unhealthy_connections": unhealthy_count,
            "active_connections": len(self._active_connections),
            "idle_connections": self._available_connections.qsize()
        }
    
    async def get_stats(self) -> PoolStats:
        """Get pool statistics"""
        # Update current stats
        self._pool_stats.last_updated = datetime.utcnow()
        self._pool_stats.connection_stats = list(self._connection_stats.values())
        
        # Calculate aggregate metrics
        if self._connection_stats:
            total_requests = sum(stats.total_requests for stats in self._connection_stats.values())
            successful_requests = sum(stats.successful_requests for stats in self._connection_stats.values())
            failed_requests = sum(stats.failed_requests for stats in self._connection_stats.values())
            
            avg_response_times = [stats.avg_response_time_ms for stats in self._connection_stats.values() if stats.avg_response_time_ms > 0]
            avg_response_time = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0.0
            
            self._pool_stats.total_requests = total_requests
            self._pool_stats.successful_requests = successful_requests
            self._pool_stats.failed_requests = failed_requests
            self._pool_stats.avg_response_time_ms = avg_response_time
        
        return self._pool_stats
    
    async def scale_pool(self, target_size: int) -> None:
        """Scale the pool to target size"""
        async with self._lock:
            current_size = len(self._connections)
            
            if target_size > current_size:
                # Scale up
                for i in range(target_size - current_size):
                    try:
                        connection = await self._create_connection(current_size + i)
                        if connection:
                            await self._add_connection_to_pool(connection)
                    except Exception as e:
                        logging.error(f"Failed to scale up connection {i}: {e}")
            
            elif target_size < current_size:
                # Scale down
                connections_to_remove = current_size - target_size
                for _ in range(connections_to_remove):
                    if self._available_connections.qsize() > 0:
                        try:
                            connection_id = await self._available_connections.get()
                            await self._remove_connection(connection_id)
                        except Exception as e:
                            logging.error(f"Failed to scale down connection: {e}")
    
    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks"""
        while not self._shutdown_event.is_set():
            try:
                await self.health_check()
                await asyncio.sleep(self._config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in health check loop: {e}")
                await asyncio.sleep(self._config.health_check_interval)
    
    async def _metrics_collection_loop(self) -> None:
        """Background task for metrics collection"""
        while not self._shutdown_event.is_set():
            try:
                # Update metrics
                await self.get_stats()
                await asyncio.sleep(60)  # Collect metrics every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(60)
    
    async def shutdown(self) -> None:
        """Shutdown the connection pool"""
        logging.info(f"Shutting down connection pool: {self._config.pool_name}")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._metrics_task:
            self._metrics_task.cancel()
            try:
                await self._metrics_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        async with self._lock:
            for connection_id in list(self._connections.keys()):
                await self._remove_connection(connection_id)
        
        self._initialized = False
        logging.info(f"Connection pool shutdown complete: {self._config.pool_name}")


class BaseConnectionManager(IConnectionManager):
    """
    Base implementation for connection managers.
    
    Manages multiple connection pools across different providers.
    """
    
    def __init__(self):
        """Initialize base connection manager"""
        self._pools: Dict[str, IConnectionPool] = {}
        self._lock = asyncio.Lock()
        self._metrics = PoolMetrics()
    
    async def register_pool(self, pool: IConnectionPool) -> None:
        """Register a connection pool"""
        async with self._lock:
            self._pools[pool.provider] = pool
            await pool.initialize()
            logging.info(f"Registered connection pool for provider: {pool.provider}")
    
    async def unregister_pool(self, provider: str) -> None:
        """Unregister a connection pool"""
        async with self._lock:
            if provider in self._pools:
                pool = self._pools.pop(provider)
                await pool.shutdown()
                logging.info(f"Unregistered connection pool for provider: {provider}")
    
    async def get_connection(self, provider: str, **kwargs) -> AsyncContextManager[Any]:
        """Get a connection from the appropriate pool"""
        if provider not in self._pools:
            raise ConnectionPoolError(f"No pool registered for provider: {provider}")
        
        pool = self._pools[provider]
        return pool.get_connection(**kwargs)
    
    async def release_connection(self, provider: str, connection: Any, **kwargs) -> None:
        """Release a connection back to the appropriate pool"""
        if provider not in self._pools:
            raise ConnectionPoolError(f"No pool registered for provider: {provider}")
        
        pool = self._pools[provider]
        await pool.release_connection(connection, **kwargs)
    
    async def get_pool_stats(self, provider: Optional[str] = None) -> Dict[str, PoolStats]:
        """Get statistics for one or all pools"""
        stats = {}
        
        if provider:
            if provider in self._pools:
                stats[provider] = await self._pools[provider].get_stats()
        else:
            for prov, pool in self._pools.items():
                stats[prov] = await pool.get_stats()
        
        return stats
    
    async def health_check_all_pools(self) -> Dict[str, Any]:
        """Perform health check on all pools"""
        health_results = {}
        
        for provider, pool in self._pools.items():
            try:
                health_results[provider] = await pool.health_check()
            except Exception as e:
                health_results[provider] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_results
    
    async def configure_pool(self, provider: str, config: PoolConfig) -> None:
        """Configure a specific pool"""
        # This would typically recreate the pool with new configuration
        if provider in self._pools:
            await self.unregister_pool(provider)
        
        # Create new pool with configuration (provider-specific implementation needed)
        # This is typically done by the connection manager factory
    
    async def shutdown_all_pools(self) -> None:
        """Shutdown all connection pools"""
        async with self._lock:
            for provider in list(self._pools.keys()):
                await self.unregister_pool(provider)


class PoolMetrics(IPoolMetrics):
    """
    Base implementation for pool metrics collection.
    
    Collects and stores metrics for analysis and monitoring.
    """
    
    def __init__(self):
        """Initialize pool metrics"""
        self._request_metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._connection_events: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._lock = threading.Lock()
    
    async def record_request(self, provider: str, connection_id: str, 
                           response_time_ms: float, success: bool) -> None:
        """Record a request metric"""
        metric = {
            "timestamp": datetime.utcnow(),
            "connection_id": connection_id,
            "response_time_ms": response_time_ms,
            "success": success
        }
        
        with self._lock:
            self._request_metrics[provider].append(metric)
            
            # Keep only recent metrics (last 1000 per provider)
            if len(self._request_metrics[provider]) > 1000:
                self._request_metrics[provider] = self._request_metrics[provider][-1000:]
    
    async def record_connection_event(self, provider: str, connection_id: str, 
                                    event: str, metadata: Dict[str, Any] = None) -> None:
        """Record a connection event"""
        event_record = {
            "timestamp": datetime.utcnow(),
            "connection_id": connection_id,
            "event": event,
            "metadata": metadata or {}
        }
        
        with self._lock:
            self._connection_events[provider].append(event_record)
            
            # Keep only recent events (last 500 per provider)
            if len(self._connection_events[provider]) > 500:
                self._connection_events[provider] = self._connection_events[provider][-500:]
    
    async def get_metrics(self, provider: Optional[str] = None, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metrics for analysis"""
        with self._lock:
            if provider:
                providers = [provider] if provider in self._request_metrics else []
            else:
                providers = list(self._request_metrics.keys())
            
            metrics = {}
            for prov in providers:
                requests = self._request_metrics.get(prov, [])
                events = self._connection_events.get(prov, [])
                
                # Filter by time range if specified
                if start_time or end_time:
                    if start_time:
                        requests = [r for r in requests if r["timestamp"] >= start_time]
                        events = [e for e in events if e["timestamp"] >= start_time]
                    if end_time:
                        requests = [r for r in requests if r["timestamp"] <= end_time]
                        events = [e for e in events if e["timestamp"] <= end_time]
                
                metrics[prov] = {
                    "requests": requests,
                    "events": events,
                    "summary": self._calculate_summary(requests)
                }
            
            return metrics
    
    def _calculate_summary(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for requests"""
        if not requests:
            return {}
        
        total_requests = len(requests)
        successful_requests = sum(1 for r in requests if r["success"])
        response_times = [r["response_time_ms"] for r in requests]
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / total_requests) * 100,
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times)
        }
    
    async def get_performance_insights(self, provider: str) -> Dict[str, Any]:
        """Get performance insights and recommendations"""
        metrics = await self.get_metrics(provider)
        if not metrics or provider not in metrics:
            return {}
        
        provider_metrics = metrics[provider]
        summary = provider_metrics.get("summary", {})
        
        insights = {
            "provider": provider,
            "performance_score": self._calculate_performance_score(summary),
            "recommendations": self._generate_recommendations(summary),
            "trends": self._analyze_trends(provider_metrics.get("requests", []))
        }
        
        return insights
    
    def _calculate_performance_score(self, summary: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""
        if not summary:
            return 0.0
        
        success_rate = summary.get("success_rate", 0)
        avg_response_time = summary.get("avg_response_time_ms", 1000)
        
        # Score based on success rate (0-50 points)
        success_score = success_rate * 0.5
        
        # Score based on response time (0-50 points)
        # Lower response time = higher score
        response_score = max(0, 50 - (avg_response_time / 20))
        
        return min(100, success_score + response_score)
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        if not summary:
            return ["Insufficient data for recommendations"]
        
        success_rate = summary.get("success_rate", 100)
        avg_response_time = summary.get("avg_response_time_ms", 0)
        
        if success_rate < 95:
            recommendations.append("Success rate is below 95%. Consider checking connection health and retrying failed requests.")
        
        if avg_response_time > 1000:
            recommendations.append("Average response time is above 1000ms. Consider increasing connection pool size or using multiple API keys.")
        
        if avg_response_time > 500:
            recommendations.append("Response time could be improved. Consider implementing request caching or using faster endpoints.")
        
        if not recommendations:
            recommendations.append("Performance is good. No specific recommendations at this time.")
        
        return recommendations
    
    def _analyze_trends(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends"""
        if len(requests) < 10:
            return {"trend": "insufficient_data"}
        
        # Analyze recent vs older requests
        mid_point = len(requests) // 2
        older_requests = requests[:mid_point]
        recent_requests = requests[mid_point:]
        
        older_avg = sum(r["response_time_ms"] for r in older_requests) / len(older_requests)
        recent_avg = sum(r["response_time_ms"] for r in recent_requests) / len(recent_requests)
        
        trend = "stable"
        if recent_avg > older_avg * 1.2:
            trend = "degrading"
        elif recent_avg < older_avg * 0.8:
            trend = "improving"
        
        return {
            "trend": trend,
            "older_avg_response_time": older_avg,
            "recent_avg_response_time": recent_avg,
            "change_percentage": ((recent_avg - older_avg) / older_avg) * 100
        }
    
    async def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        metrics = await self.get_metrics()
        
        if format.lower() == "json":
            import json
            return json.dumps(metrics, default=str, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
