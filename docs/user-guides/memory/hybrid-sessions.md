---
title: 'Hybrid Session Management'
description: 'Learn how LangSwarm combines native provider sessions with local persistence for robust, unified state management.'
---

# Hybrid Session Management

LangSwarm V2 introduces **Hybrid Session Management**, a powerful layer that unifies stateful and stateless LLM providers into a single, cohesive interface. This system allows you to use providers like Claude and Gemini with the same persistence guarantees as OpenAI Assistants.

## Overview

The `LangSwarmSessionManager` (and its `SessionManager` implementation) intelligently handles session state based on the provider's capabilities:

1.  **Native Mode**: For providers with built-in state (e.g., OpenAI Threads), it largely delegates state management to the provider while mirroring messages locally for backup.
2.  **Hybrid Mode**: For stateless providers (e.g., Claude, Gemini, Cohere), it simulates a stateful session by managing conversation history locally and injecting it into each API call. It also persists this history to a local database (SQLite) or other storage backends.

## Key Features

*   **Unified API**: Use `create_session`, `send_message`, and `get_history` uniformly across all providers.
*   **Automatic Hydration**: When your application restarts, LangSwarm automatically "hydrates" the in-memory state of stateless providers from your persistent storage.
*   **Provider Agostic**: Switch between OpenAI (Stateful) and Claude (Stateless) without changing your application logic.

## Usage

### 1. Basic Setup

To use Hybrid Sessions, initialize the `SessionManager` and create a session with the `HYBRID` backend.

```python
from langswarm.core.session import SessionManager, SessionBackend
from langswarm.core.session.storage import SQLiteSessionStorage

# 1. Initialize Storage (Persistent)
storage = SQLiteSessionStorage(db_path="my_app_sessions.db")

# 2. Initialize Manager
manager = SessionManager(storage=storage)

# 3. Create a Hybrid Session (e.g., with Claude)
session = await manager.create_session(
    user_id="user_123",
    provider="anthropic", # or "gemini", "cohere", "mistral"
    model="claude-3-5-sonnet-20241022",
    backend=SessionBackend.HYBRID 
)

print(f"Session Created: {session.session_id}")
```

### 2. Sending Messages

Interaction is identical regardless of the underlying provider backend.

```python
# Send a message
response = await session.send_message("Explain quantum computing in one sentence.")
print(f"AI: {response.content}")

# The session state is now:
# 1. Updated in the in-memory provider adapter.
# 2. Persisted to 'my_app_sessions.db'.
```

### 3. Resuming Sessions (Hydration)

If your application restarts, you can resume the conversation seamlessly.

```python
# ... restart application ...

# Re-initialize manager with SAME storage
manager = SessionManager(storage=SQLiteSessionStorage("my_app_sessions.db"))

# Load the session by ID
resumed_session = await manager.get_session("session_user_123_abcd...")

if resumed_session:
    # continue conversation - context is fully restored!
    response = await resumed_session.send_message("What was my previous question?")
    print(f"AI: {response.content}") 
```

## Supported Providers

| Provider | Type | API Used | Hybrid Support |
| :--- | :--- | :--- | :--- |
| **OpenAI** | Stateful | Threads API | Native / Backup |
| **Mistral** | Stateful* | Conversations API | Native / Hybrid |
| **Anthropic** | Stateless | Messages API | **Full Hybrid** |
| **Gemini** | Stateless | Generative API | **Full Hybrid** |
| **Cohere** | Stateless | Chat API | **Full Hybrid** |

*\* Mistral support is currently implemented as Hybrid wrapper around the client, ready for native state integration.*

## Advanced Configuration

### Custom Storage
You can implement `ISessionStorage` to use Redis, Postgres, or any other backend.

```python
class RedisStorage(ISessionStorage):
   # ... implement save/load/delete ...
```

### Session Middleware
Add middleware to intercept and modify messages before they are processed or saved.

```python
class PIIFilterMiddleware(ISessionMiddleware):
    async def process_outgoing_message(self, session, message):
        # scrub PII
        return message

session.add_middleware(PIIFilterMiddleware())
```
