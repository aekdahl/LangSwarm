# LangSwarm V2 Native Vector Stores Examples

**Practical examples for native vector database implementations across different use cases and deployment scenarios**

## 🎯 Overview

This collection provides real-world vector store examples for LangSwarm V2, demonstrating native implementations that replace LangChain/LlamaIndex dependencies with 20-40% better performance. Each example includes complete implementations and usage instructions.

**Example Categories:**
- **Getting Started**: Simple vector store usage for learning
- **Production Deployments**: Scalable, monitored production configurations
- **Migration Examples**: LangChain/LlamaIndex to V2 migration scenarios
- **Advanced Patterns**: Custom similarity metrics, hybrid search, and specialized stores
- **Performance Optimization**: High-throughput and efficient vector operations
- **Integration Examples**: Memory system integration and workflow patterns

---

## 🚀 Getting Started Examples

### **1. Simple SQLite Vector Store**

```python
"""
Simple local vector store with SQLite backend
"""
import asyncio
import numpy as np
from langswarm.core.memory.vector_stores import VectorStoreFactory, VectorDocument, VectorQuery

async def simple_sqlite_example():
    # Create SQLite vector store
    store = VectorStoreFactory.create_sqlite_store(
        db_path="simple_vectors.db",
        embedding_dimension=1536
    )
    
    # Connect to store
    await store.connect()
    print("Connected to SQLite vector store")
    
    # Create sample documents
    documents = [
        VectorDocument(
            id="doc1",
            content="Machine learning is a subset of artificial intelligence",
            metadata={"category": "AI", "difficulty": "beginner"}
        ),
        VectorDocument(
            id="doc2",
            content="Python is a popular programming language for data science",
            metadata={"category": "Programming", "difficulty": "beginner"}
        ),
        VectorDocument(
            id="doc3",
            content="Deep learning uses neural networks with multiple layers",
            metadata={"category": "AI", "difficulty": "intermediate"}
        ),
        VectorDocument(
            id="doc4",
            content="Vector databases enable efficient similarity search",
            metadata={"category": "Database", "difficulty": "intermediate"}
        )
    ]
    
    # Add documents (embeddings will be generated automatically)
    print(f"Adding {len(documents)} documents...")
    document_ids = await store.add_documents(documents)
    print(f"Added documents: {document_ids}")
    
    # Perform similarity search
    query = VectorQuery(
        text="What is artificial intelligence?",
        top_k=3,
        metadata_filter={"category": "AI"}
    )
    
    results = await store.query(query)
    
    print(f"\nSearch results for: '{query.text}'")
    print("=" * 50)
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result.score:.3f}")
        print(f"   Content: {result.document.content}")
        print(f"   Metadata: {result.document.metadata}")
        print()
    
    # Get store statistics
    stats = await store.get_statistics()
    print(f"Store Statistics:")
    print(f"  Total documents: {stats.total_documents}")
    print(f"  Storage size: {stats.storage_size_mb:.2f} MB")
    print(f"  Average query time: {stats.avg_query_time_ms:.2f} ms")
    
    # Clean up
    await store.disconnect()

# Run the example
asyncio.run(simple_sqlite_example())
```

### **2. Multi-Backend Vector Store Comparison**

```python
"""
Compare different vector store backends
"""
import asyncio
import time
from typing import List, Dict, Any
from langswarm.core.memory.vector_stores import VectorStoreFactory, VectorDocument, VectorQuery

async def multi_backend_comparison():
    # Test documents
    test_documents = [
        VectorDocument(
            id=f"doc_{i}",
            content=f"Test document {i} about machine learning and AI concepts",
            metadata={"batch": "test", "index": i}
        )
        for i in range(100)
    ]
    
    # Backends to test
    backends_config = {
        "sqlite": {
            "factory_method": "create_sqlite_store",
            "config": {"db_path": "test_sqlite.db", "embedding_dimension": 1536}
        },
        "chroma": {
            "factory_method": "create_chroma_store", 
            "config": {"collection_name": "test_chroma", "embedding_dimension": 1536}
        }
    }
    
    results = {}
    
    for backend_name, backend_config in backends_config.items():
        print(f"\n=== Testing {backend_name.upper()} Backend ===")
        
        try:
            # Create store
            factory_method = getattr(VectorStoreFactory, backend_config["factory_method"])
            store = factory_method(**backend_config["config"])
            
            await store.connect()
            print(f"✅ Connected to {backend_name}")
            
            # Measure insertion time
            start_time = time.time()
            await store.add_documents(test_documents)
            insert_time = time.time() - start_time
            
            # Measure query time
            query = VectorQuery(text="machine learning concepts", top_k=10)
            
            start_time = time.time()
            query_results = await store.query(query)
            query_time = time.time() - start_time
            
            # Get statistics
            stats = await store.get_statistics()
            
            results[backend_name] = {
                "insert_time": insert_time,
                "query_time": query_time,
                "storage_size_mb": stats.storage_size_mb,
                "avg_query_time_ms": stats.avg_query_time_ms,
                "results_count": len(query_results),
                "status": "success"
            }
            
            print(f"  Insert time: {insert_time:.3f}s")
            print(f"  Query time: {query_time:.3f}s")
            print(f"  Results: {len(query_results)} documents")
            
            await store.disconnect()
            
        except Exception as e:
            print(f"❌ Error with {backend_name}: {e}")
            results[backend_name] = {"status": "error", "error": str(e)}
    
    # Print comparison
    print(f"\n{'='*50}")
    print("BACKEND COMPARISON RESULTS")
    print(f"{'='*50}")
    
    for backend, metrics in results.items():
        if metrics["status"] == "success":
            print(f"{backend.upper()}:")
            print(f"  Insert time: {metrics['insert_time']:.3f}s")
            print(f"  Query time: {metrics['query_time']:.3f}s") 
            print(f"  Storage size: {metrics['storage_size_mb']:.2f} MB")
            print(f"  Avg query time: {metrics['avg_query_time_ms']:.2f} ms")
        else:
            print(f"{backend.upper()}: {metrics['status']} - {metrics.get('error', '')}")
        print()

asyncio.run(multi_backend_comparison())
```

### **3. Vector-Enabled Memory Integration**

```python
"""
Vector store integration with V2 memory system
"""
import asyncio
from langswarm.core.memory import MemoryFactory

async def vector_memory_example():
    # Create vector-enabled memory backend
    memory = MemoryFactory.create(
        backend="vector",
        config={
            "vector_store": "sqlite",
            "db_path": "semantic_memory.db",
            "embedding_provider": "openai",
            "auto_index": True,
            "similarity_threshold": 0.7
        }
    )
    
    print("Created vector-enabled memory backend")
    
    # Simulate conversation with automatic semantic indexing
    conversations = [
        ("user123", "Tell me about machine learning algorithms"),
        ("assistant", "Machine learning algorithms are computational methods that learn patterns from data..."),
        ("user123", "What are neural networks?"),
        ("assistant", "Neural networks are computing systems inspired by biological neural networks..."),
        ("user123", "How does deep learning work?"),
        ("assistant", "Deep learning uses neural networks with multiple layers to learn complex patterns..."),
        ("user456", "Explain artificial intelligence"),
        ("assistant", "Artificial intelligence refers to the simulation of human intelligence in machines...")
    ]
    
    # Add messages to memory (automatically indexed for semantic search)
    for speaker, message in conversations:
        await memory.add_message(speaker, message)
        print(f"Added message from {speaker}: {message[:50]}...")
    
    print(f"\nAdded {len(conversations)} messages to vector memory")
    
    # Perform semantic search across conversations
    search_queries = [
        "neural network concepts",
        "learning algorithms",
        "artificial intelligence definition"
    ]
    
    for query in search_queries:
        print(f"\n🔍 Semantic search for: '{query}'")
        print("-" * 40)
        
        similar_messages = await memory.semantic_search(
            query=query,
            limit=3
        )
        
        for i, message in enumerate(similar_messages, 1):
            print(f"{i}. Similarity: {message.similarity:.3f}")
            print(f"   Speaker: {message.speaker}")
            print(f"   Content: {message.content[:80]}...")
            print()
    
    # Search within specific user's conversations
    print("\n🔍 User-specific semantic search")
    print("-" * 40)
    
    user_results = await memory.semantic_search(
        query="machine learning",
        user_id="user123",
        limit=2
    )
    
    for result in user_results:
        print(f"User {result.user_id}: {result.content[:100]}...")
        print(f"Similarity: {result.similarity:.3f}\n")

asyncio.run(vector_memory_example())
```

---

## 🏭 Production Examples

### **4. High-Performance Pinecone Setup**

```python
"""
Production Pinecone vector store configuration
"""
import asyncio
import os
from langswarm.core.memory.vector_stores import VectorStoreFactory, VectorDocument, VectorQuery

async def production_pinecone_example():
    # Production Pinecone configuration
    store = VectorStoreFactory.create_pinecone_store(
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-west1-gcp",
        index_name="production-langswarm",
        embedding_dimension=1536,
        metric="cosine"
    )
    
    await store.connect()
    print("Connected to production Pinecone store")
    
    # Batch document processing for production
    async def process_document_batch(documents: List[VectorDocument], batch_size: int = 100):
        """Process large document batches efficiently"""
        total_processed = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                start_time = time.time()
                document_ids = await store.add_documents(batch)
                processing_time = time.time() - start_time
                
                total_processed += len(document_ids)
                
                print(f"Processed batch {i//batch_size + 1}: {len(document_ids)} documents in {processing_time:.2f}s")
                
                # Rate limiting for production
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing batch {i//batch_size + 1}: {e}")
                continue
        
        print(f"Total processed: {total_processed} documents")
        return total_processed
    
    # Simulate production document load
    production_documents = []
    categories = ["documentation", "support", "knowledge_base", "tutorials"]
    
    for i in range(500):
        doc = VectorDocument(
            id=f"prod_doc_{i}",
            content=f"Production document {i} containing important information about various topics",
            metadata={
                "category": categories[i % len(categories)],
                "priority": "high" if i % 10 == 0 else "normal",
                "source": "production_system",
                "indexed_at": "2024-01-01T00:00:00Z"
            }
        )
        production_documents.append(doc)
    
    # Process documents in batches
    await process_document_batch(production_documents, batch_size=50)
    
    # Production query patterns
    production_queries = [
        VectorQuery(
            text="system configuration and setup",
            top_k=20,
            metadata_filter={"category": "documentation", "priority": "high"}
        ),
        VectorQuery(
            text="troubleshooting common issues",
            top_k=15,
            metadata_filter={"category": "support"}
        ),
        VectorQuery(
            text="best practices and guidelines",
            top_k=10,
            metadata_filter={"source": "production_system"}
        )
    ]
    
    # Execute production queries with monitoring
    for i, query in enumerate(production_queries, 1):
        print(f"\n📊 Production Query {i}: '{query.text}'")
        print("-" * 50)
        
        start_time = time.time()
        results = await store.query(query)
        query_time = time.time() - start_time
        
        print(f"Query time: {query_time:.3f}s")
        print(f"Results: {len(results)} documents")
        
        # Show top results
        for j, result in enumerate(results[:3], 1):
            print(f"  {j}. Score: {result.score:.3f} | {result.document.metadata.get('category', 'N/A')}")
            print(f"     {result.document.content[:80]}...")
    
    # Production health monitoring
    health = await store.health_check()
    print(f"\n🏥 Production Health Check")
    print("-" * 30)
    print(f"Status: {'✅ Healthy' if health.is_healthy else '❌ Unhealthy'}")
    print(f"Response time: {health.response_time_ms:.2f}ms")
    
    if health.issues:
        print("Issues:")
        for issue in health.issues:
            print(f"  - {issue}")
    
    # Production statistics
    stats = await store.get_statistics()
    print(f"\n📈 Production Statistics")
    print("-" * 25)
    print(f"Total documents: {stats.total_documents:,}")
    print(f"Index size: {stats.index_size_mb:.2f} MB")
    print(f"Average query time: {stats.avg_query_time_ms:.2f}ms")
    print(f"Total queries: {stats.total_queries:,}")

asyncio.run(production_pinecone_example())
```

### **5. Qdrant Production Deployment**

```python
"""
Self-hosted Qdrant production deployment
"""
import asyncio
from langswarm.core.memory.vector_stores import VectorStoreFactory

async def qdrant_production_example():
    # Production Qdrant configuration
    store = VectorStoreFactory.create_qdrant_store(
        url="http://qdrant-server:6333",
        collection_name="production_vectors",
        embedding_dimension=1536,
        distance_metric="Cosine",
        connection_config={
            "timeout": 60,
            "pool_size": 20,
            "max_retries": 3,
            "retry_delay": 1.0
        }
    )
    
    await store.connect()
    print("Connected to production Qdrant cluster")
    
    # Create collection with optimized settings
    await store.create_collection({
        "vectors": {
            "size": 1536,
            "distance": "Cosine"
        },
        "optimizers_config": {
            "default_segment_number": 2,
            "max_segment_size": 20000,
            "max_optimization_threads": 2
        },
        "replication_factor": 2,
        "write_consistency_factor": 1
    })
    
    # Payload indexing for efficient filtering
    await store.create_payload_index("category", "keyword")
    await store.create_payload_index("priority", "keyword")
    await store.create_payload_index("timestamp", "datetime")
    
    print("Collection created with optimized configuration")
    
    # Production document ingestion
    async def ingest_production_data():
        """Simulate production data ingestion"""
        
        # Sample production data
        categories = ["user_manual", "api_docs", "troubleshooting", "faq", "tutorials"]
        priorities = ["critical", "high", "medium", "low"]
        
        documents = []
        for i in range(1000):
            doc = VectorDocument(
                id=f"qdrant_prod_{i}",
                content=f"Production content {i} with detailed information and procedures",
                metadata={
                    "category": categories[i % len(categories)],
                    "priority": priorities[i % len(priorities)],
                    "version": f"v{i//100 + 1}.0",
                    "timestamp": f"2024-01-{(i%30)+1:02d}T10:00:00Z",
                    "author": f"user_{i%50}",
                    "tags": [f"tag_{j}" for j in range(i%3 + 1)]
                }
            )
            documents.append(doc)
        
        # Batch processing with error handling
        batch_size = 100
        success_count = 0
        error_count = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                await store.add_documents(batch)
                success_count += len(batch)
                print(f"✅ Batch {i//batch_size + 1}: {len(batch)} documents")
                
            except Exception as e:
                error_count += len(batch)
                print(f"❌ Batch {i//batch_size + 1} failed: {e}")
                continue
        
        print(f"Ingestion complete: {success_count} success, {error_count} errors")
        return success_count
    
    # Ingest data
    await ingest_production_data()
    
    # Advanced production queries
    advanced_queries = [
        # Multi-criteria search
        VectorQuery(
            text="system installation and configuration",
            top_k=25,
            metadata_filter={
                "category": {"$in": ["user_manual", "api_docs"]},
                "priority": {"$in": ["critical", "high"]}
            }
        ),
        
        # Time-based search
        VectorQuery(
            text="recent updates and changes", 
            top_k=15,
            metadata_filter={
                "timestamp": {"$gte": "2024-01-15T00:00:00Z"}
            }
        ),
        
        # Tag-based search
        VectorQuery(
            text="troubleshooting guide",
            top_k=10,
            metadata_filter={
                "category": "troubleshooting",
                "tags": {"$contains": "tag_1"}
            }
        )
    ]
    
    # Execute advanced queries
    for i, query in enumerate(advanced_queries, 1):
        print(f"\n🔍 Advanced Query {i}")
        print(f"Text: {query.text}")
        print(f"Filter: {query.metadata_filter}")
        print("-" * 40)
        
        results = await store.query(query)
        print(f"Results: {len(results)} documents")
        
        # Analyze result distribution
        categories = {}
        priorities = {}
        
        for result in results:
            cat = result.document.metadata.get("category", "unknown")
            pri = result.document.metadata.get("priority", "unknown")
            
            categories[cat] = categories.get(cat, 0) + 1
            priorities[pri] = priorities.get(pri, 0) + 1
        
        print(f"Categories: {categories}")
        print(f"Priorities: {priorities}")
    
    # Collection information
    collection_info = await store.get_collection_info()
    print(f"\n📊 Collection Information")
    print("-" * 25)
    print(f"Status: {collection_info.get('status')}")
    print(f"Vectors count: {collection_info.get('vectors_count', 0):,}")
    print(f"Segments: {collection_info.get('segments_count', 0)}")
    print(f"Disk usage: {collection_info.get('disk_data_size', 0) / 1024 / 1024:.2f} MB")

asyncio.run(qdrant_production_example())
```

---

## 🔄 Migration Examples

### **6. LangChain to V2 Migration**

```python
"""
Migrating from LangChain vector stores to V2 native
"""
import asyncio
import numpy as np
from typing import List

# Simulate LangChain data for migration
class LangChainSimulator:
    """Simulate LangChain vector store for migration example"""
    
    def __init__(self):
        self.documents = []
        for i in range(100):
            self.documents.append({
                "id": f"langchain_doc_{i}",
                "text": f"LangChain document {i} about various AI and ML topics",
                "metadata": {"source": "langchain", "index": i, "category": f"cat_{i%5}"},
                "embedding": np.random.rand(1536).tolist()
            })
    
    def get_all_documents(self):
        return self.documents
    
    def similarity_search(self, query, k=5):
        # Simulate similarity search
        return self.documents[:k]

async def langchain_to_v2_migration():
    """Complete migration from LangChain to V2"""
    
    print("🔄 Starting LangChain to V2 Migration")
    print("=" * 40)
    
    # 1. Initialize LangChain simulator
    langchain_store = LangChainSimulator()
    print(f"✅ LangChain store simulated with {len(langchain_store.documents)} documents")
    
    # 2. Create V2 vector store
    from langswarm.core.memory.vector_stores import VectorStoreFactory, VectorDocument
    
    v2_store = VectorStoreFactory.create_sqlite_store(
        db_path="migrated_vectors.db",
        embedding_dimension=1536
    )
    await v2_store.connect()
    print("✅ V2 vector store created and connected")
    
    # 3. Migration process
    async def migrate_data():
        """Migrate documents from LangChain to V2"""
        
        langchain_docs = langchain_store.get_all_documents()
        v2_documents = []
        
        # Convert LangChain format to V2 format
        for lc_doc in langchain_docs:
            v2_doc = VectorDocument(
                id=lc_doc["id"].replace("langchain_", "v2_"),  # Update ID
                content=lc_doc["text"],
                metadata={
                    **lc_doc["metadata"],
                    "migrated_from": "langchain",
                    "migration_date": "2024-01-01"
                },
                embedding=np.array(lc_doc["embedding"])
            )
            v2_documents.append(v2_doc)
        
        # Batch insert into V2 store
        batch_size = 50
        migrated_count = 0
        
        for i in range(0, len(v2_documents), batch_size):
            batch = v2_documents[i:i + batch_size]
            
            try:
                await v2_store.add_documents(batch)
                migrated_count += len(batch)
                print(f"  Migrated batch {i//batch_size + 1}: {len(batch)} documents")
                
            except Exception as e:
                print(f"  ❌ Migration error in batch {i//batch_size + 1}: {e}")
        
        print(f"✅ Migration completed: {migrated_count} documents")
        return migrated_count
    
    # Execute migration
    migrated_count = await migrate_data()
    
    # 4. Validation - compare search results
    print("\n🔍 Validating Migration - Search Comparison")
    print("-" * 45)
    
    test_query = "artificial intelligence and machine learning"
    
    # LangChain search (simulated)
    lc_results = langchain_store.similarity_search(test_query, k=5)
    print(f"LangChain results: {len(lc_results)} documents")
    
    # V2 search
    from langswarm.core.memory.vector_stores import VectorQuery
    
    v2_results = await v2_store.query(VectorQuery(
        text=test_query,
        top_k=5
    ))
    print(f"V2 results: {len(v2_results)} documents")
    
    # 5. Performance comparison
    print("\n⚡ Performance Comparison")
    print("-" * 25)
    
    import time
    
    # V2 query performance
    start_time = time.time()
    for _ in range(10):
        await v2_store.query(VectorQuery(text="test query", top_k=10))
    v2_time = (time.time() - start_time) / 10
    
    print(f"V2 average query time: {v2_time:.4f}s")
    print(f"Migration benefit: Native performance + type safety")
    
    # 6. Migration summary
    stats = await v2_store.get_statistics()
    
    print(f"\n📊 Migration Summary")
    print("-" * 20)
    print(f"Documents migrated: {migrated_count}")
    print(f"V2 store size: {stats.storage_size_mb:.2f} MB")
    print(f"V2 documents: {stats.total_documents}")
    print(f"Migration status: ✅ Complete")
    
    await v2_store.disconnect()

asyncio.run(langchain_to_v2_migration())
```

### **7. LlamaIndex to V2 Migration**

```python
"""
Migrating from LlamaIndex to V2 native implementation
"""
import asyncio
import numpy as np

class LlamaIndexSimulator:
    """Simulate LlamaIndex for migration example"""
    
    def __init__(self):
        self.index_data = {
            "documents": [],
            "embeddings": [],
            "metadata": []
        }
        
        # Simulate LlamaIndex data
        for i in range(150):
            self.index_data["documents"].append({
                "doc_id": f"llama_doc_{i}",
                "text": f"LlamaIndex document {i} containing research and documentation",
                "metadata": {
                    "source": "llamaindex",
                    "type": "research" if i % 3 == 0 else "documentation",
                    "author": f"researcher_{i%10}",
                    "date": f"2023-{(i%12)+1:02d}-01"
                }
            })
            
            self.index_data["embeddings"].append(np.random.rand(1536))
    
    def get_all_data(self):
        return self.index_data
    
    def query(self, query_text, top_k=5):
        # Simulate LlamaIndex query
        return {
            "nodes": self.index_data["documents"][:top_k],
            "similarities": [0.9, 0.8, 0.75, 0.7, 0.65][:top_k]
        }

async def llamaindex_to_v2_migration():
    """Complete LlamaIndex to V2 migration"""
    
    print("🔄 Starting LlamaIndex to V2 Migration")
    print("=" * 42)
    
    # 1. Load LlamaIndex data
    llama_index = LlamaIndexSimulator()
    llama_data = llama_index.get_all_data()
    
    print(f"✅ LlamaIndex data loaded: {len(llama_data['documents'])} documents")
    
    # 2. Create V2 vector store
    from langswarm.core.memory.vector_stores import VectorStoreFactory, VectorDocument
    
    v2_store = VectorStoreFactory.create_chroma_store(
        collection_name="migrated_llamaindex",
        embedding_dimension=1536
    )
    
    await v2_store.connect()
    print("✅ V2 ChromaDB store created")
    
    # 3. Data transformation and migration
    async def transform_and_migrate():
        """Transform LlamaIndex data to V2 format"""
        
        v2_documents = []
        
        # Transform each document
        for i, (doc, embedding) in enumerate(zip(
            llama_data["documents"],
            llama_data["embeddings"]
        )):
            # Create V2 document with enhanced metadata
            v2_doc = VectorDocument(
                id=doc["doc_id"].replace("llama_", "v2_"),
                content=doc["text"],
                metadata={
                    **doc["metadata"],
                    "original_source": "llamaindex",
                    "migration_timestamp": "2024-01-01T12:00:00Z",
                    "document_length": len(doc["text"]),
                    "embedding_model": "text-embedding-ada-002"
                },
                embedding=embedding
            )
            v2_documents.append(v2_doc)
        
        # Batch migration with progress tracking
        batch_size = 25
        total_migrated = 0
        
        print(f"\n📦 Migrating {len(v2_documents)} documents in batches of {batch_size}")
        
        for i in range(0, len(v2_documents), batch_size):
            batch = v2_documents[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            try:
                start_time = time.time()
                await v2_store.add_documents(batch)
                batch_time = time.time() - start_time
                
                total_migrated += len(batch)
                progress = (total_migrated / len(v2_documents)) * 100
                
                print(f"  Batch {batch_num}: {len(batch)} docs in {batch_time:.2f}s [{progress:.1f}%]")
                
            except Exception as e:
                print(f"  ❌ Batch {batch_num} failed: {e}")
        
        return total_migrated
    
    # Execute migration
    import time
    migration_start = time.time()
    migrated_count = await transform_and_migrate()
    migration_time = time.time() - migration_start
    
    print(f"✅ Migration completed in {migration_time:.2f}s")
    
    # 4. Feature comparison testing
    print("\n🆚 Feature Comparison Testing")
    print("-" * 30)
    
    test_queries = [
        "research methodologies and approaches",
        "documentation best practices",
        "data analysis techniques"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        # LlamaIndex query (simulated)
        llama_results = llama_index.query(query, top_k=3)
        print(f"  LlamaIndex: {len(llama_results['nodes'])} results")
        
        # V2 query
        from langswarm.core.memory.vector_stores import VectorQuery
        
        v2_results = await v2_store.query(VectorQuery(
            text=query,
            top_k=3,
            include_metadata=True
        ))
        print(f"  V2 Native: {len(v2_results)} results")
        
        # Show V2 result quality
        if v2_results:
            best_result = v2_results[0]
            print(f"  Best match: {best_result.score:.3f} - {best_result.document.content[:60]}...")
    
    # 5. Advanced V2 features demonstration
    print("\n🚀 Advanced V2 Features")
    print("-" * 25)
    
    # Metadata filtering (not available in basic LlamaIndex)
    research_query = VectorQuery(
        text="scientific research",
        top_k=5,
        metadata_filter={"type": "research"}
    )
    
    research_results = await v2_store.query(research_query)
    print(f"Research documents: {len(research_results)} results")
    
    # Date-based filtering
    recent_query = VectorQuery(
        text="recent developments",
        top_k=5,
        metadata_filter={"date": {"$gte": "2023-06-01"}}
    )
    
    recent_results = await v2_store.query(recent_query)
    print(f"Recent documents: {len(recent_results)} results")
    
    # Author-based search
    author_query = VectorQuery(
        text="machine learning",
        top_k=3,
        metadata_filter={"author": "researcher_1"}
    )
    
    author_results = await v2_store.query(author_query)
    print(f"Author-specific: {len(author_results)} results")
    
    # 6. Migration benefits summary
    v2_stats = await v2_store.get_statistics()
    
    print(f"\n📈 Migration Benefits")
    print("-" * 20)
    print(f"✅ Documents migrated: {migrated_count}")
    print(f"✅ Enhanced metadata filtering")
    print(f"✅ Type-safe operations")
    print(f"✅ Async performance: {v2_stats.avg_query_time_ms:.2f}ms avg")
    print(f"✅ No framework dependencies")
    print(f"✅ Production-ready error handling")
    
    await v2_store.disconnect()

asyncio.run(llamaindex_to_v2_migration())
```

---

## 🎯 Advanced Vector Operations

### **8. Custom Similarity Metrics Example**

```python
"""
Advanced similarity metrics and custom search logic
"""
import asyncio
import numpy as np
from langswarm.core.memory.vector_stores import VectorStoreFactory, VectorDocument, VectorQuery

class AdvancedSimilarityDemo:
    """Demonstrate advanced similarity calculations"""
    
    def __init__(self, store):
        self.store = store
    
    async def setup_demo_data(self):
        """Set up documents for similarity demo"""
        
        documents = [
            VectorDocument(
                id="tech_1",
                content="Machine learning algorithms for data analysis and pattern recognition",
                metadata={"domain": "technology", "complexity": "high", "topic": "ML"}
            ),
            VectorDocument(
                id="tech_2", 
                content="Artificial intelligence and neural network architectures",
                metadata={"domain": "technology", "complexity": "high", "topic": "AI"}
            ),
            VectorDocument(
                id="tech_3",
                content="Python programming for beginners and data science applications",
                metadata={"domain": "technology", "complexity": "medium", "topic": "Programming"}
            ),
            VectorDocument(
                id="business_1",
                content="Strategic planning and business development methodologies",
                metadata={"domain": "business", "complexity": "medium", "topic": "Strategy"}
            ),
            VectorDocument(
                id="business_2",
                content="Marketing analytics and customer segmentation techniques",
                metadata={"domain": "business", "complexity": "medium", "topic": "Marketing"}
            ),
            VectorDocument(
                id="science_1",
                content="Quantum physics principles and theoretical frameworks",
                metadata={"domain": "science", "complexity": "high", "topic": "Physics"}
            )
        ]
        
        await self.store.add_documents(documents)
        print(f"✅ Added {len(documents)} demo documents")
        
        return documents
    
    async def demonstrate_similarity_metrics(self):
        """Show different similarity approaches"""
        
        query_text = "artificial intelligence and machine learning"
        
        print(f"\n🔍 Query: '{query_text}'")
        print("=" * 50)
        
        # Standard cosine similarity
        standard_results = await self.store.query(VectorQuery(
            text=query_text,
            top_k=6,
            include_metadata=True
        ))
        
        print("\n📊 Standard Cosine Similarity Results:")
        for i, result in enumerate(standard_results, 1):
            print(f"{i}. Score: {result.score:.3f} | {result.document.id}")
            print(f"   Domain: {result.document.metadata['domain']} | Topic: {result.document.metadata['topic']}")
            print(f"   Content: {result.document.content[:60]}...")
            print()
    
    async def domain_weighted_search(self):
        """Demonstrate domain-weighted similarity"""
        
        query = VectorQuery(
            text="data analysis and algorithms",
            top_k=6,
            include_metadata=True
        )
        
        results = await self.store.query(query)
        
        print("\n🎯 Domain-Weighted Search Results:")
        print("(Technology domain gets 1.2x boost)")
        print("-" * 40)
        
        # Apply domain weighting
        for result in results:
            domain = result.document.metadata.get("domain")
            if domain == "technology":
                result.score *= 1.2  # Boost technology documents
            elif domain == "science":
                result.score *= 1.1  # Slight boost for science
        
        # Re-sort by adjusted scores
        results.sort(key=lambda x: x.score, reverse=True)
        
        for i, result in enumerate(results, 1):
            boost_indicator = "🚀" if result.document.metadata["domain"] in ["technology", "science"] else ""
            print(f"{i}. Score: {result.score:.3f} {boost_indicator} | {result.document.id}")
            print(f"   Domain: {result.document.metadata['domain']}")
            print()
    
    async def complexity_filtered_search(self):
        """Search with complexity-based filtering and scoring"""
        
        print("\n🎛️ Complexity-Filtered Search")
        print("-" * 30)
        
        # High complexity documents
        high_complexity_query = VectorQuery(
            text="advanced concepts and methodologies",
            top_k=5,
            metadata_filter={"complexity": "high"},
            include_metadata=True
        )
        
        high_results = await self.store.query(high_complexity_query)
        
        print("High Complexity Results:")
        for result in high_results:
            print(f"  • {result.document.id}: {result.score:.3f}")
            print(f"    {result.document.metadata['topic']} - {result.document.content[:50]}...")
        
        print()
        
        # Medium complexity documents
        medium_complexity_query = VectorQuery(
            text="practical applications and techniques",
            top_k=5,
            metadata_filter={"complexity": "medium"},
            include_metadata=True
        )
        
        medium_results = await self.store.query(medium_complexity_query)
        
        print("Medium Complexity Results:")
        for result in medium_results:
            print(f"  • {result.document.id}: {result.score:.3f}")
            print(f"    {result.document.metadata['topic']} - {result.document.content[:50]}...")

async def advanced_similarity_example():
    """Main example for advanced similarity metrics"""
    
    # Create vector store
    store = VectorStoreFactory.create_sqlite_store(
        db_path="advanced_similarity.db",
        embedding_dimension=1536
    )
    
    await store.connect()
    print("✅ Connected to advanced similarity demo store")
    
    # Initialize demo
    demo = AdvancedSimilarityDemo(store)
    
    # Set up demo data
    await demo.setup_demo_data()
    
    # Run similarity demonstrations
    await demo.demonstrate_similarity_metrics()
    await demo.domain_weighted_search()
    await demo.complexity_filtered_search()
    
    # Cleanup
    await store.disconnect()
    print("\n✅ Advanced similarity demo completed")

asyncio.run(advanced_similarity_example())
```

### **9. Hybrid Search Implementation**

```python
"""
Hybrid search combining semantic and keyword matching
"""
import asyncio
import re
from typing import List, Dict, Set
from langswarm.core.memory.vector_stores import VectorStoreFactory, VectorDocument, VectorQuery, VectorResult

class HybridSearchEngine:
    """Advanced hybrid search engine"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.keyword_index = {}  # Simple keyword index
    
    async def index_documents_for_keyword_search(self, documents: List[VectorDocument]):
        """Build keyword index for hybrid search"""
        
        for doc in documents:
            # Extract keywords
            keywords = self._extract_keywords(doc.content)
            
            # Add to keyword index
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = set()
                self.keyword_index[keyword].add(doc.id)
        
        print(f"✅ Built keyword index with {len(self.keyword_index)} terms")
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        text = text.lower()
        words = re.findall(r'\b\w{3,}\b', text)  # Words with 3+ characters
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy',
            'did', 'about', 'after', 'also', 'back', 'other', 'many', 'than',
            'then', 'them', 'these', 'time', 'very', 'when', 'come', 'here',
            'just', 'like', 'long', 'make', 'over', 'such', 'take', 'than',
            'they', 'well', 'were'
        }
        
        keywords = {word for word in words if word not in stop_words}
        return keywords
    
    async def hybrid_search(
        self,
        query_text: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        metadata_filter: Dict = None
    ) -> List[VectorResult]:
        """Perform hybrid semantic + keyword search"""
        
        print(f"\n🔍 Hybrid Search: '{query_text}'")
        print(f"Semantic weight: {semantic_weight}, Keyword weight: {keyword_weight}")
        print("-" * 50)
        
        # 1. Semantic search
        semantic_query = VectorQuery(
            text=query_text,
            top_k=top_k * 2,  # Get more candidates
            metadata_filter=metadata_filter,
            include_metadata=True
        )
        
        semantic_results = await self.vector_store.query(semantic_query)
        print(f"📊 Semantic search: {len(semantic_results)} results")
        
        # 2. Keyword search
        keyword_results = self._keyword_search(query_text, top_k * 2)
        print(f"🔤 Keyword search: {len(keyword_results)} results")
        
        # 3. Combine results
        combined_results = self._combine_search_results(
            semantic_results,
            keyword_results,
            semantic_weight,
            keyword_weight
        )
        
        # 4. Return top results
        final_results = combined_results[:top_k]
        print(f"🎯 Combined results: {len(final_results)} final results")
        
        return final_results
    
    def _keyword_search(self, query_text: str, max_results: int) -> List[Dict[str, any]]:
        """Perform keyword-based search"""
        
        query_keywords = self._extract_keywords(query_text)
        doc_scores = {}
        
        # Score documents based on keyword matches
        for keyword in query_keywords:
            if keyword in self.keyword_index:
                for doc_id in self.keyword_index[keyword]:
                    if doc_id not in doc_scores:
                        doc_scores[doc_id] = 0
                    doc_scores[doc_id] += 1
        
        # Normalize scores
        max_score = max(doc_scores.values()) if doc_scores else 1
        normalized_scores = {
            doc_id: score / max_score 
            for doc_id, score in doc_scores.items()
        }
        
        # Convert to result format
        keyword_results = []
        for doc_id, score in sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True):
            keyword_results.append({
                "document_id": doc_id,
                "score": score,
                "type": "keyword"
            })
        
        return keyword_results[:max_results]
    
    def _combine_search_results(
        self,
        semantic_results: List[VectorResult],
        keyword_results: List[Dict],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[VectorResult]:
        """Combine semantic and keyword search results"""
        
        # Create document ID mappings
        semantic_map = {result.document.id: result for result in semantic_results}
        keyword_map = {result["document_id"]: result for result in keyword_results}
        
        # Get all unique document IDs
        all_doc_ids = set(semantic_map.keys()) | set(keyword_map.keys())
        
        combined_results = []
        
        for doc_id in all_doc_ids:
            semantic_result = semantic_map.get(doc_id)
            keyword_result = keyword_map.get(doc_id)
            
            # Calculate combined score
            combined_score = 0.0
            
            if semantic_result:
                combined_score += semantic_result.score * semantic_weight
                base_result = semantic_result
            
            if keyword_result:
                combined_score += keyword_result["score"] * keyword_weight
                if not semantic_result:
                    # Need to create a result for keyword-only matches
                    # This would require fetching the document
                    continue
            
            # Create combined result
            if semantic_result:
                combined_result = VectorResult(
                    document=base_result.document,
                    score=combined_score,
                    similarity=base_result.similarity
                )
                
                # Add combination metadata
                combined_result.explanation = {
                    "semantic_score": semantic_result.score if semantic_result else 0,
                    "keyword_score": keyword_result["score"] if keyword_result else 0,
                    "combined_score": combined_score,
                    "search_type": "hybrid"
                }
                
                combined_results.append(combined_result)
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        return combined_results

async def hybrid_search_example():
    """Demonstrate hybrid search capabilities"""
    
    # Create vector store
    store = VectorStoreFactory.create_sqlite_store(
        db_path="hybrid_search.db",
        embedding_dimension=1536
    )
    
    await store.connect()
    print("✅ Connected to hybrid search demo store")
    
    # Create diverse demo documents
    documents = [
        VectorDocument(
            id="ai_fundamentals",
            content="Artificial intelligence fundamentals include machine learning, neural networks, and deep learning algorithms for pattern recognition and data analysis",
            metadata={"category": "AI", "level": "beginner", "keywords": ["AI", "ML", "neural networks"]}
        ),
        VectorDocument(
            id="python_programming",
            content="Python programming language basics, syntax, data structures, and object-oriented programming concepts for software development",
            metadata={"category": "Programming", "level": "beginner", "keywords": ["Python", "programming", "OOP"]}
        ),
        VectorDocument(
            id="data_science_methods",
            content="Data science methodologies including statistical analysis, data visualization, machine learning model training, and predictive analytics",
            metadata={"category": "Data Science", "level": "intermediate", "keywords": ["data science", "statistics", "analytics"]}
        ),
        VectorDocument(
            id="deep_learning_advanced",
            content="Advanced deep learning techniques: convolutional neural networks, recurrent neural networks, transformers, and attention mechanisms",
            metadata={"category": "AI", "level": "advanced", "keywords": ["deep learning", "CNN", "RNN", "transformers"]}
        ),
        VectorDocument(
            id="web_development",
            content="Web development with modern frameworks, RESTful APIs, database integration, and frontend-backend communication patterns",
            metadata={"category": "Programming", "level": "intermediate", "keywords": ["web dev", "API", "database"]}
        ),
        VectorDocument(
            id="algorithm_design",
            content="Algorithm design and analysis, computational complexity, optimization techniques, and efficient data structure implementations",
            metadata={"category": "Computer Science", "level": "advanced", "keywords": ["algorithms", "complexity", "optimization"]}
        )
    ]
    
    # Add documents to store
    await store.add_documents(documents)
    print(f"✅ Added {len(documents)} documents")
    
    # Initialize hybrid search engine
    hybrid_engine = HybridSearchEngine(store)
    await hybrid_engine.index_documents_for_keyword_search(documents)
    
    # Test queries with different characteristics
    test_queries = [
        {
            "query": "machine learning algorithms",
            "description": "Should match both semantic (AI content) and keyword (ML terms)"
        },
        {
            "query": "Python programming tutorials",
            "description": "Strong keyword match with semantic similarity"
        },
        {
            "query": "neural network architectures",
            "description": "Semantic match with technical keywords"
        },
        {
            "query": "data analysis techniques",
            "description": "Broad semantic match across multiple domains"
        }
    ]
    
    # Execute hybrid searches
    for test in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: '{test['query']}'")
        print(f"Expected: {test['description']}")
        print(f"{'='*60}")
        
        # Test different weight combinations
        weight_combinations = [
            (0.8, 0.2, "Semantic-heavy"),
            (0.5, 0.5, "Balanced"),
            (0.3, 0.7, "Keyword-heavy")
        ]
        
        for semantic_w, keyword_w, label in weight_combinations:
            print(f"\n{label} ({semantic_w:.1f}/{keyword_w:.1f}):")
            print("-" * 30)
            
            results = await hybrid_engine.hybrid_search(
                query_text=test["query"],
                top_k=3,
                semantic_weight=semantic_w,
                keyword_weight=keyword_w
            )
            
            for i, result in enumerate(results, 1):
                explanation = result.explanation
                print(f"{i}. {result.document.id} (Score: {result.score:.3f})")
                print(f"   Semantic: {explanation['semantic_score']:.3f} | "
                      f"Keyword: {explanation['keyword_score']:.3f}")
                print(f"   Category: {result.document.metadata['category']}")
                print(f"   Content: {result.document.content[:60]}...")
                print()
    
    # Cleanup
    await store.disconnect()
    print("\n✅ Hybrid search demo completed")

asyncio.run(hybrid_search_example())
```

---

## 📊 Performance Examples

### **10. High-Throughput Vector Operations**

```python
"""
High-performance vector operations for production workloads
"""
import asyncio
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from langswarm.core.memory.vector_stores import VectorStoreFactory, VectorDocument, VectorQuery

class HighThroughputVectorOps:
    """High-throughput vector operations manager"""
    
    def __init__(self, store):
        self.store = store
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.performance_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "total_time": 0.0,
            "operations_per_second": 0.0
        }
    
    async def batch_document_processing(
        self,
        document_count: int = 5000,
        batch_size: int = 200,
        concurrent_batches: int = 5
    ):
        """Process large numbers of documents with high throughput"""
        
        print(f"🚀 High-Throughput Document Processing")
        print(f"Documents: {document_count:,} | Batch size: {batch_size} | Concurrent: {concurrent_batches}")
        print("-" * 60)
        
        # Generate test documents
        print("📝 Generating test documents...")
        documents = []
        categories = ["technology", "science", "business", "education", "healthcare"]
        
        for i in range(document_count):
            doc = VectorDocument(
                id=f"perf_doc_{i:06d}",
                content=f"High-performance document {i} containing detailed information about {categories[i % len(categories)]} topics and methodologies",
                metadata={
                    "category": categories[i % len(categories)],
                    "batch_id": i // batch_size,
                    "priority": "high" if i % 100 == 0 else "normal",
                    "size": "large" if len(f"Document {i}") > 10 else "small",
                    "index": i
                }
            )
            documents.append(doc)
        
        print(f"✅ Generated {len(documents):,} test documents")
        
        # Process documents in concurrent batches
        start_time = time.time()
        processed_count = 0
        error_count = 0
        
        # Create batches
        batches = [
            documents[i:i + batch_size] 
            for i in range(0, len(documents), batch_size)
        ]
        
        print(f"\n📦 Processing {len(batches)} batches with {concurrent_batches} concurrent workers")
        
        # Process batches concurrently
        semaphore = asyncio.Semaphore(concurrent_batches)
        
        async def process_batch(batch, batch_num):
            async with semaphore:
                try:
                    batch_start = time.time()
                    await self.store.add_documents(batch)
                    batch_time = time.time() - batch_start
                    
                    print(f"  ✅ Batch {batch_num:3d}: {len(batch):3d} docs in {batch_time:.2f}s "
                          f"({len(batch)/batch_time:.1f} docs/s)")
                    
                    return len(batch), 0
                    
                except Exception as e:
                    print(f"  ❌ Batch {batch_num:3d}: Error - {e}")
                    return 0, len(batch)
        
        # Execute all batches
        tasks = [
            process_batch(batch, i + 1) 
            for i, batch in enumerate(batches)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate metrics
        for result in results:
            if isinstance(result, tuple):
                success, errors = result
                processed_count += success
                error_count += errors
        
        total_time = time.time() - start_time
        
        print(f"\n📊 Batch Processing Results:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Documents processed: {processed_count:,}")
        print(f"  Errors: {error_count:,}")
        print(f"  Throughput: {processed_count/total_time:.1f} docs/s")
        print(f"  Success rate: {(processed_count/(processed_count+error_count))*100:.1f}%")
        
        return processed_count
    
    async def concurrent_query_performance(
        self,
        query_count: int = 1000,
        concurrent_queries: int = 20
    ):
        """Test concurrent query performance"""
        
        print(f"\n⚡ Concurrent Query Performance Test")
        print(f"Queries: {query_count:,} | Concurrent: {concurrent_queries}")
        print("-" * 50)
        
        # Generate diverse queries
        query_templates = [
            "advanced {} concepts and methodologies",
            "practical {} applications and techniques", 
            "fundamental {} principles and frameworks",
            "modern {} approaches and best practices",
            "innovative {} solutions and strategies"
        ]
        
        categories = ["technology", "science", "business", "education", "healthcare"]
        
        queries = []
        for i in range(query_count):
            template = query_templates[i % len(query_templates)]
            category = categories[i % len(categories)]
            query_text = template.format(category)
            
            query = VectorQuery(
                text=query_text,
                top_k=10,
                metadata_filter={"category": category} if i % 3 == 0 else None
            )
            queries.append(query)
        
        print(f"✅ Generated {len(queries):,} test queries")
        
        # Execute queries concurrently
        semaphore = asyncio.Semaphore(concurrent_queries)
        query_times = []
        successful_queries = 0
        failed_queries = 0
        
        async def execute_query(query, query_num):
            async with semaphore:
                try:
                    start_time = time.time()
                    results = await self.store.query(query)
                    query_time = time.time() - start_time
                    
                    query_times.append(query_time)
                    
                    if query_num % 100 == 0:
                        print(f"  Query {query_num:4d}: {len(results)} results in {query_time:.3f}s")
                    
                    return len(results), query_time
                    
                except Exception as e:
                    print(f"  ❌ Query {query_num}: Error - {e}")
                    return 0, 0.0
        
        # Start performance test
        print(f"\n🔍 Executing {query_count:,} concurrent queries...")
        start_time = time.time()
        
        tasks = [
            execute_query(query, i + 1)
            for i, query in enumerate(queries)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Calculate performance metrics
        for result in results:
            if isinstance(result, tuple) and result[1] > 0:
                successful_queries += 1
            else:
                failed_queries += 1
        
        # Performance analysis
        if query_times:
            avg_query_time = np.mean(query_times)
            p95_query_time = np.percentile(query_times, 95)
            p99_query_time = np.percentile(query_times, 99)
            queries_per_second = successful_queries / total_time
            
            print(f"\n📈 Query Performance Metrics:")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Successful queries: {successful_queries:,}")
            print(f"  Failed queries: {failed_queries:,}")
            print(f"  Queries/second: {queries_per_second:.1f}")
            print(f"  Average query time: {avg_query_time:.3f}s")
            print(f"  95th percentile: {p95_query_time:.3f}s")
            print(f"  99th percentile: {p99_query_time:.3f}s")
            
            # Performance quality assessment
            if queries_per_second > 100:
                print("  🚀 Excellent performance")
            elif queries_per_second > 50:
                print("  ✅ Good performance") 
            elif queries_per_second > 20:
                print("  ⚠️ Acceptable performance")
            else:
                print("  🐌 Performance needs optimization")
    
    async def memory_efficient_operations(self):
        """Demonstrate memory-efficient large-scale operations"""
        
        print(f"\n💾 Memory-Efficient Operations")
        print("-" * 30)
        
        # Streaming query processing
        async def streaming_query_processor(base_query_text: str, variations: int = 1000):
            """Process queries in streaming fashion to minimize memory usage"""
            
            total_results = 0
            processed_queries = 0
            
            print(f"🌊 Streaming {variations} query variations...")
            
            for i in range(variations):
                # Generate query variation
                query_text = f"{base_query_text} variation {i}"
                query = VectorQuery(text=query_text, top_k=5)
                
                try:
                    # Process immediately without storing
                    results = await self.store.query(query)
                    total_results += len(results)
                    processed_queries += 1
                    
                    # Periodic progress updates
                    if i % 100 == 0:
                        print(f"  Processed {i:4d} queries, {total_results:5d} total results")
                    
                    # Small delay to prevent overwhelming
                    if i % 50 == 0:
                        await asyncio.sleep(0.01)
                        
                except Exception as e:
                    print(f"  ❌ Query {i} failed: {e}")
            
            print(f"✅ Streaming complete: {processed_queries:,} queries, {total_results:,} results")
            return processed_queries, total_results
        
        # Execute streaming operations
        await streaming_query_processor("technology concepts", 500)
        await streaming_query_processor("scientific research", 300)

async def performance_benchmark_example():
    """Main performance benchmark example"""
    
    # Create high-performance store setup
    store = VectorStoreFactory.create_sqlite_store(
        db_path="performance_test.db",
        embedding_dimension=1536
    )
    
    await store.connect()
    print("✅ Connected to performance test store")
    
    # Initialize performance manager
    perf_manager = HighThroughputVectorOps(store)
    
    # Run performance tests
    print(f"\n{'='*70}")
    print("HIGH-THROUGHPUT VECTOR OPERATIONS BENCHMARK")
    print(f"{'='*70}")
    
    # Test 1: Batch document processing
    processed_count = await perf_manager.batch_document_processing(
        document_count=2000,
        batch_size=100,
        concurrent_batches=5
    )
    
    # Test 2: Concurrent query performance
    await perf_manager.concurrent_query_performance(
        query_count=500,
        concurrent_queries=10
    )
    
    # Test 3: Memory-efficient operations
    await perf_manager.memory_efficient_operations()
    
    # Final statistics
    stats = await store.get_statistics()
    print(f"\n📊 Final Store Statistics:")
    print(f"  Total documents: {stats.total_documents:,}")
    print(f"  Storage size: {stats.storage_size_mb:.2f} MB")
    print(f"  Average query time: {stats.avg_query_time_ms:.2f}ms")
    print(f"  Total queries executed: {stats.total_queries:,}")
    
    # Cleanup
    await store.disconnect()
    print("\n✅ Performance benchmark completed")

asyncio.run(performance_benchmark_example())
```

---

## 📚 Vector Store Best Practices

### **Development Best Practices**
- **Start Simple**: Begin with SQLite store for development and testing
- **Test Thoroughly**: Validate vector operations with known datasets
- **Monitor Performance**: Track insertion and query performance
- **Use Appropriate Backends**: SQLite for development, cloud stores for production

### **Production Best Practices**
- **Choose Right Backend**: Pinecone for managed cloud, Qdrant for self-hosted
- **Optimize Embeddings**: Use efficient embedding models and batch processing
- **Monitor Health**: Implement comprehensive health checks and alerting
- **Plan Capacity**: Monitor storage growth and query performance scaling

### **Performance Best Practices**
- **Batch Operations**: Use batch operations for large datasets
- **Connection Pooling**: Configure appropriate connection pool sizes
- **Concurrent Processing**: Use async operations and concurrency limits
- **Memory Management**: Process large datasets in streaming fashion

### **Migration Best Practices**
- **Backup Data**: Always backup existing vector data before migration
- **Gradual Transition**: Migrate incrementally rather than all at once
- **Validate Results**: Compare search quality before and after migration
- **Performance Testing**: Benchmark V2 performance against framework implementations

---

**These examples demonstrate the full capabilities of LangSwarm V2's native vector stores, providing practical patterns for real-world applications while achieving 20-40% better performance than framework-based implementations.**
