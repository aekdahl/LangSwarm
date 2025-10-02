# Memory System Fallback Improvements - Implementation Plan

## Problem Statement
The LangSwarm v2 memory system uses fallback mechanisms that can hide real errors, potentially causing silent failures in production environments.

## Key Issues Identified

### 1. Silent Manager Creation Failures
**File:** `langswarm/v2/core/memory/factory.py:404-408`
```python
def create_memory_manager(config) -> Optional[IMemoryManager]:
    try:
        return MemoryFactory.create_manager(memory_config)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create memory manager: {e}")
        return None  # 🚨 PROBLEM: Returns None instead of failing
```

### 2. Global Memory Setup Fallbacks
**File:** `langswarm/v2/core/memory/factory.py:453-465`
```python
def setup_global_memory(config) -> bool:
    if _global_memory_manager:
        return True
    else:
        logging.getLogger(__name__).info("Memory disabled - global manager not created")
        return True  # 🚨 PROBLEM: Treats failure as success
```

### 3. Auto-Selection Only Checks Import, Not Connection
**File:** `langswarm/v2/core/memory/factory.py:327-336`
```python
def _auto_select_backend(cls, config: MemoryConfiguration) -> str:
    try:
        import redis  # 🚨 PROBLEM: Only checks import, not connection
        if os.getenv("REDIS_URL") or os.getenv("REDIS_HOST"):
            return "redis"
    except ImportError:
        pass
    return "sqlite"  # 🚨 PROBLEM: Silent fallback
```

### 4. Vector Store Silent Fallbacks
**File:** `langswarm/v2/core/memory/vector_stores/factory.py:363-368`
```python
for store_type, check_available in store_preferences:
    try:
        # Create store...
    except Exception as e:
        logger.warning(f"Failed to create {store_type} store: {e}")
        continue  # 🚨 PROBLEM: Silent fallback to next option
```

## Recommended Implementation

### Phase 1: Add Strict Mode Configuration

1. **Update MemoryConfiguration**
   ```python
   @dataclass
   class MemoryConfiguration:
       # Existing fields...
       strict_mode: bool = False  # When True, fail fast instead of fallback
       validate_connections: bool = True  # Test connections during auto-selection
   ```

2. **Modify create_memory_manager**
   ```python
   def create_memory_manager(
       config: Union[bool, str, Dict[str, Any], MemoryConfiguration],
       strict_mode: Optional[bool] = None
   ) -> Optional[IMemoryManager]:
       if isinstance(config, MemoryConfiguration):
           memory_config = config
       else:
           memory_config = MemoryConfiguration.from_simple_config(config)
       
       # Override strict mode if explicitly provided
       if strict_mode is not None:
           memory_config.strict_mode = strict_mode
       
       if not memory_config.enabled:
           return None
       
       try:
           return MemoryFactory.create_manager(memory_config)
       except Exception as e:
           if memory_config.strict_mode:
               raise  # Fail fast in strict mode
           else:
               logging.getLogger(__name__).error(f"Failed to create memory manager: {e}")
               logging.getLogger(__name__).warning("Continuing without memory (set strict_mode=True to fail fast)")
               return None
   ```

3. **Update Auto-Selection with Connection Testing**
   ```python
   @classmethod
   def _auto_select_backend(cls, config: MemoryConfiguration) -> str:
       # Development/testing preference
       if config.debug_mode:
           return "in_memory"
       
       # Check for Redis availability with connection test
       if config.validate_connections:
           try:
               import redis
               if os.getenv("REDIS_URL") or os.getenv("REDIS_HOST"):
                   # Test actual connection
                   if cls._test_redis_connection(config):
                       return "redis"
                   elif config.strict_mode:
                       raise ConnectionError("Redis environment variables found but connection failed")
           except ImportError:
               if config.strict_mode and (os.getenv("REDIS_URL") or os.getenv("REDIS_HOST")):
                   raise ImportError("Redis environment variables found but redis package not installed")
       
       # Default to SQLite
       return "sqlite"
   
   @classmethod
   def _test_redis_connection(cls, config: MemoryConfiguration) -> bool:
       """Test if Redis is actually reachable"""
       try:
           import redis
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
           
           client = redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
           client.ping()
           client.close()
           return True
       except Exception:
           return False
   ```

### Phase 2: Enhanced Error Reporting

1. **Add Backend Creation Context**
   ```python
   @classmethod
   def create_backend(cls, config: MemoryConfiguration) -> IMemoryBackend:
       if not config.enabled:
           raise ValueError("Cannot create backend: memory is disabled")
       
       # Validate configuration
       errors = config.validate()
       if errors:
           raise ValueError(f"Invalid memory configuration: {'; '.join(errors)}")
       
       backend_name = config.backend
       attempted_backends = []
       
       # Auto-select backend
       if backend_name == "auto":
           backend_name, attempted_backends = cls._auto_select_backend_with_context(config)
       
       # Create backend with detailed error context
       try:
           backend_class = cls._backend_registry[backend_name]
           backend = backend_class(config.settings)
           cls._logger.info(f"Created {backend_name} memory backend")
           return backend
       except Exception as e:
           error_context = {
               "requested_backend": config.backend,
               "selected_backend": backend_name,
               "attempted_backends": attempted_backends,
               "available_backends": list(cls._backend_registry.keys()),
               "config_settings": config.settings
           }
           cls._logger.error(f"Failed to create {backend_name} backend: {e}")
           cls._logger.error(f"Context: {error_context}")
           
           if config.strict_mode:
               raise MemoryBackendCreationError(
                   f"Failed to create {backend_name} backend: {e}",
                   context=error_context
               ) from e
           else:
               raise
   ```

2. **Add Custom Exception Types**
   ```python
   class MemoryBackendCreationError(Exception):
       def __init__(self, message: str, context: Dict[str, Any] = None):
           super().__init__(message)
           self.context = context or {}
   
   class MemoryConnectionError(Exception):
       def __init__(self, backend: str, details: str):
           super().__init__(f"Failed to connect to {backend}: {details}")
           self.backend = backend
           self.details = details
   ```

### Phase 3: Configuration Validation

1. **Add Validation Methods**
   ```python
   def validate_memory_configuration(
       config: Union[bool, str, Dict[str, Any], MemoryConfiguration]
   ) -> List[str]:
       """Validate memory configuration and return list of issues"""
       if isinstance(config, MemoryConfiguration):
           memory_config = config
       else:
           memory_config = MemoryConfiguration.from_simple_config(config)
       
       issues = []
       
       # Validate basic configuration
       config_errors = memory_config.validate()
       issues.extend(config_errors)
       
       # Test backend availability
       if memory_config.backend == "auto":
           backend_name = MemoryFactory._auto_select_backend(memory_config)
           issues.extend(_validate_backend_connection(backend_name, memory_config))
       else:
           issues.extend(_validate_backend_connection(memory_config.backend, memory_config))
       
       return issues
   
   def _validate_backend_connection(backend_name: str, config: MemoryConfiguration) -> List[str]:
       """Validate that a specific backend can be connected to"""
       issues = []
       
       if backend_name == "redis":
           if not MemoryFactory._test_redis_connection(config):
               issues.append("Redis backend selected but connection test failed")
       elif backend_name == "sqlite":
           # Test SQLite path writability
           db_path = config.settings.get("db_path", "langswarm_memory.db")
           if db_path != ":memory:":
               try:
                   Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                   # Test write access
                   test_path = Path(db_path).parent / ".test_write"
                   test_path.write_text("test")
                   test_path.unlink()
               except Exception as e:
                   issues.append(f"SQLite database path not writable: {e}")
       
       return issues
   ```

## Migration Strategy

### Backward Compatibility
- Default behavior remains unchanged (`strict_mode=False`)
- Existing code continues to work
- New `strict_mode` is opt-in

### Environment-Based Defaults
```python
def get_default_strict_mode() -> bool:
    """Get default strict mode based on environment"""
    env = os.getenv("LANGSWARM_ENV", "development").lower()
    return env in ["production", "prod", "staging"]
```

### Documentation Updates
1. Update memory configuration docs to explain strict mode
2. Add troubleshooting guide for common connection issues
3. Provide migration examples for production deployments

## Testing Strategy

### Unit Tests
- Test strict mode behavior
- Test connection validation
- Test error message quality

### Integration Tests
- Test with actual Redis/SQLite failures
- Verify fallback behavior in both modes
- Test configuration validation

### Production Testing
- Add health check endpoints
- Monitor fallback metrics
- Alert on backend selection changes

## Implementation Priority

1. **High Priority** (Week 1)
   - Add strict_mode configuration
   - Improve create_memory_manager error handling
   - Add connection testing to auto-selection

2. **Medium Priority** (Week 2)
   - Enhanced error reporting with context
   - Configuration validation methods
   - Custom exception types

3. **Low Priority** (Week 3)
   - Environment-based defaults
   - Documentation updates
   - Additional health checks
