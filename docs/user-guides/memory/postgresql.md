---
sidebar_position: 4
title: PostgreSQL & PGVector
---

# PostgreSQL Memory Backend

For production workloads requiring robust data integrity and scalability, LangSwarm supports PostgreSQL. This backend handles:

1.  **Session Persistence**: Storing standard chat history.
2.  **Vector Search**:  Native RAG capabilities using the `pgvector` extension.

## 📦 Installation

```bash
pip install "langswarm[postgres]"
# Required: asyncpg, pgvector
```

## 🚀 Configuration

Use `create_memory_manager` to initialize the connection.

### Standard Persistence

Stores conversation history reliably in PostgreSQL.

```python
from langswarm.core.memory import create_memory_manager
from langswarm.core.agents import AgentBuilder

# 1. Initialize Manager
memory_manager = create_memory_manager({
    "backend": "postgres",
    "config": {
        "url": "postgresql://user:pass@localhost:5432/dbname",
        "table_prefix": "ls_"  # Optional: Prefix for tables (default: ls_)
    }
})

# 2. Attach to Agent
agent = await (AgentBuilder("db_agent")
    .memory_manager(memory_manager)
    .build())
```

### Vector Search (RAG)

Enable semantic search over long-term memory. Requires `pgvector` extension.

```sql
-- Run this in your database first
CREATE EXTENSION IF NOT EXISTS vector;
```

```python
memory_manager = create_memory_manager({
    "backend": "postgres",
    "config": {
        "url": "postgresql://user:pass@localhost:5432/dbname",
        
        # Enable RAG capabilities
        "enable_vector": True,
        "embedding_dimension": 1536, # Matches text-embedding-3-small
        "embedding": {
            "provider": "openai",
            "model": "text-embedding-3-small",
            "api_key": "sk-..." 
        }
    }
})
```

## 🔍 Semantic Search Usage

Once configured with vector support, you can search past conversations.

```python
# Search past session history
relevant_memories = await memory_manager.search_history(
    session_id="session_123", 
    query="What was the deployment configuration?",
    limit=5
)

for mem in relevant_memories:
    print(f"[{mem.score:.2f}] {mem.content}")
```

## 📊 Schema

LangSwarm automatically manages the following tables (transparently):

| Table | Description |
| :--- | :--- |
| `ls_sessions` | Metadata for each conversation thread |
| `ls_messages` | Full message logs (User, Assistant, Tool Calls) |
| `ls_embeddings` | Vector embeddings (if `enable_vector=True`) |
