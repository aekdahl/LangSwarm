# Langswarm_Memory Interfaces API

**Module:** `langswarm_memory.interfaces`

## Overview

Memory Interfaces for langswarm-memory

Unified, clean interfaces for memory management that align with major LLM
providers and provide a consistent experience across all memory backends.

## Table of Contents

### Classes
- [ConversationSummary](#conversationsummary)
- [IMemoryBackend](#imemorybackend)
- [IMemoryManager](#imemorymanager)
- [IMemoryMigrator](#imemorymigrator)
- [IMemoryProvider](#imemoryprovider)
- [IMemorySession](#imemorysession)
- [MemoryBackendType](#memorybackendtype)
- [MemoryUsage](#memoryusage)
- [Message](#message)
- [MessageRole](#messagerole)
- [SessionMetadata](#sessionmetadata)
- [SessionStatus](#sessionstatus)

## Classes

### ConversationSummary

```python
class ConversationSummary
```

Conversation summary for memory optimization


### IMemoryBackend

```python
class IMemoryBackend(ABC)
```

Interface for memory backend implementations

**Methods:**

#### cleanup_expired_sessions

```python
async def cleanup_expired_sessions(self) -> int
```

Clean up expired sessions, return count deleted

**Parameters:**


**Returns:**

`int`

#### connect

```python
async def connect(self) -> bool
```

Connect to the memory backend

**Parameters:**


**Returns:**

`bool`

#### create_session

```python
async def create_session(self, metadata: langswarm_memory.interfaces.SessionMetadata) -> langswarm_memory.interfaces.IMemorySession
```

Create a new memory session

**Parameters:**

- `metadata`: `SessionMetadata`

**Returns:**

`IMemorySession`

#### delete_session

```python
async def delete_session(self, session_id: str) -> bool
```

Delete a session and all its data

**Parameters:**

- `session_id`: `str`

**Returns:**

`bool`

#### disconnect

```python
async def disconnect(self) -> bool
```

Disconnect from the memory backend

**Parameters:**


**Returns:**

`bool`

#### get_session

```python
async def get_session(self, session_id: str) -> Optional[langswarm_memory.interfaces.IMemorySession]
```

Get an existing memory session

**Parameters:**

- `session_id`: `str`

**Returns:**

`Optional`

#### get_usage_stats

```python
async def get_usage_stats(self) -> langswarm_memory.interfaces.MemoryUsage
```

Get memory usage statistics

**Parameters:**


**Returns:**

`MemoryUsage`

#### health_check

```python
async def health_check(self) -> Dict[str, Any]
```

Get backend health status

**Parameters:**


**Returns:**

`Dict`

#### list_sessions

```python
async def list_sessions(self, user_id: Optional[str] = None, status: Optional[langswarm_memory.interfaces.SessionStatus] = None, limit: int = 100, offset: int = 0) -> List[langswarm_memory.interfaces.SessionMetadata]
```

List sessions with filtering

**Parameters:**

- `user_id`: `Optional = None`
- `status`: `Optional = None`
- `limit`: `int = 100`
- `offset`: `int = 0`

**Returns:**

`List`


### IMemoryManager

```python
class IMemoryManager(ABC)
```

Interface for unified memory management

**Methods:**

#### cleanup_expired_sessions

```python
async def cleanup_expired_sessions(self) -> int
```

Clean up expired sessions

**Parameters:**


**Returns:**

`int`

#### create_session

```python
async def create_session(self, session_id: Optional[str] = None, user_id: Optional[str] = None, agent_id: Optional[str] = None, **kwargs) -> langswarm_memory.interfaces.IMemorySession
```

Create a new memory session

**Parameters:**

- `session_id`: `Optional = None`
- `user_id`: `Optional = None`
- `agent_id`: `Optional = None`
- `kwargs`: `Any`

**Returns:**

`IMemorySession`

#### delete_session

```python
async def delete_session(self, session_id: str) -> bool
```

Delete a session

**Parameters:**

- `session_id`: `str`

**Returns:**

`bool`

#### get_or_create_session

```python
async def get_or_create_session(self, session_id: str, user_id: Optional[str] = None, agent_id: Optional[str] = None, **kwargs) -> langswarm_memory.interfaces.IMemorySession
```

Get existing session or create new one

**Parameters:**

- `session_id`: `str`
- `user_id`: `Optional = None`
- `agent_id`: `Optional = None`
- `kwargs`: `Any`

**Returns:**

`IMemorySession`

#### get_session

```python
async def get_session(self, session_id: str) -> Optional[langswarm_memory.interfaces.IMemorySession]
```

Get or restore a memory session

**Parameters:**

- `session_id`: `str`

**Returns:**

`Optional`

#### get_system_stats

```python
async def get_system_stats(self) -> Dict[str, Any]
```

Get system memory statistics

**Parameters:**


**Returns:**

`Dict`

#### list_user_sessions

```python
async def list_user_sessions(self, user_id: str, status: Optional[langswarm_memory.interfaces.SessionStatus] = None, limit: int = 50) -> List[langswarm_memory.interfaces.SessionMetadata]
```

List sessions for a user

**Parameters:**

- `user_id`: `str`
- `status`: `Optional = None`
- `limit`: `int = 50`

**Returns:**

`List`


### IMemoryMigrator

```python
class IMemoryMigrator(ABC)
```

Interface for memory data migration

**Methods:**

#### backup_data

```python
async def backup_data(self, backend: langswarm_memory.interfaces.IMemoryBackend, backup_path: str) -> bool
```

Backup memory data

**Parameters:**

- `backend`: `IMemoryBackend`
- `backup_path`: `str`

**Returns:**

`bool`

#### migrate_from_v1

```python
async def migrate_from_v1(self, source_config: Dict[str, Any], target_backend: langswarm_memory.interfaces.IMemoryBackend, progress_callback: Optional[Callable] = None) -> Dict[str, Any]
```

Migrate memory data from V1 system

**Parameters:**

- `source_config`: `Dict`
- `target_backend`: `IMemoryBackend`
- `progress_callback`: `Optional = None`

**Returns:**

`Dict`

#### restore_data

```python
async def restore_data(self, backend: langswarm_memory.interfaces.IMemoryBackend, backup_path: str) -> bool
```

Restore memory data from backup

**Parameters:**

- `backend`: `IMemoryBackend`
- `backup_path`: `str`

**Returns:**

`bool`

#### validate_migration

```python
async def validate_migration(self, source_config: Dict[str, Any], target_backend: langswarm_memory.interfaces.IMemoryBackend) -> Dict[str, Any]
```

Validate migration without performing it

**Parameters:**

- `source_config`: `Dict`
- `target_backend`: `IMemoryBackend`

**Returns:**

`Dict`


### IMemoryProvider

```python
class IMemoryProvider(ABC)
```

Interface for specialized memory providers (e.g., MemoryPro)

**Methods:**

#### analyze_conversation

```python
async def analyze_conversation(self, messages: List[langswarm_memory.interfaces.Message]) -> Dict[str, Any]
```

Analyze conversation for insights

**Parameters:**

- `messages`: `List`

**Returns:**

`Dict`

#### extract_entities

```python
async def extract_entities(self, messages: List[langswarm_memory.interfaces.Message]) -> List[Dict[str, Any]]
```

Extract entities from conversation

**Parameters:**

- `messages`: `List`

**Returns:**

`List`

#### get_insights

```python
async def get_insights(self, session: langswarm_memory.interfaces.IMemorySession) -> Dict[str, Any]
```

Get conversation insights and analytics

**Parameters:**

- `session`: `IMemorySession`

**Returns:**

`Dict`

#### suggest_actions

```python
async def suggest_actions(self, session: langswarm_memory.interfaces.IMemorySession) -> List[Dict[str, Any]]
```

Suggest actions based on conversation history

**Parameters:**

- `session`: `IMemorySession`

**Returns:**

`List`


### IMemorySession

```python
class IMemorySession(ABC)
```

Interface for memory session management

**Methods:**

#### add_message

```python
async def add_message(self, message: langswarm_memory.interfaces.Message) -> bool
```

Add a message to the session

**Parameters:**

- `message`: `Message`

**Returns:**

`bool`

#### clear_messages

```python
async def clear_messages(self, keep_system: bool = True) -> bool
```

Clear messages from session

**Parameters:**

- `keep_system`: `bool = True`

**Returns:**

`bool`

#### close

```python
async def close(self) -> bool
```

Close the session

**Parameters:**


**Returns:**

`bool`

#### create_summary

```python
async def create_summary(self, force: bool = False) -> Optional[langswarm_memory.interfaces.ConversationSummary]
```

Create conversation summary

**Parameters:**

- `force`: `bool = False`

**Returns:**

`Optional`

#### get_messages

```python
async def get_messages(self, limit: Optional[int] = None, include_system: bool = True, since: Optional[datetime.datetime] = None) -> List[langswarm_memory.interfaces.Message]
```

Get messages from the session

**Parameters:**

- `limit`: `Optional = None`
- `include_system`: `bool = True`
- `since`: `Optional = None`

**Returns:**

`List`

#### get_recent_context

```python
async def get_recent_context(self, max_tokens: Optional[int] = None) -> List[langswarm_memory.interfaces.Message]
```

Get recent messages that fit within token limit

**Parameters:**

- `max_tokens`: `Optional = None`

**Returns:**

`List`

#### get_summary

```python
async def get_summary(self) -> Optional[langswarm_memory.interfaces.ConversationSummary]
```

Get conversation summary if available

**Parameters:**


**Returns:**

`Optional`

#### update_metadata

```python
async def update_metadata(self, **kwargs) -> bool
```

Update session metadata

**Parameters:**

- `kwargs`: `Any`

**Returns:**

`bool`


### MemoryBackendType

```python
class MemoryBackendType(Enum)
```

Supported memory backend types


### MemoryUsage

```python
class MemoryUsage
```

Memory usage statistics


### Message

```python
class Message
```

Universal message format aligned with LLM provider patterns

**Methods:**

#### to_anthropic_format

```python
def to_anthropic_format(self) -> Dict[str, Any]
```

Convert to Anthropic message format

**Parameters:**


**Returns:**

`Dict`

#### to_dict

```python
def to_dict(self) -> Dict[str, Any]
```

Convert to dictionary format

**Parameters:**


**Returns:**

`Dict`

#### to_openai_format

```python
def to_openai_format(self) -> Dict[str, Any]
```

Convert to OpenAI message format

**Parameters:**


**Returns:**

`Dict`


### MessageRole

```python
class MessageRole(Enum)
```

Message roles aligned with LLM provider conventions


### SessionMetadata

```python
class SessionMetadata
```

Session metadata and configuration

**Methods:**

#### is_expired

```python
def is_expired(self) -> bool
```

Check if session is expired

**Parameters:**


**Returns:**

`bool`

#### update_timestamp

```python
def update_timestamp(self)
```

Update the last updated timestamp

**Parameters:**



### SessionStatus

```python
class SessionStatus(Enum)
```

Session status states

