"""
Memory Factory for AgentMem

Provides factory functions and configuration management for creating
memory backends and managers with simplified configuration patterns.
"""

import logging
import os
from typing import Dict, Any, Optional, Union, Type, List
from dataclasses import dataclass, field

from .interfaces import (
    IMemoryBackend, IMemoryManager,
    MemoryBackendType, MemoryConfig
)
from .base import MemoryManager
from .backends import InMemoryBackend, SQLiteBackend, RedisBackend
from .vector_backend import VectorMemoryBackend


# Custom exception classes for better error handling
class MemoryBackendError(Exception):
    """Raised when memory backend creation or connection fails"""
    def __init__(self, message: str, backend: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.backend = backend
        self.details = details or {}


class MemoryConfigurationError(Exception):
    """Raised when memory configuration is invalid"""
    def __init__(self, message: str, config: Dict[str, Any] = None):
        super().__init__(message)
        self.config = config or {}


@dataclass
class MemoryConfiguration:
    """Unified memory configuration with simplified setup patterns"""
    
    # Basic configuration
    enabled: bool = True
    backend: str = "auto"  # auto, in_memory, sqlite, redis, etc.
    
    # Backend-specific settings
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Advanced options
    auto_cleanup: bool = True
    cleanup_interval: int = 300  # 5 minutes
    session_ttl: Optional[int] = None  # seconds, None = no expiration
    
    # Performance settings
    cache_sessions: bool = True
    max_cached_sessions: int = 1000
    
    # Development and testing
    debug_mode: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def from_simple_config(cls, config: Union[bool, str, Dict[str, Any]]) -> 'MemoryConfiguration':
        """
        Create memory configuration from simplified inputs.
        
        Examples:
        - memory=True -> Auto-select appropriate backend
        - memory="development" -> SQLite with dev settings
        - memory="production" -> Redis/SQLite optimized for production
        - memory={"backend": "redis", "url": "redis://..."} -> Custom config
        """
        
        # Disabled memory
        if config is False:
            return cls(enabled=False)
        
        # Auto-enabled memory
        if config is True:
            return cls(
                enabled=True,
                backend="auto",
                settings={}
            )
        
        # Environment-based configuration
        if isinstance(config, str):
            env_type = config.lower()
            
            if env_type in ["development", "dev", "local"]:
                return cls(
                    enabled=True,
                    backend="sqlite",
                    settings={
                        "db_path": os.path.join(os.getcwd(), "langswarm_dev_memory.db"),
                        "enable_wal": True
                    },
                    debug_mode=True,
                    log_level="DEBUG"
                )
            
            elif env_type in ["testing", "test"]:
                return cls(
                    enabled=True,
                    backend="in_memory",
                    settings={},
                    auto_cleanup=False,  # Don't cleanup during tests
                    debug_mode=True
                )
            
            elif env_type in ["production", "prod"]:
                # Auto-select production backend
                backend, settings = cls._select_production_backend()
                return cls(
                    enabled=True,
                    backend=backend,
                    settings=settings,
                    auto_cleanup=True,
                    cleanup_interval=600,  # 10 minutes
                    cache_sessions=True,
                    max_cached_sessions=5000
                )
            
            elif env_type == "cloud":
                # Cloud-optimized configuration
                backend, settings = cls._select_cloud_backend()
                return cls(
                    enabled=True,
                    backend=backend,
                    settings=settings,
                    auto_cleanup=True,
                    cleanup_interval=300,
                    session_ttl=86400  # 24 hours
                )
            
            else:
                # Treat as backend name
                return cls(
                    enabled=True,
                    backend=env_type,
                    settings={}
                )
        
        # Full configuration
        if isinstance(config, dict):
            return cls(
                enabled=config.get("enabled", True),
                backend=config.get("backend", "auto"),
                settings=config.get("settings", {}),
                auto_cleanup=config.get("auto_cleanup", True),
                cleanup_interval=config.get("cleanup_interval", 300),
                session_ttl=config.get("session_ttl"),
                cache_sessions=config.get("cache_sessions", True),
                max_cached_sessions=config.get("max_cached_sessions", 1000),
                debug_mode=config.get("debug_mode", False),
                log_level=config.get("log_level", "INFO")
            )
        
        # Fallback: disabled
        return cls(enabled=False)
    
    @staticmethod
    def _select_production_backend() -> tuple[str, Dict[str, Any]]:
        """Select optimal production backend based on environment"""
        
        # Check for Redis availability
        if os.getenv("REDIS_URL") or os.getenv("REDIS_HOST"):
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                host = os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", "6379"))
                db = int(os.getenv("REDIS_DB", "0"))
                password = os.getenv("REDIS_PASSWORD")
                
                if password:
                    redis_url = f"redis://:{password}@{host}:{port}/{db}"
                else:
                    redis_url = f"redis://{host}:{port}/{db}"
            
            return "redis", {
                "url": redis_url,
                "key_prefix": "langswarm:v2:memory:",
                "ttl": 86400,  # 24 hours
                "max_connections": 20
            }
        
        # Fallback to optimized SQLite
        return "sqlite", {
            "db_path": os.path.join(os.getcwd(), "langswarm_production_memory.db"),
            "enable_wal": True,
            "cache_size": 2000,
            "synchronous": "NORMAL",
            "journal_mode": "WAL"
        }
    
    @staticmethod
    def _select_cloud_backend() -> tuple[str, Dict[str, Any]]:
        """Select optimal cloud backend based on available services"""
        
        # Check for cloud Redis services
        if os.getenv("REDIS_URL") or os.getenv("REDISCLOUD_URL") or os.getenv("REDIS_TLS_URL"):
            redis_url = (os.getenv("REDIS_URL") or 
                        os.getenv("REDISCLOUD_URL") or 
                        os.getenv("REDIS_TLS_URL"))
            
            return "redis", {
                "url": redis_url,
                "key_prefix": "langswarm:cloud:memory:",
                "ttl": 86400,
                "ssl_cert_reqs": None if "localhost" in redis_url else "required"
            }
        
        # Fallback to SQLite for cloud
        return "sqlite", {
            "db_path": "/tmp/langswarm_cloud_memory.db",
            "enable_wal": True,
            "cache_size": 1000
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []
        
        if not self.enabled:
            return errors  # No validation needed for disabled memory
        
        # Validate backend
        valid_backends = ["auto", "in_memory", "sqlite", "redis", "vector"]
        if self.backend not in valid_backends:
            errors.append(f"Invalid backend '{self.backend}'. Must be one of: {valid_backends}")
        
        # Validate settings for specific backends
        if self.backend == "sqlite":
            if "db_path" in self.settings:
                db_path = self.settings["db_path"]
                if db_path != ":memory:":
                    # Check if directory is writable
                    import pathlib
                    try:
                        pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        errors.append(f"SQLite db_path directory not writable: {e}")
        
        elif self.backend == "redis":
            if "url" not in self.settings:
                errors.append("Redis backend requires 'url' in settings")
        
        # Validate numeric values
        if self.cleanup_interval <= 0:
            errors.append("cleanup_interval must be positive")
        
        if self.max_cached_sessions <= 0:
            errors.append("max_cached_sessions must be positive")
        
        if self.session_ttl is not None and self.session_ttl <= 0:
            errors.append("session_ttl must be positive or None")
        
        return errors


class MemoryFactory:
    """
    Factory for creating memory backends and managers with automatic
    backend selection and configuration management.
    """
    
    _backend_registry: Dict[str, Type[IMemoryBackend]] = {
        "in_memory": InMemoryBackend,
        "sqlite": SQLiteBackend,
        "redis": RedisBackend,
        "vector": VectorMemoryBackend
    }
    
    _logger = logging.getLogger(__name__)
    
    @classmethod
    def register_backend(cls, name: str, backend_class: Type[IMemoryBackend]):
        """Register a custom memory backend"""
        cls._backend_registry[name] = backend_class
        cls._logger.info(f"Registered memory backend: {name}")
    
    @classmethod
    def create_backend(cls, config: MemoryConfiguration) -> IMemoryBackend:
        """Create a memory backend from configuration"""
        
        if not config.enabled:
            raise ValueError("Cannot create backend: memory is disabled")
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise MemoryConfigurationError(
                f"Invalid memory configuration: {'; '.join(errors)}",
                config={"backend": config.backend, "settings": config.settings}
            )
        
        backend_name = config.backend
        attempted_backends = []
        
        # Auto-select backend
        if backend_name == "auto":
            attempted_backends.append("auto")
            backend_name = cls._auto_select_backend(config)
            attempted_backends.append(f"selected:{backend_name}")
        
        # Get backend class
        if backend_name not in cls._backend_registry:
            available_backends = list(cls._backend_registry.keys())
            raise MemoryBackendError(
                f"Unknown memory backend '{backend_name}'. Available backends: {available_backends}",
                backend=backend_name,
                details={
                    "requested_backend": config.backend,
                    "available_backends": available_backends,
                    "attempted_backends": attempted_backends
                }
            )
        
        backend_class = cls._backend_registry[backend_name]
        
        # Create backend with detailed error context
        try:
            backend = backend_class(config.settings)
            cls._logger.info(f"Created {backend_name} memory backend")
            return backend
        except Exception as e:
            cls._logger.error(f"Failed to create {backend_name} backend: {e}")
            
            # Add backend-specific troubleshooting advice
            troubleshooting = []
            if backend_name == "redis":
                troubleshooting.extend([
                    "Ensure Redis server is running and accessible",
                    "Verify REDIS_URL or connection settings are correct",
                    "Check network connectivity and firewall rules",
                    "Verify Redis authentication credentials if required"
                ])
            elif backend_name == "sqlite":
                troubleshooting.extend([
                    "Ensure database directory exists and is writable",
                    "Check available disk space",
                    "Verify file permissions for database path",
                    "Ensure SQLite is properly installed"
                ])
            elif backend_name == "vector":
                troubleshooting.extend([
                    "Check vector store configuration and dependencies",
                    "Verify embedding provider settings",
                    "Ensure vector store service is accessible"
                ])
            
            error_details = {
                "backend": backend_name,
                "settings": config.settings,
                "attempted_backends": attempted_backends,
                "troubleshooting": troubleshooting,
                "original_error": str(e)
            }
            
            raise MemoryBackendError(
                f"Failed to create {backend_name} backend: {e}",
                backend=backend_name,
                details=error_details
            ) from e
    
    @classmethod
    def create_manager(cls, config: MemoryConfiguration) -> IMemoryManager:
        """Create a memory manager from configuration"""
        
        if not config.enabled:
            raise ValueError("Cannot create manager: memory is disabled")
        
        # Create backend
        backend = cls.create_backend(config)
        
        # Create manager
        manager = MemoryManager(backend)
        
        # Configure manager based on settings
        if hasattr(manager, '_cleanup_interval'):
            manager._cleanup_interval = config.cleanup_interval
        
        cls._logger.info(f"Created memory manager with {backend.backend_type.value} backend")
        return manager
    
    @classmethod
    def _auto_select_backend(cls, config: MemoryConfiguration) -> str:
        """Automatically select the best backend for the environment"""
        
        # Development/testing preference
        if config.debug_mode:
            return "in_memory"
        
        # Check for Redis availability with actual connection test
        redis_env_vars = os.getenv("REDIS_URL") or os.getenv("REDIS_HOST")
        if redis_env_vars:
            try:
                import redis
            except ImportError:
                raise MemoryBackendError(
                    "Redis environment variables detected but 'redis' package not installed. "
                    "Install with: pip install redis"
                )
            
            # Test actual Redis connection
            if not cls._test_redis_connection():
                raise MemoryBackendError(
                    f"Redis environment variables found ({redis_env_vars}) but connection failed. "
                    "Check Redis server status and network connectivity."
                )
            
            cls._logger.info("Redis connection verified, selecting Redis backend")
            return "redis"
        
        # Default to SQLite with validation
        cls._logger.info("No Redis configuration found, selecting SQLite backend")
        return "sqlite"
    
    @classmethod
    def list_backends(cls) -> List[str]:
        """List available memory backends"""
        return list(cls._backend_registry.keys())
    
    @classmethod
    def get_backend_info(cls, backend_name: str) -> Dict[str, Any]:
        """Get information about a specific backend"""
        if backend_name not in cls._backend_registry:
            raise ValueError(f"Unknown backend: {backend_name}")
        
        backend_class = cls._backend_registry[backend_name]
        
        return {
            "name": backend_name,
            "class": backend_class.__name__,
            "module": backend_class.__module__,
            "type": getattr(backend_class, "backend_type", None),
            "available": cls._check_backend_availability(backend_name)
        }
    
    @classmethod
    def _test_redis_connection(cls) -> bool:
        """Test if Redis is actually reachable"""
        try:
            import redis
            
            # Build Redis URL from environment
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                host = os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", "6379"))
                db = int(os.getenv("REDIS_DB", "0"))
                password = os.getenv("REDIS_PASSWORD")
                
                if password:
                    redis_url = f"redis://:{password}@{host}:{port}/{db}"
                else:
                    redis_url = f"redis://{host}:{port}/{db}"
            
            # Test connection with short timeout
            client = redis.from_url(
                redis_url,
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=False
            )
            client.ping()
            client.close()
            return True
            
        except Exception as e:
            cls._logger.debug(f"Redis connection test failed: {e}")
            return False
    
    @classmethod
    def _check_backend_availability(cls, backend_name: str) -> bool:
        """Check if a backend is available (dependencies installed, etc.)"""
        
        if backend_name == "redis":
            try:
                import redis
                return cls._test_redis_connection()
            except ImportError:
                return False
        
        # Most backends are always available
        return True


# Convenience functions for common usage patterns

def create_memory_manager(
    config: Union[bool, str, Dict[str, Any], MemoryConfiguration]
) -> Optional[IMemoryManager]:
    """
    Create a memory manager with simplified configuration.
    
    Examples:
        # Development
        manager = create_memory_manager("development")
        
        # Production
        manager = create_memory_manager("production")
        
        # Custom
        manager = create_memory_manager({
            "backend": "redis",
            "settings": {"url": "redis://localhost:6379"}
        })
    
    Raises:
        MemoryConfigurationError: If configuration is invalid
        MemoryBackendError: If backend creation/connection fails
        ValueError: If memory is disabled in configuration
    """
    
    if isinstance(config, MemoryConfiguration):
        memory_config = config
    else:
        memory_config = MemoryConfiguration.from_simple_config(config)
    
    if not memory_config.enabled:
        return None
    
    # Fail fast - don't catch exceptions, let them propagate with context
    try:
        return MemoryFactory.create_manager(memory_config)
    except Exception as e:
        # Add context and re-raise instead of returning None
        logger = logging.getLogger(__name__)
        logger.error(f"Memory manager creation failed: {e}")
        logger.error(f"Configuration: backend={memory_config.backend}, settings={memory_config.settings}")
        
        # Provide helpful troubleshooting information
        if memory_config.backend == "redis" or (memory_config.backend == "auto" and (os.getenv("REDIS_URL") or os.getenv("REDIS_HOST"))):
            logger.error("Redis connection failed. Check:")
            logger.error("  - Redis server is running and accessible")
            logger.error("  - REDIS_URL or REDIS_HOST environment variables are correct")
            logger.error("  - Network connectivity and firewall settings")
            logger.error("  - Redis authentication credentials")
        elif memory_config.backend == "sqlite":
            logger.error("SQLite setup failed. Check:")
            logger.error("  - Database directory is writable")
            logger.error("  - Sufficient disk space available")
            logger.error("  - No file permission issues")
        
        raise MemoryBackendError(f"Failed to create memory manager: {e}") from e


def create_memory_backend(
    backend_type: str,
    **settings
) -> IMemoryBackend:
    """
    Create a memory backend with direct configuration.
    
    Examples:
        # SQLite
        backend = create_memory_backend("sqlite", db_path="memory.db")
        
        # Redis
        backend = create_memory_backend("redis", url="redis://localhost:6379")
    """
    
    config = MemoryConfiguration(
        enabled=True,
        backend=backend_type,
        settings=settings
    )
    
    return MemoryFactory.create_backend(config)


# Global memory manager instance
_global_memory_manager: Optional[IMemoryManager] = None


def setup_global_memory(
    config: Union[bool, str, Dict[str, Any], MemoryConfiguration]
) -> bool:
    """
    Setup the global memory manager.
    
    Args:
        config: Memory configuration
        
    Returns:
        True if setup was successful (including when memory is disabled)
        
    Raises:
        MemoryBackendError: If memory setup fails when enabled
    """
    global _global_memory_manager
    
    # Let exceptions propagate instead of catching and returning False
    _global_memory_manager = create_memory_manager(config)
    
    if _global_memory_manager:
        logging.getLogger(__name__).info("Global memory manager setup complete")
        return True
    else:
        logging.getLogger(__name__).info("Memory disabled - global manager not created")
        return True  # Not an error to have memory disabled


def get_global_memory_manager() -> Optional[IMemoryManager]:
    """Get the global memory manager instance"""
    return _global_memory_manager


def teardown_global_memory():
    """Teardown the global memory manager"""
    global _global_memory_manager
    
    if _global_memory_manager:
        # Note: In async environment, you'd want to await manager.stop()
        _global_memory_manager = None
        logging.getLogger(__name__).info("Global memory manager torn down")
