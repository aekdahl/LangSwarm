"""
LangSwarm V2 Global Connection Manager

Centralized management of connection pools across all providers with:
- Automatic pool creation and configuration
- Load balancing across multiple API keys
- Health monitoring and automatic failover
- Performance optimization and metrics collection
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncContextManager
from datetime import datetime

from .base import BaseConnectionManager
from .interfaces import (
    IConnectionPool, PoolConfig, ConnectionConfig,
    PoolStrategy, LoadBalancingMode, ConnectionPoolError
)
from .providers import (
    OpenAIConnectionPool, AnthropicConnectionPool, GeminiConnectionPool,
    CohereConnectionPool, MistralConnectionPool, HuggingFaceConnectionPool,
    LocalConnectionPool
)
from .load_balancer import ConnectionLoadBalancer
from .monitoring import ConnectionMonitor


class GlobalConnectionManager(BaseConnectionManager):
    """
    Global connection manager for all V2 agent providers.
    
    Features:
    - Automatic provider detection and pool creation
    - Cross-provider load balancing and health monitoring
    - Performance optimization and resource management
    - Centralized configuration and metrics collection
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize global connection manager.
        
        Args:
            config: Global configuration for all providers
        """
        super().__init__()
        self._config = config or {}
        self._load_balancer = ConnectionLoadBalancer()
        self._monitor = ConnectionMonitor()
        self._auto_scaling_enabled = self._config.get("auto_scaling_enabled", True)
        self._global_health_check_interval = self._config.get("health_check_interval", 300)
        self._health_check_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logging.info("Initialized Global Connection Manager")
    
    async def initialize(self) -> None:
        """Initialize the global connection manager"""
        try:
            # Create pools for configured providers
            await self._create_configured_pools()
            
            # Start background tasks
            self._health_check_task = asyncio.create_task(self._global_health_check_loop())
            if self._auto_scaling_enabled:
                self._optimization_task = asyncio.create_task(self._optimization_loop())
            
            logging.info("Global Connection Manager initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize Global Connection Manager: {e}")
            raise ConnectionPoolError(f"Manager initialization failed: {e}")
    
    async def _create_configured_pools(self) -> None:
        """Create connection pools based on configuration"""
        providers_config = self._config.get("providers", {})
        
        for provider, provider_config in providers_config.items():
            try:
                await self._create_provider_pool(provider, provider_config)
            except Exception as e:
                logging.error(f"Failed to create pool for provider {provider}: {e}")
    
    async def _create_provider_pool(self, provider: str, config: Dict[str, Any]) -> None:
        """Create a connection pool for a specific provider"""
        try:
            # Create pool configuration
            pool_config = self._create_pool_config(provider, config)
            
            # Create provider-specific pool
            if provider.lower() == "openai":
                pool = OpenAIConnectionPool(pool_config)
            elif provider.lower() == "anthropic":
                pool = AnthropicConnectionPool(pool_config)
            elif provider.lower() == "gemini":
                pool = GeminiConnectionPool(pool_config)
            elif provider.lower() == "cohere":
                pool = CohereConnectionPool(pool_config)
            elif provider.lower() == "mistral":
                pool = MistralConnectionPool(pool_config)
            elif provider.lower() == "huggingface":
                use_local = config.get("use_local", False)
                pool = HuggingFaceConnectionPool(pool_config, use_local=use_local)
            elif provider.lower() == "local":
                backend = config.get("backend", "ollama")
                pool = LocalConnectionPool(pool_config, backend=backend)
            else:
                logging.warning(f"Unknown provider: {provider}")
                return
            
            # Register the pool
            await self.register_pool(pool)
            
            # Register with load balancer
            await self._load_balancer.register_pool(provider, pool)
            
            # Register with monitor
            await self._monitor.register_pool(provider, pool)
            
            logging.info(f"Created connection pool for provider: {provider}")
            
        except Exception as e:
            logging.error(f"Failed to create pool for provider {provider}: {e}")
            raise
    
    def _create_pool_config(self, provider: str, config: Dict[str, Any]) -> PoolConfig:
        """Create pool configuration from provider config"""
        # Extract connection configurations
        api_keys = config.get("api_keys", [])
        if isinstance(api_keys, str):
            api_keys = [api_keys]
        
        base_urls = config.get("base_urls", [])
        if isinstance(base_urls, str):
            base_urls = [base_urls]
        
        # Create connection configs
        connection_configs = []
        for i, api_key in enumerate(api_keys):
            conn_config = ConnectionConfig(
                api_key=api_key,
                base_url=base_urls[i] if i < len(base_urls) else None,
                timeout=config.get("timeout", 30),
                max_retries=config.get("max_retries", 3),
                max_requests_per_minute=config.get("max_requests_per_minute", 1000),
                weight=config.get("weights", [1.0] * len(api_keys))[i] if i < len(config.get("weights", [])) else 1.0
            )
            connection_configs.append(conn_config)
        
        # Create pool config
        pool_config = PoolConfig(
            pool_name=f"{provider}_pool",
            provider=provider,
            min_connections=config.get("min_connections", 1),
            max_connections=config.get("max_connections", 10),
            connection_timeout=config.get("connection_timeout", 30),
            idle_timeout=config.get("idle_timeout", 300),
            max_lifetime=config.get("max_lifetime", 3600),
            health_check_interval=config.get("health_check_interval", 60),
            pool_strategy=PoolStrategy(config.get("pool_strategy", "round_robin")),
            load_balancing_mode=LoadBalancingMode(config.get("load_balancing_mode", "api_key_rotation")),
            auto_scaling_enabled=config.get("auto_scaling_enabled", True),
            auto_scaling_threshold=config.get("auto_scaling_threshold", 0.8),
            connection_configs=connection_configs,
            monitoring_enabled=config.get("monitoring_enabled", True),
            metrics_retention_days=config.get("metrics_retention_days", 7)
        )
        
        return pool_config
    
    async def get_connection(self, provider: str, **kwargs) -> AsyncContextManager[Any]:
        """Get a connection with load balancing"""
        if provider not in self._pools:
            raise ConnectionPoolError(f"No pool registered for provider: {provider}")
        
        # Use load balancer to select optimal connection
        pool = self._pools[provider]
        
        # Get load balancing strategy from kwargs or pool config
        strategy = kwargs.get("strategy", pool.config.pool_strategy)
        
        # For now, use the default pool connection method
        # In future, this could implement more sophisticated load balancing
        return pool.get_connection(**kwargs)
    
    async def auto_configure_provider(self, provider: str, **kwargs) -> None:
        """Automatically configure a provider pool"""
        if provider in self._pools:
            logging.info(f"Pool already exists for provider: {provider}")
            return
        
        # Create default configuration
        default_config = {
            "api_keys": [kwargs.get("api_key", "")],
            "base_urls": [kwargs.get("base_url")] if kwargs.get("base_url") else [],
            "min_connections": kwargs.get("min_connections", 1),
            "max_connections": kwargs.get("max_connections", 5),
            "timeout": kwargs.get("timeout", 30),
            "max_retries": kwargs.get("max_retries", 3)
        }
        
        # Add provider-specific defaults
        if provider.lower() == "huggingface":
            default_config["use_local"] = kwargs.get("use_local", False)
        elif provider.lower() == "local":
            default_config["backend"] = kwargs.get("backend", "ollama")
        
        await self._create_provider_pool(provider, default_config)
    
    async def scale_provider_pool(self, provider: str, target_size: int) -> None:
        """Scale a specific provider pool"""
        if provider in self._pools:
            pool = self._pools[provider]
            await pool.scale_pool(target_size)
            logging.info(f"Scaled {provider} pool to {target_size} connections")
        else:
            raise ConnectionPoolError(f"No pool found for provider: {provider}")
    
    async def get_provider_recommendations(self, provider: str) -> Dict[str, Any]:
        """Get optimization recommendations for a provider"""
        if provider not in self._pools:
            return {"error": f"No pool found for provider: {provider}"}
        
        pool = self._pools[provider]
        stats = await pool.get_stats()
        
        recommendations = []
        
        # Analyze utilization
        if stats.utilization_rate > 80:
            recommendations.append({
                "type": "scale_up",
                "message": f"High utilization ({stats.utilization_rate:.1f}%). Consider increasing pool size.",
                "suggested_action": f"scale_pool({provider}, {stats.total_connections + 2})"
            })
        elif stats.utilization_rate < 20 and stats.total_connections > pool.config.min_connections:
            recommendations.append({
                "type": "scale_down",
                "message": f"Low utilization ({stats.utilization_rate:.1f}%). Consider decreasing pool size.",
                "suggested_action": f"scale_pool({provider}, {max(pool.config.min_connections, stats.total_connections - 1)})"
            })
        
        # Analyze health
        if stats.health_rate < 90:
            recommendations.append({
                "type": "health_issue",
                "message": f"Low health rate ({stats.health_rate:.1f}%). Check connection configurations.",
                "suggested_action": "Review API keys and network connectivity"
            })
        
        # Analyze performance
        if stats.avg_response_time_ms > 2000:
            recommendations.append({
                "type": "performance",
                "message": f"High response time ({stats.avg_response_time_ms:.0f}ms). Consider optimizing requests.",
                "suggested_action": "Review request patterns or add more connections"
            })
        
        if not recommendations:
            recommendations.append({
                "type": "optimal",
                "message": "Pool is performing well. No immediate optimizations needed."
            })
        
        return {
            "provider": provider,
            "recommendations": recommendations,
            "current_stats": {
                "total_connections": stats.total_connections,
                "utilization_rate": stats.utilization_rate,
                "health_rate": stats.health_rate,
                "avg_response_time_ms": stats.avg_response_time_ms
            }
        }
    
    async def _global_health_check_loop(self) -> None:
        """Global health check loop for all pools"""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_global_health_check()
                await asyncio.sleep(self._global_health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in global health check loop: {e}")
                await asyncio.sleep(self._global_health_check_interval)
    
    async def _perform_global_health_check(self) -> None:
        """Perform health check on all pools"""
        health_results = await self.health_check_all_pools()
        
        for provider, health_info in health_results.items():
            if health_info.get("status") != "healthy":
                logging.warning(f"Provider {provider} health issue: {health_info}")
                
                # Attempt to fix common issues
                await self._attempt_health_recovery(provider, health_info)
    
    async def _attempt_health_recovery(self, provider: str, health_info: Dict[str, Any]) -> None:
        """Attempt to recover from health issues"""
        try:
            if provider in self._pools:
                pool = self._pools[provider]
                
                # If too many unhealthy connections, try to recreate some
                unhealthy_count = health_info.get("unhealthy_connections", 0)
                total_count = health_info.get("total_connections", 0)
                
                if total_count > 0 and unhealthy_count / total_count > 0.5:
                    logging.info(f"Attempting to recover {provider} pool health")
                    
                    # Scale down and back up to recreate connections
                    min_conn = pool.config.min_connections
                    await pool.scale_pool(min_conn)
                    await asyncio.sleep(5)  # Brief pause
                    await pool.scale_pool(min_conn + 1)
        
        except Exception as e:
            logging.error(f"Failed to recover health for provider {provider}: {e}")
    
    async def _optimization_loop(self) -> None:
        """Auto-optimization loop"""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_auto_optimization()
                await asyncio.sleep(600)  # Optimize every 10 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(600)
    
    async def _perform_auto_optimization(self) -> None:
        """Perform automatic optimization on all pools"""
        for provider in self._pools.keys():
            try:
                recommendations = await self.get_provider_recommendations(provider)
                
                # Apply safe optimizations automatically
                for rec in recommendations.get("recommendations", []):
                    if rec["type"] == "scale_up" and rec.get("auto_apply", False):
                        # Only auto-scale up if explicitly enabled
                        current_stats = recommendations["current_stats"]
                        if current_stats["utilization_rate"] > 85:
                            new_size = current_stats["total_connections"] + 1
                            await self.scale_provider_pool(provider, new_size)
                            logging.info(f"Auto-scaled {provider} to {new_size} connections")
            
            except Exception as e:
                logging.error(f"Error optimizing provider {provider}: {e}")
    
    async def get_global_stats(self) -> Dict[str, Any]:
        """Get global statistics across all pools"""
        all_stats = await self.get_pool_stats()
        
        global_stats = {
            "total_providers": len(all_stats),
            "total_connections": 0,
            "total_active_connections": 0,
            "total_requests": 0,
            "overall_success_rate": 0.0,
            "overall_avg_response_time": 0.0,
            "provider_stats": all_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if all_stats:
            # Calculate aggregates
            total_requests = sum(stats.total_requests for stats in all_stats.values())
            successful_requests = sum(stats.successful_requests for stats in all_stats.values())
            response_times = [stats.avg_response_time_ms for stats in all_stats.values() if stats.avg_response_time_ms > 0]
            
            global_stats.update({
                "total_connections": sum(stats.total_connections for stats in all_stats.values()),
                "total_active_connections": sum(stats.active_connections for stats in all_stats.values()),
                "total_requests": total_requests,
                "overall_success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 100.0,
                "overall_avg_response_time": sum(response_times) / len(response_times) if response_times else 0.0
            })
        
        return global_stats
    
    async def shutdown(self) -> None:
        """Shutdown the global connection manager"""
        logging.info("Shutting down Global Connection Manager")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown all pools
        await self.shutdown_all_pools()
        
        logging.info("Global Connection Manager shutdown complete")


# Factory functions for easy creation
def create_connection_manager(config: Dict[str, Any] = None) -> GlobalConnectionManager:
    """Create a global connection manager with configuration"""
    return GlobalConnectionManager(config)


def get_connection_manager() -> Optional[GlobalConnectionManager]:
    """Get the current global connection manager"""
    # This would typically return a singleton instance
    # For now, return None - users should create their own instance
    return None


async def configure_pools(providers_config: Dict[str, Dict[str, Any]]) -> GlobalConnectionManager:
    """Configure connection pools for multiple providers"""
    config = {"providers": providers_config}
    manager = create_connection_manager(config)
    await manager.initialize()
    return manager
