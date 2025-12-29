---
sidebar_position: 4
title: PostgreSQL & PGVector
---

# PostgreSQL Memory Backend

The PostgreSQL backend provides robust, production-grade memory storage for LangSwarm. It supports both standard relational storage for session history and native vector search using the `pgvector` extension.

## Features

- **Robust Persistence**: Store conversations securely in PostgreSQL.
- **Vector Search**: Native semantic search using `pgvector`.
- **AsyncIO**: Fully asynchronous using `asyncpg`.
- **Scalable**: Suitable for high-concurrency production deployments.

## Installation

To use the PostgreSQL backend, install `langswarm` with the `postgres` extra:

```bash
pip install "langswarm[postgres]"
# or manually
pip install asyncpg pgvector
```

### Database Setup

Ensure your PostgreSQL database has the `vector` extension installed if you plan to use semantic search:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

> The backend will attempt to create this extension automatically if the database user has sufficient privileges.

## Configuration

### Code-First Configuration

You can configure the backend programmatically using `create_memory_manager`:

```python
from langswarm.core.memory import create_memory_manager

manager = create_memory_manager(
    backend="postgres",
    # Connection details
    url="postgresql://user:pass@localhost:5432/dbname",
    # Or individual params:
    # user="user", password="pass", host="localhost", port=5432, database="dbname"
    
    # Vector Search Configuration
    enable_vector=True,
    embedding_dimension=1536,  # Matches OpenAI text-embedding-3-small
    embedding={
        "provider": "openai",
        "model": "text-embedding-3-small",
        "api_key": "sk-..." 
    }
)

# Attach to agent
agent = create_agent(..., memory_manager=manager)
```

### YAML Configuration

If using `langswarm.yaml`:

```yaml
agents:
  - id: "my-agent"
    memory:
      enabled: true
      backend: "postgres"
      config:
        url: "postgresql://user:pass@postgresql.railway.internal:5432/railway"
        enable_vector: true
        embedding:
          provider: "openai"
          model: "text-embedding-3-small"
```

## Vector Search

When `enable_vector` is set to `True`, LangSwarm will automatically:

1.  Generate embeddings for every new message using the configured provider.
2.  Store the embedding in the `embedding` vector column.
3.  Enable semantic search capabilities via `memory.search_messages()`.

### Performing Semantic Search

```python
# Search for relevant context
results = await agent.memory.search_messages("What did we discuss about deployment?")

for msg in results:
    print(f"[{msg.timestamp}] {msg.content}")
``` 

## Tables Created

The backend automatically creates the following tables (transparently managed):

- `sessions`: Stores session metadata.
- `messages`: Stores chat messages and embeddings.
- `summaries`: Stores conversation summaries.

By default, tables are created in the `public` schema. You can override this with the `schema` parameter.
