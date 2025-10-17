# Core Session API

**Module:** `langswarm.core.session`

## Overview

LangSwarm V2 Session Management

Modern, provider-aligned session management system that replaces the complex
V1 session system with a clean, efficient implementation leveraging native
LLM provider capabilities.

Key Features:
- Provider-native session support (OpenAI threads, Anthropic conversations)
- Simple, unified API across all providers
- Efficient storage backends (in-memory, SQLite)
- Session lifecycle management
- Message persistence and retrieval
- Metrics and analytics

Usage:
    from langswarm.core.session import SessionManager, create_session_manager
    
    # Create session manager
    manager = create_session_manager(storage="sqlite")
    
    # Create session
    session = await manager.create_session("user123", "openai", "gpt-4o")
    
    # Send message
    response = await session.send_message("Hello!")
    
    # Get conversation history
    messages = await session.get_messages()

## Table of Contents

### Functions
- [configure_development_sessions](#configure_development_sessions)
- [configure_production_sessions](#configure_production_sessions)
- [create_provider_session](#create_provider_session)
- [create_session_manager](#create_session_manager)
- [create_simple_session](#create_simple_session)
- [get_session_manager](#get_session_manager)
- [initialize_default_session_manager](#initialize_default_session_manager)
- [session_context](#session_context)
- [set_session_manager](#set_session_manager)

### Classes
- [LoggingMiddleware](#loggingmiddleware)
- [MetricsHook](#metricshook)
- [SessionContext](#sessioncontext)

## Functions

### configure_development_sessions

```python
def configure_development_sessions() -> langswarm.core.session.base.SessionManager
```

Configure session manager for development

**Returns:**

`SessionManager`


### configure_production_sessions

```python
def configure_production_sessions(storage_config: Optional[Dict[str, Any]] = None, providers: Optional[Dict[str, str]] = None) -> langswarm.core.session.base.SessionManager
```

Configure session manager for production

**Parameters:**

- `storage_config`: `Optional = None`
- `providers`: `Optional = None`

**Returns:**

`SessionManager`


### create_provider_session

```python
def create_provider_session(provider: str, api_key: str, **kwargs) -> langswarm.core.session.interfaces.IProviderSession
```

Create a provider session instance.

Args:
    provider: Provider name
    api_key: Provider API key
    **kwargs: Provider-specific configuration
    
Returns:
    Provider session instance

**Parameters:**

- `provider`: `str`
- `api_key`: `str`
- `kwargs`: `Any`

**Returns:**

`IProviderSession`


### create_session_manager

```python
def create_session_manager(storage: str = 'sqlite', storage_config: Optional[Dict[str, Any]] = None, providers: Optional[Dict[str, str]] = None) -> langswarm.core.session.base.SessionManager
```

Create a session manager with specified configuration.

Args:
    storage: Storage backend type ("memory", "sqlite")
    storage_config: Storage-specific configuration
    providers: Provider API keys {"openai": "sk-...", "anthropic": "sk-..."}
    
Returns:
    Configured session manager

**Parameters:**

- `storage`: `str = 'sqlite'`
- `storage_config`: `Optional = None`
- `providers`: `Optional = None`

**Returns:**

`SessionManager`


### create_simple_session

```python
async def create_simple_session(user_id: str, provider: str = 'mock', model: str = 'gpt-4o', api_key: Optional[str] = None, storage: str = 'memory') -> langswarm.core.session.base.BaseSession
```

Create a simple session for quick testing.

Args:
    user_id: User identifier
    provider: LLM provider
    model: Model name
    api_key: Provider API key
    storage: Storage backend
    
Returns:
    Created session

**Parameters:**

- `user_id`: `str`
- `provider`: `str = 'mock'`
- `model`: `str = 'gpt-4o'`
- `api_key`: `Optional = None`
- `storage`: `str = 'memory'`

**Returns:**

`BaseSession`


### get_session_manager

```python
def get_session_manager() -> Optional[langswarm.core.session.base.SessionManager]
```

Get the global session manager instance

**Returns:**

`Optional`


### initialize_default_session_manager

```python
def initialize_default_session_manager()
```

Initialize default session manager


### session_context

```python
def session_context(session: langswarm.core.session.interfaces.ISession) -> langswarm.core.session.SessionContext
```

Create session context manager

**Parameters:**

- `session`: `ISession`

**Returns:**

`SessionContext`


### set_session_manager

```python
def set_session_manager(manager: langswarm.core.session.base.SessionManager)
```

Set the global session manager instance

**Parameters:**

- `manager`: `SessionManager`


## Classes

### LoggingMiddleware

```python
class LoggingMiddleware(ISessionMiddleware)
```

Simple logging middleware for sessions

**Methods:**

#### process_incoming_message

```python
async def process_incoming_message(self, session: langswarm.core.session.interfaces.ISession, message: langswarm.core.session.interfaces.SessionMessage) -> langswarm.core.session.interfaces.SessionMessage
```

Log incoming messages

**Parameters:**

- `session`: `ISession`
- `message`: `SessionMessage`

**Returns:**

`SessionMessage`

#### process_outgoing_message

```python
async def process_outgoing_message(self, session: langswarm.core.session.interfaces.ISession, message: langswarm.core.session.interfaces.SessionMessage) -> langswarm.core.session.interfaces.SessionMessage
```

Log outgoing messages

**Parameters:**

- `session`: `ISession`
- `message`: `SessionMessage`

**Returns:**

`SessionMessage`


### MetricsHook

```python
class MetricsHook(ISessionLifecycleHook)
```

Simple metrics collection hook

**Methods:**

#### get_metrics

```python
def get_metrics(self) -> Dict[str, int]
```

Get collected metrics

**Parameters:**


**Returns:**

`Dict`

#### on_message_received

```python
async def on_message_received(self, session: langswarm.core.session.interfaces.ISession, message: langswarm.core.session.interfaces.SessionMessage) -> None
```

Track message receiving

**Parameters:**

- `session`: `ISession`
- `message`: `SessionMessage`

**Returns:**

`None`

#### on_message_sent

```python
async def on_message_sent(self, session: langswarm.core.session.interfaces.ISession, message: langswarm.core.session.interfaces.SessionMessage) -> None
```

Track message sending

**Parameters:**

- `session`: `ISession`
- `message`: `SessionMessage`

**Returns:**

`None`

#### on_session_archived

```python
async def on_session_archived(self, session: langswarm.core.session.interfaces.ISession) -> None
```

Track session archiving

**Parameters:**

- `session`: `ISession`

**Returns:**

`None`

#### on_session_created

```python
async def on_session_created(self, session: langswarm.core.session.interfaces.ISession) -> None
```

Track session creation

**Parameters:**

- `session`: `ISession`

**Returns:**

`None`

#### on_session_deleted

```python
async def on_session_deleted(self, session: langswarm.core.session.interfaces.ISession) -> None
```

Track session deletion

**Parameters:**

- `session`: `ISession`

**Returns:**

`None`


### SessionContext

```python
class SessionContext
```

Context manager for session operations

