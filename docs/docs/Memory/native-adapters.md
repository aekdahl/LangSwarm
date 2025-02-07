# LangSwarm Database Adapters Documentation

LangSwarm provides several native database adapters that enable structured storage and retrieval of documents. These adapters facilitate efficient interaction with various types of databases, each optimized for different use cases.

## Supported Database Adapters

### Shared Interface for All Adapters

All database adapters in LangSwarm are designed to implement a consistent interface. This modular approach allows developers to easily switch between different database backends without changing the application logic. Each adapter supports the following core methods:

- **`add_documents(documents: List[Dict])`**: Adds a list of documents to the database.
- **`query(query: str, filters: Optional[Dict] = None)`**: Retrieves documents based on the provided query and optional metadata filters.
- **`delete(document_ids: List[str])`**: Deletes documents from the database by their IDs.
- **`run(payload: Dict, action: str)`**: Executes the specified action (query, add_documents, delete) with the provided payload.

### 1. SQLiteAdapter

**Description**: A lightweight document store for managing structured text retrieval using SQLite.

**Features**:
- Efficient storage and retrieval of text documents.
- SQL-based keyword searches with metadata filtering.
- Operations for adding, querying, and deleting documents.

**Usage**:
```python
# Initialize the SQLite adapter
sqlite_adapter = SQLiteAdapter(identifier="sqlite_memory")

# Add documents
sqlite_adapter.add_documents([
    {"key": "doc1", "text": "This is a sample document.", "metadata": {"author": "John Doe"}},
    {"key": "doc2", "text": "Another document with more content.", "metadata": {"author": "Jane Doe"}}
])

# Query documents
results = sqlite_adapter.query(query="sample", filters={"author": "John Doe"})
print(results)

# Delete documents
sqlite_adapter.delete(document_ids=["doc1"])
```

---

### 2. RedisAdapter

**Description**: A fast key-value document store for structured retrieval using Redis.

**Features**:
- Supports keyword-based searching and metadata filtering.
- Quick access to documents for real-time applications.

**Usage**:
```python
# Initialize the Redis adapter
redis_adapter = RedisAdapter(identifier="redis_memory")

# Add documents
redis_adapter.add_documents([
    {"key": "feedback1", "text": "Great service!", "metadata": {"user": "customer1"}},
    {"key": "feedback2", "text": "Could be better.", "metadata": {"user": "customer2"}}
])

# Query documents
results = redis_adapter.query(query="great")
print(results)

# Delete documents
redis_adapter.delete(document_ids=["feedback1"])
```

---

### 3. ChromaDBAdapter

**Description**: A high-performance vector database adapter for semantic search using ChromaDB.

**Features**:
- Store and retrieve vector-embedded documents.
- Perform semantic and metadata-based searches.

**Usage**:
```python
# Initialize the ChromaDB adapter
chromadb_adapter = ChromaDBAdapter(identifier="chromadb_memory")

# Add documents
chromadb_adapter.add_documents([
    {"key": "research1", "text": "Quantum computing advances.", "metadata": {"field": "science"}},
    {"key": "research2", "text": "AI in healthcare.", "metadata": {"field": "health"}}
])

# Query documents
results = chromadb_adapter.query(query="quantum", filters={"field": "science"})
print(results)

# Delete documents
chromadb_adapter.delete(document_ids=["research1"])
```

---

### 4. GCSAdapter

**Description**: A Google Cloud Storage adapter for document storage and retrieval.

**Features**:
- Store and retrieve textual data in GCS.
- Metadata-based filtering for improved query results.

**Usage**:
```python
# Initialize the GCS adapter
gcs_adapter = GCSAdapter(identifier="gcs_memory", bucket_name="my_bucket")

# Add documents
gcs_adapter.add_documents([
    {"key": "report1", "text": "Annual financial report.", "metadata": {"year": "2022"}},
    {"key": "report2", "text": "Quarterly earnings.", "metadata": {"year": "2023"}}
])

# Query documents
results = gcs_adapter.query(query="financial")
print(results)

# Delete documents
gcs_adapter.delete(document_ids=["report1"])
```

---

### 5. ElasticsearchAdapter

**Description**: An Elasticsearch adapter for document storage and retrieval.

**Features**:
- Full-text search and metadata-based filtering.
- Vector search capabilities for similarity matching.

**Usage**:
```python
# Initialize the Elasticsearch adapter
es_adapter = ElasticsearchAdapter(identifier="es_memory", connection_string="http://localhost:9200")

# Add documents
es_adapter.add_documents([
    {"text": "New innovations in AI.", "metadata": {"category": "technology"}},
    {"text": "Climate change effects.", "metadata": {"category": "environment"}}
])

# Query documents
results = es_adapter.query(query="AI", filters={"category": "technology"})
print(results)

# Delete documents
es_adapter.delete(document_ids=["1"])