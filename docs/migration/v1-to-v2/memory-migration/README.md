# LangSwarm V1 to V2 Memory Migration Guide

**Complete guide for migrating from V1's complex memory adapters to V2's unified memory system**

## 🎯 Overview

LangSwarm V2 dramatically simplifies memory management by replacing 15+ complex V1 memory adapters with a unified system that provides 75% complexity reduction while adding powerful new features. This guide helps you migrate your memory usage from V1 to V2.

**Migration Benefits:**
- **75% Complexity Reduction**: From 15+ adapters to 3 unified backends
- **Simplified Configuration**: `memory="development"` vs complex configuration objects
- **LLM Provider Alignment**: Native OpenAI and Anthropic format support
- **Enhanced Performance**: Sub-millisecond operations with intelligent caching
- **Better Developer Experience**: Context managers and clean APIs

---

## 🔄 Migration Strategy

### **Phase 1: Assessment and Planning**
Understand your current V1 memory usage and plan the migration approach.

```bash
# Find all memory adapter usage in your codebase
grep -r "memory.adapters" your_project/
grep -r "MemoryAdapter" your_project/
grep -r "chromadb_adapter\|sqlite_adapter\|redis_adapter" your_project/
```

### **Phase 2: V2 Backend Selection**
Choose the appropriate V2 backend based on your V1 adapter usage.

| V1 Adapter | V2 Backend | Migration Path |
|------------|------------|---------------|
| `SQLiteAdapter` | `SQLiteBackend` | Direct migration with schema conversion |
| `RedisAdapter` | `RedisBackend` | Configuration simplification |
| `ChromaDBAdapter` | `SQLiteBackend` + MemoryPro | Functionality preserved in provider |
| `InMemoryAdapter` | `InMemoryBackend` | Direct replacement |
| Custom adapters | Custom backend | Implement `IMemoryBackend` interface |

### **Phase 3: Gradual Migration**
Migrate incrementally while maintaining functionality.

```python
# Phase 3a: Side-by-side operation
v1_adapter = SQLiteAdapter(v1_config)
v2_memory = initialize_memory("production")

# Phase 3b: Data migration 
migrator = V1MemoryMigrator()
await migrator.migrate_sessions(v1_adapter, v2_memory.backend)

# Phase 3c: Replace V1 calls with V2
# Replace adapter calls with V2 memory operations
```

---

## 📊 V1 vs V2 Comparison

### **Configuration Complexity**

#### **V1 Configuration (Complex)**
```python
# V1 Complex configuration
from langswarm.memory.adapters.sqlite_adapter import SQLiteAdapter
from langswarm.memory.adapters.chromadb_adapter import ChromaDBAdapter

memory_config = {
    "memory": {
        "adapter": "sqlite",
        "backend": "sqlite",
        "settings": {
            "db_path": "/path/to/memory.db",
            "table_name": "conversations",
            "enable_wal": True,
            "journal_mode": "WAL",
            "synchronous": "NORMAL",
            "cache_size": -64000,
            "temp_store": "memory",
            "mmap_size": 268435456,
            "auto_vacuum": "incremental",
            "foreign_keys": True,
            "enable_load_extension": False,
            "connection_timeout": 30,
            "busy_timeout": 5000,
            "max_connections": 10,
            "enable_sharing": False,
            "thread_check": True,
            "isolation_level": None
        },
        "session_config": {
            "max_messages": 1000,
            "max_tokens": 32000,
            "enable_summarization": True,
            "summarization_threshold": 100,
            "summarization_strategy": "rolling",
            "compression_algorithm": "zlib",
            "encryption": {
                "enabled": False,
                "algorithm": "AES-256",
                "key_derivation": "PBKDF2"
            }
        }
    }
}

adapter = SQLiteAdapter(memory_config["memory"]["settings"])
```

#### **V2 Configuration (Simple)**
```python
# V2 Simple configuration
from langswarm.core.memory import initialize_memory

# One line for production
initialize_memory("production")

# Or custom configuration
initialize_memory(memory={
    "backend": "sqlite",
    "config": {
        "db_path": "/path/to/memory.db",
        "enable_wal": True
    }
})
```

### **Usage Pattern Comparison**

#### **V1 Usage (Complex)**
```python
# V1 Complex usage pattern
from langswarm.memory.session_manager import SessionManager
from langswarm.memory.message_formatter import MessageFormatter

# Setup
adapter = SQLiteAdapter(config)
session_manager = SessionManager(adapter)
formatter = MessageFormatter()

# Create session
session_config = {
    "user_id": "user123",
    "max_messages": 500,
    "auto_summarize": True
}
session = session_manager.create_session(session_config)

# Add message
message_data = {
    "role": "user",
    "content": "Hello",
    "timestamp": datetime.now(),
    "metadata": {"source": "web"}
}
formatted_message = formatter.format_message(message_data)
session.add_message(formatted_message)

# Get conversation
messages = session.get_messages(limit=20)
conversation_context = formatter.format_for_openai(messages)
```

#### **V2 Usage (Simple)**
```python
# V2 Simple usage pattern
from langswarm.core.memory import MemorySessionContext, create_openai_message

# Direct usage with context manager
async with MemorySessionContext(user_id="user123") as session:
    # Add message
    await session.add_message(create_openai_message("user", "Hello"))
    
    # Get conversation context ready for LLM
    context = await session.get_conversation_context(max_tokens=4000)
```

---

## 🛠️ Step-by-Step Migration

### **Step 1: Migrate SQLite Adapter**

#### **V1 SQLiteAdapter Usage**
```python
# V1 SQLite setup
from langswarm.memory.adapters.sqlite_adapter import SQLiteAdapter

config = {
    "db_path": "/data/conversations.db",
    "table_name": "messages",
    "enable_wal": True,
    "max_connections": 5
}

adapter = SQLiteAdapter(config)
await adapter.connect()

# Add conversation
session_id = "session_123"
message = {
    "role": "user",
    "content": "Hello",
    "timestamp": datetime.now()
}
await adapter.add_message(session_id, message)

# Get conversation
messages = await adapter.get_messages(session_id, limit=10)
```

#### **V2 SQLite Migration**
```python
# V2 SQLite setup
from langswarm.core.memory import initialize_memory, MemorySessionContext

# Initialize with SQLite backend
initialize_memory(memory={
    "backend": "sqlite",
    "config": {
        "db_path": "/data/conversations.db",
        "enable_wal": True
    }
})

# Use with context manager
async with MemorySessionContext(session_id="session_123") as session:
    # Add message (automatically handles formatting)
    await session.add_message(create_openai_message("user", "Hello"))
    
    # Get messages (automatically optimized)
    messages = await session.get_messages(limit=10)
```

### **Step 2: Migrate Redis Adapter**

#### **V1 RedisAdapter Usage**
```python
# V1 Redis setup
from langswarm.memory.adapters.redis_adapter import RedisAdapter

config = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": None,
    "connection_pool_size": 10,
    "key_prefix": "langswarm:memory:",
    "ttl": 86400
}

adapter = RedisAdapter(config)
await adapter.connect()

# Session management
session_data = {
    "user_id": "user123",
    "created_at": datetime.now(),
    "metadata": {"app": "chatbot"}
}
await adapter.create_session("session_123", session_data)

# Message operations
await adapter.add_message("session_123", message_data)
messages = await adapter.get_session_messages("session_123")
```

#### **V2 Redis Migration**
```python
# V2 Redis setup
from langswarm.core.memory import initialize_memory

# Initialize with Redis backend
initialize_memory(memory={
    "backend": "redis",
    "config": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "pool_size": 10,
        "ttl_seconds": 86400
    }
})

# Automatic session and message management
async with MemorySessionContext(
    user_id="user123",
    session_id="session_123",
    metadata={"app": "chatbot"}
) as session:
    await session.add_message(create_openai_message("user", "Hello"))
    messages = await session.get_messages()
    # TTL handled automatically
```

### **Step 3: Migrate ChromaDB Adapter**

#### **V1 ChromaDB Usage**
```python
# V1 ChromaDB setup
from langswarm.memory.adapters.chromadb_adapter import ChromaDBAdapter

config = {
    "persist_directory": "/data/chromadb",
    "collection_name": "conversations",
    "embedding_model": "all-MiniLM-L6-v2",
    "distance_metric": "cosine",
    "enable_semantic_search": True
}

adapter = ChromaDBAdapter(config)
await adapter.connect()

# Semantic operations
await adapter.add_message_with_embedding(session_id, message, embedding)
similar_messages = await adapter.search_similar_messages(query, limit=5)
```

#### **V2 Migration Strategy**
```python
# V2 approach: Use base memory + MemoryPro provider
from langswarm.core.memory import initialize_memory
from langswarm.providers.memorypro import MemoryProProvider

# Initialize base memory
initialize_memory("production")

# Add semantic search via MemoryPro provider
memory_pro = MemoryProProvider(
    vector_backend="chromadb",
    config={
        "persist_directory": "/data/chromadb",
        "embedding_model": "all-MiniLM-L6-v2"
    }
)

# Use both base memory and semantic search
async with MemorySessionContext(user_id="user123") as session:
    # Basic message storage
    await session.add_message(create_openai_message("user", "Query about AI"))
    
    # Semantic search via MemoryPro
    similar_messages = await memory_pro.search_similar(
        session_id=session.session_id,
        query="artificial intelligence",
        limit=5
    )
```

---

## 🔄 Data Migration

### **Automated Migration Tool**

```python
from langswarm.core.memory.migration import V1MemoryMigrator

class V1MemoryMigrator:
    """Migrate V1 memory data to V2 format"""
    
    async def migrate_sqlite_adapter(
        self,
        v1_db_path: str,
        v2_backend: IMemoryBackend,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """Migrate SQLite adapter data to V2"""
        
        # Connect to V1 database
        v1_conn = sqlite3.connect(v1_db_path)
        
        # Get all sessions from V1
        v1_sessions = v1_conn.execute(
            "SELECT DISTINCT session_id, user_id, created_at FROM messages"
        ).fetchall()
        
        migration_stats = {
            "sessions_migrated": 0,
            "messages_migrated": 0,
            "errors": []
        }
        
        for session_id, user_id, created_at in v1_sessions:
            try:
                # Create V2 session
                v2_session = await v2_backend.create_session(SessionMetadata(
                    session_id=session_id,
                    user_id=user_id,
                    created_at=datetime.fromisoformat(created_at)
                ))
                
                # Migrate messages in batches
                offset = 0
                while True:
                    v1_messages = v1_conn.execute(
                        """SELECT role, content, timestamp, metadata 
                           FROM messages 
                           WHERE session_id = ? 
                           ORDER BY timestamp 
                           LIMIT ? OFFSET ?""",
                        (session_id, batch_size, offset)
                    ).fetchall()
                    
                    if not v1_messages:
                        break
                    
                    # Convert to V2 format
                    for role, content, timestamp, metadata_str in v1_messages:
                        v2_message = Message(
                            role=MessageRole(role),
                            content=content,
                            timestamp=datetime.fromisoformat(timestamp),
                            metadata=json.loads(metadata_str or "{}")
                        )
                        await v2_session.add_message(v2_message)
                        migration_stats["messages_migrated"] += 1
                    
                    offset += batch_size
                
                migration_stats["sessions_migrated"] += 1
                
            except Exception as e:
                migration_stats["errors"].append({
                    "session_id": session_id,
                    "error": str(e)
                })
        
        return migration_stats
    
    async def migrate_redis_adapter(
        self,
        v1_redis_config: Dict,
        v2_backend: IMemoryBackend
    ) -> Dict[str, Any]:
        """Migrate Redis adapter data to V2"""
        
        import redis.asyncio as aioredis
        
        # Connect to V1 Redis
        v1_redis = aioredis.from_url(
            f"redis://{v1_redis_config['host']}:{v1_redis_config['port']}"
        )
        
        # Get all V1 session keys
        key_pattern = f"{v1_redis_config.get('key_prefix', 'langswarm:memory:')}*"
        session_keys = await v1_redis.keys(key_pattern)
        
        migration_stats = {
            "sessions_migrated": 0,
            "messages_migrated": 0,
            "errors": []
        }
        
        for key in session_keys:
            try:
                # Extract session ID from key
                session_id = key.decode().split(":")[-1]
                
                # Get V1 session data
                v1_data = await v1_redis.hgetall(key)
                
                # Create V2 session
                v2_session = await v2_backend.create_session(SessionMetadata(
                    session_id=session_id,
                    user_id=v1_data.get(b"user_id", b"").decode(),
                    created_at=datetime.fromisoformat(
                        v1_data.get(b"created_at", datetime.now().isoformat()).decode()
                    )
                ))
                
                # Migrate messages
                messages_data = json.loads(v1_data.get(b"messages", b"[]").decode())
                for msg_data in messages_data:
                    v2_message = Message(
                        role=MessageRole(msg_data["role"]),
                        content=msg_data["content"],
                        timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        metadata=msg_data.get("metadata", {})
                    )
                    await v2_session.add_message(v2_message)
                    migration_stats["messages_migrated"] += 1
                
                migration_stats["sessions_migrated"] += 1
                
            except Exception as e:
                migration_stats["errors"].append({
                    "key": key.decode(),
                    "error": str(e)
                })
        
        return migration_stats

# Usage
migrator = V1MemoryMigrator()

# Migrate SQLite data
v2_memory = initialize_memory("production")
sqlite_result = await migrator.migrate_sqlite_adapter(
    v1_db_path="/old/memory.db",
    v2_backend=v2_memory.backend
)

print(f"SQLite Migration Results:")
print(f"  Sessions: {sqlite_result['sessions_migrated']}")
print(f"  Messages: {sqlite_result['messages_migrated']}")
print(f"  Errors: {len(sqlite_result['errors'])}")
```

### **Manual Migration Script**

```python
import asyncio
from langswarm.core.memory import initialize_memory, get_global_memory_manager

async def manual_migration():
    """Manual migration for custom V1 setups"""
    
    # Initialize V2 memory
    initialize_memory("production")
    v2_memory = get_global_memory_manager()
    
    # Example: Migrate from CSV export
    import pandas as pd
    
    # Load V1 data export
    v1_data = pd.read_csv("v1_memory_export.csv")
    
    # Group by session
    for session_id, session_data in v1_data.groupby("session_id"):
        
        # Create V2 session
        session = await v2_memory.create_session(
            session_id=session_id,
            user_id=session_data.iloc[0]["user_id"]
        )
        
        # Add messages
        for _, row in session_data.iterrows():
            message = create_openai_message(
                role=row["role"],
                content=row["content"]
            )
            message.timestamp = pd.to_datetime(row["timestamp"])
            await session.add_message(message)
        
        print(f"Migrated session {session_id}: {len(session_data)} messages")

# Run migration
asyncio.run(manual_migration())
```

---

## 🧪 Testing Migration

### **Validation Tests**

```python
import pytest

class TestMemoryMigration:
    """Test suite for memory migration validation"""
    
    async def test_message_preservation(self):
        """Test that all messages are preserved during migration"""
        
        # Setup V1 test data
        v1_messages = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2024-01-01T10:00:01"}
        ]
        
        # Create V1 test database
        v1_db = create_test_v1_database(v1_messages)
        
        # Migrate to V2
        v2_memory = initialize_memory("testing")
        migrator = V1MemoryMigrator()
        result = await migrator.migrate_sqlite_adapter(v1_db, v2_memory.backend)
        
        # Validate migration
        assert result["messages_migrated"] == len(v1_messages)
        
        # Check message content
        v2_session = await v2_memory.get_session("test_session")
        v2_messages = await v2_session.get_messages()
        
        assert len(v2_messages) == len(v1_messages)
        for v1_msg, v2_msg in zip(v1_messages, v2_messages):
            assert v1_msg["role"] == v2_msg.role.value
            assert v1_msg["content"] == v2_msg.content
    
    async def test_performance_improvement(self):
        """Test that V2 performance is better than V1"""
        
        # Create large test dataset
        test_data = create_large_test_dataset(sessions=100, messages_per_session=50)
        
        # Time V1 operations
        v1_start = time.time()
        v1_results = simulate_v1_operations(test_data)
        v1_duration = time.time() - v1_start
        
        # Time V2 operations
        v2_start = time.time()
        v2_results = await perform_v2_operations(test_data)
        v2_duration = time.time() - v2_start
        
        # V2 should be faster
        improvement = (v1_duration - v2_duration) / v1_duration
        assert improvement > 0, f"V2 should be faster than V1"
        
        print(f"Performance improvement: {improvement:.1%}")
    
    async def test_feature_equivalence(self):
        """Test that V2 provides equivalent functionality to V1"""
        
        # Test session management
        session = await v2_memory.create_session(user_id="test_user")
        assert session.session_id is not None
        
        # Test message operations
        await session.add_message(create_openai_message("user", "Test"))
        messages = await session.get_messages()
        assert len(messages) == 1
        
        # Test conversation context
        context = await session.get_conversation_context(max_tokens=1000)
        assert len(context) == 1
        
        # Test session listing
        sessions = await v2_memory.backend.list_sessions(user_id="test_user")
        assert len(sessions) >= 1
```

---

## 📋 Migration Checklist

### **Pre-Migration Assessment**
- [ ] Inventory all V1 memory adapter usage
- [ ] Document current memory configurations
- [ ] Identify custom adapter implementations
- [ ] Plan V2 backend selection strategy
- [ ] Estimate data migration time and resources

### **Migration Preparation**
- [ ] Set up V2 memory system in staging environment
- [ ] Create migration scripts for your specific adapters
- [ ] Implement data validation and testing procedures
- [ ] Plan rollback strategy in case of issues
- [ ] Schedule migration maintenance window

### **Migration Execution**
- [ ] Backup all V1 memory data
- [ ] Run migration scripts in staging
- [ ] Validate migrated data integrity
- [ ] Test application functionality with V2 memory
- [ ] Update application code to use V2 APIs

### **Post-Migration Validation**
- [ ] Verify all conversations migrated correctly
- [ ] Test performance improvements
- [ ] Monitor memory usage and performance
- [ ] Update documentation and training materials
- [ ] Clean up V1 memory systems

---

## 🎯 Migration Success Metrics

### **Data Integrity**
- [ ] **100% Message Preservation**: All messages migrated successfully
- [ ] **Session Continuity**: All conversation sessions maintained
- [ ] **Metadata Preservation**: Custom metadata and timestamps preserved
- [ ] **User Association**: User-session relationships maintained

### **Performance Improvements**
- [ ] **Faster Operations**: Sub-millisecond response times
- [ ] **Lower Memory Usage**: Reduced memory footprint
- [ ] **Better Caching**: Intelligent session caching working
- [ ] **Improved Throughput**: Higher concurrent session capacity

### **Functionality Enhancement**
- [ ] **LLM Integration**: Native OpenAI/Anthropic format support
- [ ] **Auto-Summarization**: Conversation summarization working
- [ ] **Session Management**: Enhanced session lifecycle management
- [ ] **Analytics**: Memory usage analytics available

### **Developer Experience**
- [ ] **Simplified APIs**: Context managers and clean interfaces
- [ ] **Better Error Handling**: Clear error messages and recovery
- [ ] **Type Safety**: Full type annotations working
- [ ] **Documentation**: Updated guides and examples

---

## 🚀 Post-Migration Optimization

### **Leverage V2 Features**

```python
# Take advantage of V2-specific improvements
async with MemorySessionContext(
    user_id="user123",
    max_tokens=8000,           # Optimized for your LLM
    auto_summarize_threshold=50 # Automatic conversation summarization
) as session:
    
    # Native LLM format support
    await session.add_message(create_openai_message("user", "Query"))
    openai_context = await session.get_conversation_context(max_tokens=4000)
    
    # Use context directly with OpenAI API
    response = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages_to_openai_format(openai_context)
    )
```

### **Performance Tuning**

```python
# Optimize for your specific use case
initialize_memory(memory={
    "backend": "redis",
    "config": {
        "pool_size": 20,        # Tune for concurrent users
        "ttl_seconds": 7200,    # 2 hour session expiration
    }
})

# Monitor and adjust based on usage patterns
memory = get_global_memory_manager()
stats = await memory.get_system_stats()

if stats["avg_messages_per_session"] > 100:
    # Enable more aggressive summarization
    # Update session configs
    pass
```

---

**The V2 memory migration transforms complex, fragmented memory management into a simple, unified system while preserving all data and adding powerful new capabilities for better LLM integration and performance.**
