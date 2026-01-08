# Storage Backends

LangSwarm separates memory into two distinct types of storage:
1.  **Session Storage**: Stores chat metadata, conversation history, and summaries.
2.  **Vector Storage**: Stores embeddings for semantic search (RAG).

You can mix and match these backends depending on your needs.

## Session Storage

Session storage handles the "hot" memory of your agents. It must be fast and reliable.

### 🚀 Available Backends

| Backend | Type | Best For | Features |
|:---|:---|:---|:---|
| **SQLite** | `sqlite` | Development, Single-instance | Zero-setup, single file persistence. |
| **Redis** | `redis` | Production, Distributed | High performance, auto-expiration (TTL), shared state. |
| **PostgreSQL** | `postgres` | Enterprise Production | ACID compliance, rigid schema, reliable long-term history. |
| **BigQuery** | `bigquery` | Analytics, Archival | Storing massive history for observation/analytics (not low latency). |
| **MongoDB** | `mongodb` | Flexible Schema | Distributed document storage, horizontal scaling. |
| **Elasticsearch** | `elasticsearch` | Search/Analytics | Full-text search capabilities over history. |
| **In-Memory** | `in_memory` | Testing | Fast testing, non-persistent. |

### Configuration

Session storage is configured via `create_memory_manager`:

```python
# PostgreSQL Example
manager = create_memory_manager({
    "backend": "postgres",
    "settings": {
        "host": "localhost",
        "port": 5432,
        "database": "langswarm",
        "user": "admin",
        "password": "password"
    }
})

# Redis Example
manager = create_memory_manager({
    "backend": "redis",
    "settings": {
        "url": "redis://localhost:6379",
        "key_prefix": "ls:v1:"
    }
})
```

## Vector Storage

Vector storage enables **Reflexive Memory** and **Semantic Search**. It allows agents to recall relevant information from the past based on meaning, not just recent history.

### 🧠 Available Vector Stores

| Store | Type | Best For |
|:---|:---|:---|
| **Pinecone** | `pinecone` | Managed production vector database. |
| **Qdrant** | `qdrant` | High-performance open-source vector search. |
| **PGVector** | `pgvector` | Native PostgreSQL high-performance vector extension. |
| **Redis** | `redis` | In-memory high-speed vector search (RediSearch). |
| **Chroma** | `chroma` | Simple, AI-native local/server embedding store. |
| **SQLite** | `sqlite` | Local development and testing (via numpy). |

### configuration

To enable RAG, use the `vector` backend type. Note that currently, using the `vector` backend uses **in-memory** session tracking combined with persistent vector storage.

```python
# Pinecone Example
manager = create_memory_manager({
    "backend": "vector",
    "settings": {
        "enable_semantic_search": True,
        "embedding": {
            "provider": "openai",
            "api_key": "sk-..." 
        },
        "vector_store": {
            "store_type": "pinecone",
            "connection_params": {
                "api_key": "pinecone-key",
                "environment": "us-west1",
                "index_name": "agent-memory"
            }
        }
    }
})
```
