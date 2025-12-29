# Langswarm_Memory Backends API

**Module:** `langswarm_memory.backends`

## Overview

Memory Backend Implementations for langswarm-memory

Concrete implementations of memory backends for different storage systems.
Provides SQLite, Redis, BigQuery, PostgreSQL, MongoDB, Elasticsearch backends.

## Table of Contents

### Classes
- [BigQueryBackend](#bigquerybackend)
- [BigQuerySession](#bigquerysession)
- [ElasticsearchBackend](#elasticsearchbackend)
- [ElasticsearchSession](#elasticsearchsession)
- [InMemoryBackend](#inmemorybackend)
- [InMemorySession](#inmemorysession)
- [MongoDBBackend](#mongodbbackend)
- [MongoDBSession](#mongodbsession)
- [PostgresBackend](#postgresbackend)
- [PostgresSession](#postgressession)
- [RedisBackend](#redisbackend)
- [RedisSession](#redissession)
- [SQLiteBackend](#sqlitebackend)
- [SQLiteSession](#sqlitesession)

## Classes

### BigQueryBackend

```python
class BigQueryBackend(BaseMemoryBackend)
```

BigQuery backend for cloud-scale persistent memory storage.
Ideal for large-scale deployments on Google Cloud Platform.

Config options:
    - project_id: GCP project ID (required)
    - dataset_id: BigQuery dataset ID (default: "langswarm_memory")
    - location: Dataset location (default: "US")
    - credentials_path: Path to service account JSON (optional, uses default if not set)

**Methods:**

#### cleanup_expired_sessions

```python
async def cleanup_expired_sessions(self) -> int
```

Clean up expired sessions

**Parameters:**


**Returns:**

`int`

#### connect

```python
async def connect(self) -> bool
```

Connect to BigQuery and ensure tables exist

**Parameters:**


**Returns:**

`bool`

#### create_session

```python
async def create_session(self, metadata: langswarm_memory.interfaces.SessionMetadata) -> langswarm_memory.interfaces.IMemorySession
```

Create a new BigQuery session

**Parameters:**

- `metadata`: `SessionMetadata`

**Returns:**

`IMemorySession`

#### delete_session

```python
async def delete_session(self, session_id: str) -> bool
```

Delete session from BigQuery

**Parameters:**

- `session_id`: `str`

**Returns:**

`bool`

#### disconnect

```python
async def disconnect(self) -> bool
```

Disconnect from BigQuery

**Parameters:**


**Returns:**

`bool`

#### get_client

```python
def get_client(self) -> google.cloud.bigquery.client.Client
```

Get BigQuery client (for internal use)

**Parameters:**


**Returns:**

`Client`

#### get_session

```python
async def get_session(self, session_id: str) -> Optional[langswarm_memory.interfaces.IMemorySession]
```

Get session from BigQuery

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

Check BigQuery connection health

**Parameters:**


**Returns:**

`Dict`

#### list_sessions

```python
async def list_sessions(self, user_id: Optional[str] = None, status: Optional[langswarm_memory.interfaces.SessionStatus] = None, limit: int = 100, offset: int = 0) -> List[langswarm_memory.interfaces.SessionMetadata]
```

List sessions from BigQuery

**Parameters:**

- `user_id`: `Optional = None`
- `status`: `Optional = None`
- `limit`: `int = 100`
- `offset`: `int = 0`

**Returns:**

`List`


### BigQuerySession

```python
class BigQuerySession(BaseMemorySession)
```

BigQuery session implementation

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


### ElasticsearchBackend

```python
class ElasticsearchBackend(BaseMemoryBackend)
```

Elasticsearch backend for search-optimized memory storage.
Ideal for deployments requiring full-text search and analytics.

Config options:
    - hosts: List of Elasticsearch hosts (default: ["http://localhost:9200"])
    - index_prefix: Prefix for indices (default: "langswarm_memory")
    - api_key: API key for authentication (optional)
    - username: Username for basic auth (optional)
    - password: Password for basic auth (optional)

**Methods:**

#### cleanup_expired_sessions

```python
async def cleanup_expired_sessions(self) -> int
```

Clean up expired sessions

**Parameters:**


**Returns:**

`int`

#### connect

```python
async def connect(self) -> bool
```

Connect to Elasticsearch and ensure indices exist

**Parameters:**


**Returns:**

`bool`

#### create_session

```python
async def create_session(self, metadata: langswarm_memory.interfaces.SessionMetadata) -> langswarm_memory.interfaces.IMemorySession
```

Create a new Elasticsearch session

**Parameters:**

- `metadata`: `SessionMetadata`

**Returns:**

`IMemorySession`

#### delete_session

```python
async def delete_session(self, session_id: str) -> bool
```

Delete session from Elasticsearch

**Parameters:**

- `session_id`: `str`

**Returns:**

`bool`

#### disconnect

```python
async def disconnect(self) -> bool
```

Disconnect from Elasticsearch

**Parameters:**


**Returns:**

`bool`

#### get_client

```python
def get_client(self) -> None
```

Get Elasticsearch client (for internal use)

**Parameters:**


**Returns:**

`None`

#### get_index_name

```python
def get_index_name(self, name: str) -> str
```

Get index name (for internal use)

**Parameters:**

- `name`: `str`

**Returns:**

`str`

#### get_session

```python
async def get_session(self, session_id: str) -> Optional[langswarm_memory.interfaces.IMemorySession]
```

Get session from Elasticsearch

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

Check Elasticsearch connection health

**Parameters:**


**Returns:**

`Dict`

#### list_sessions

```python
async def list_sessions(self, user_id: Optional[str] = None, status: Optional[langswarm_memory.interfaces.SessionStatus] = None, limit: int = 100, offset: int = 0) -> List[langswarm_memory.interfaces.SessionMetadata]
```

List sessions from Elasticsearch

**Parameters:**

- `user_id`: `Optional = None`
- `status`: `Optional = None`
- `limit`: `int = 100`
- `offset`: `int = 0`

**Returns:**

`List`


### ElasticsearchSession

```python
class ElasticsearchSession(BaseMemorySession)
```

Elasticsearch session implementation

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


### InMemoryBackend

```python
class InMemoryBackend(BaseMemoryBackend)
```

In-memory backend for development and testing.
Fast but non-persistent memory storage.

**Methods:**

#### cleanup_expired_sessions

```python
async def cleanup_expired_sessions(self) -> int
```

Clean up expired sessions

**Parameters:**


**Returns:**

`int`

#### connect

```python
async def connect(self) -> bool
```

Connect to in-memory storage

**Parameters:**


**Returns:**

`bool`

#### create_session

```python
async def create_session(self, metadata: langswarm_memory.interfaces.SessionMetadata) -> langswarm_memory.interfaces.IMemorySession
```

Create a new in-memory session

**Parameters:**

- `metadata`: `SessionMetadata`

**Returns:**

`IMemorySession`

#### delete_session

```python
async def delete_session(self, session_id: str) -> bool
```

Delete session from memory

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

Get session from memory

**Parameters:**

- `session_id`: `str`

**Returns:**

`Optional`

#### get_session_data

```python
def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]
```

Get raw session data (for internal use)

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

#### update_session_data

```python
def update_session_data(self, session_id: str, data: Dict[str, Any])
```

Update raw session data (for internal use)

**Parameters:**

- `session_id`: `str`
- `data`: `Dict`


### InMemorySession

```python
class InMemorySession(BaseMemorySession)
```

In-memory session implementation

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


### MongoDBBackend

```python
class MongoDBBackend(BaseMemoryBackend)
```

MongoDB backend for flexible document-based memory storage.
Ideal for deployments requiring schema flexibility and horizontal scaling.

Config options:
    - uri: MongoDB connection URI (default: "mongodb://localhost:27017")
    - database: Database name (default: "langswarm_memory")
    - collection_prefix: Prefix for collections (default: "")

**Methods:**

#### cleanup_expired_sessions

```python
async def cleanup_expired_sessions(self) -> int
```

Clean up expired sessions

**Parameters:**


**Returns:**

`int`

#### connect

```python
async def connect(self) -> bool
```

Connect to MongoDB and ensure indexes exist

**Parameters:**


**Returns:**

`bool`

#### create_session

```python
async def create_session(self, metadata: langswarm_memory.interfaces.SessionMetadata) -> langswarm_memory.interfaces.IMemorySession
```

Create a new MongoDB session

**Parameters:**

- `metadata`: `SessionMetadata`

**Returns:**

`IMemorySession`

#### delete_session

```python
async def delete_session(self, session_id: str) -> bool
```

Delete session from MongoDB

**Parameters:**

- `session_id`: `str`

**Returns:**

`bool`

#### disconnect

```python
async def disconnect(self) -> bool
```

Disconnect from MongoDB

**Parameters:**


**Returns:**

`bool`

#### get_collection_name

```python
def get_collection_name(self, name: str) -> str
```

Get collection name (for internal use)

**Parameters:**

- `name`: `str`

**Returns:**

`str`

#### get_db

```python
def get_db(self)
```

Get database instance (for internal use)

**Parameters:**


#### get_session

```python
async def get_session(self, session_id: str) -> Optional[langswarm_memory.interfaces.IMemorySession]
```

Get session from MongoDB

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

Check MongoDB connection health

**Parameters:**


**Returns:**

`Dict`

#### list_sessions

```python
async def list_sessions(self, user_id: Optional[str] = None, status: Optional[langswarm_memory.interfaces.SessionStatus] = None, limit: int = 100, offset: int = 0) -> List[langswarm_memory.interfaces.SessionMetadata]
```

List sessions from MongoDB

**Parameters:**

- `user_id`: `Optional = None`
- `status`: `Optional = None`
- `limit`: `int = 100`
- `offset`: `int = 0`

**Returns:**

`List`


### MongoDBSession

```python
class MongoDBSession(BaseMemorySession)
```

MongoDB session implementation

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


### PostgresBackend

```python
class PostgresBackend(BaseMemoryBackend)
```

PostgreSQL backend using asyncpg.
Supports both relational storage and vector embeddings (via pgvector).

**Methods:**

#### cleanup_expired_sessions

```python
async def cleanup_expired_sessions(self) -> int
```

Clean up expired sessions

**Parameters:**


**Returns:**

`int`

#### connect

```python
async def connect(self) -> bool
```

Connect to PostgreSQL

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

Disconnect from PostgreSQL

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
async def list_sessions(self, user_id=None, status=None, limit=100, offset=0) -> List[langswarm_memory.interfaces.SessionMetadata]
```

List sessions with filtering

**Parameters:**

- `user_id`: `Any = None`
- `status`: `Any = None`
- `limit`: `Any = 100`
- `offset`: `Any = 0`

**Returns:**

`List`

#### search_messages

```python
async def search_messages(self, query: str, session_id: Optional[str] = None, limit: int = 10) -> List[langswarm_memory.interfaces.Message]
```

Vector semantic search using pgvector

**Parameters:**

- `query`: `str`
- `session_id`: `Optional = None`
- `limit`: `int = 10`

**Returns:**

`List`


### PostgresSession

```python
class PostgresSession(BaseMemorySession)
```

Base implementation of memory session with common functionality.

Provides core session management, message handling, and conversation
summarization that can be extended by specific backend implementations.

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


### RedisBackend

```python
class RedisBackend(BaseMemoryBackend)
```

Redis backend for fast, distributed memory storage.
Ideal for production deployments with multiple instances.

**Methods:**

#### cleanup_expired_sessions

```python
async def cleanup_expired_sessions(self) -> int
```

Clean up expired sessions

**Parameters:**


**Returns:**

`int`

#### connect

```python
async def connect(self) -> bool
```

Connect to Redis

**Parameters:**


**Returns:**

`bool`

#### create_session

```python
async def create_session(self, metadata: langswarm_memory.interfaces.SessionMetadata) -> langswarm_memory.interfaces.IMemorySession
```

Create a new Redis session

**Parameters:**

- `metadata`: `SessionMetadata`

**Returns:**

`IMemorySession`

#### delete_session

```python
async def delete_session(self, session_id: str) -> bool
```

Delete session from Redis

**Parameters:**

- `session_id`: `str`

**Returns:**

`bool`

#### disconnect

```python
async def disconnect(self) -> bool
```

Disconnect from Redis

**Parameters:**


**Returns:**

`bool`

#### get_key_prefix

```python
def get_key_prefix(self) -> str
```

Get Redis key prefix (for internal use)

**Parameters:**


**Returns:**

`str`

#### get_redis

```python
def get_redis(self) -> redis.asyncio.client.Redis
```

Get Redis connection (for internal use)

**Parameters:**


**Returns:**

`Redis`

#### get_session

```python
async def get_session(self, session_id: str) -> Optional[langswarm_memory.interfaces.IMemorySession]
```

Get session from Redis

**Parameters:**

- `session_id`: `str`

**Returns:**

`Optional`

#### get_ttl

```python
def get_ttl(self) -> int
```

Get Redis TTL (for internal use)

**Parameters:**


**Returns:**

`int`

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


### RedisSession

```python
class RedisSession(BaseMemorySession)
```

Redis session implementation

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


### SQLiteBackend

```python
class SQLiteBackend(BaseMemoryBackend)
```

SQLite backend for persistent local storage.
Ideal for development and single-instance deployments.

**Methods:**

#### cleanup_expired_sessions

```python
async def cleanup_expired_sessions(self) -> int
```

Clean up expired sessions

**Parameters:**


**Returns:**

`int`

#### connect

```python
async def connect(self) -> bool
```

Connect to SQLite database

**Parameters:**


**Returns:**

`bool`

#### create_session

```python
async def create_session(self, metadata: langswarm_memory.interfaces.SessionMetadata) -> langswarm_memory.interfaces.IMemorySession
```

Create a new SQLite session

**Parameters:**

- `metadata`: `SessionMetadata`

**Returns:**

`IMemorySession`

#### delete_session

```python
async def delete_session(self, session_id: str) -> bool
```

Delete session from SQLite

**Parameters:**

- `session_id`: `str`

**Returns:**

`bool`

#### disconnect

```python
async def disconnect(self) -> bool
```

Disconnect from SQLite database

**Parameters:**


**Returns:**

`bool`

#### get_connection

```python
def get_connection(self) -> sqlite3.Connection
```

Get database connection (for internal use)

**Parameters:**


**Returns:**

`Connection`

#### get_session

```python
async def get_session(self, session_id: str) -> Optional[langswarm_memory.interfaces.IMemorySession]
```

Get session from SQLite

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

List sessions from SQLite

**Parameters:**

- `user_id`: `Optional = None`
- `status`: `Optional = None`
- `limit`: `int = 100`
- `offset`: `int = 0`

**Returns:**

`List`


### SQLiteSession

```python
class SQLiteSession(BaseMemorySession)
```

SQLite session implementation

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

