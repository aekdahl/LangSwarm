from typing import Dict  # For typing annotations
from langswarm.memory.adapters.database_adapter import DatabaseAdapter

try:
    import sqlite3
except ImportError:
    sqlite3 = None

try:
    import redis
except ImportError:
    redis = None

try:
    from chromadb import Client as ChromaDB
    from chromadb.config import Settings
except ImportError:
    ChromaDB = None

try:
    from google.cloud import storage
except ImportError:
    storage = None

try:
    from elasticsearch import Elasticsearch
except ImportError:
    storage = None


class SQLiteAdapter(DatabaseAdapter):
    """
    A lightweight document store for managing structured text retrieval using SQLite.

    This retriever enables:
    - Storing and retrieving text documents efficiently.
    - Performing SQL-based keyword searches with metadata filtering.
    - Managing document storage with insertion, querying, and deletion operations.

    Use cases:
    - Storing structured memory for AI agents.
    - Fast retrieval of past interactions or logs.
    - Querying metadata-enriched text databases.
    """
    
    def __init__(self, identifier, db_path="memory.db"):
        self.identifier = identifier
        self.brief = (
            f"SQLiteRetriever"
        )
        super().__init__(
            name="SQLiteRetriever",
            description=(
                "This retriever enables document storage and retrieval using SQLite. "
                "It supports keyword-based searching, metadata filtering, and structured querying. "
                "Ideal for managing structured agent memory or log-based retrieval."
            ),
            instruction="""
- Actions and Parameters:
    - `add_documents`: Add documents to SQLite.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with keys `"key"`, `"text"`, and optional `"metadata"`.

    - `query`: Perform a keyword-based SQL search.
      - Parameters:
        - `query` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `delete`: Remove documents from SQLite by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document keys to remove.

- Usage format:
```
execute_retriever:name|action|{"query": "Example text"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve documents related to a query:
```
execute_retriever:sqlite_retriever|query|{"query": "Customer feedback"}
```
        """
        )
        if any(var is None for var in (sqlite3)):
            raise ValueError("Unsupported database. Make sure sqlite3 is installed.")
            
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    metadata TEXT
                )
                """
            )
            conn.commit()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query', 'add_documents', or 'delete'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        elif action == "delete":
            return self.delete(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for doc in documents:
                key = doc.get("key", "")
                value = doc.get("text", "")
                metadata = str(doc.get("metadata", {}))
                cursor.execute(
                    "INSERT OR REPLACE INTO memory (key, value, metadata) VALUES (?, ?, ?)",
                    (key, value, metadata),
                )
            conn.commit()

    def query(self, query, filters=None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            sql_query = "SELECT key, value, metadata FROM memory WHERE value LIKE ?"
            params = [f"%{query}%"]

            if filters:
                for field, value in filters.items():
                    sql_query += f" AND metadata LIKE ?"
                    params.append(f'%"{field}": "{value}"%')

            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            return self.standardize_output(
                    text=[row[1] for row in rows],
                    source="SQLite",
                    metadata=[eval(row[2]) for row in rows],
                    id=[row[0] for row in rows]
                )

    def delete(self, document_ids):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for doc_id in document_ids:
                cursor.execute("DELETE FROM memory WHERE key = ?", (doc_id,))
            conn.commit()

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": False,  # SQLite does not support vector-based search.
            "metadata_filtering": True,  # Supports metadata filtering through SQL queries.
            "semantic_search": False,  # Requires external embeddings for semantic capabilities.
        }


class RedisAdapter(DatabaseAdapter):
    """
    A fast key-value document store for structured retrieval using Redis.

    This retriever enables:
    - Storing and retrieving text documents efficiently.
    - Performing keyword searches with metadata filtering.
    - Managing document storage with insertion, querying, and deletion operations.

    Use cases:
    - Storing structured memory for AI agents.
    - Fast retrieval of past interactions or logs.
    - Querying metadata-enriched Redis storage.
    """
    def __init__(self, identifier, redis_url="redis://localhost:6379/0"):
        self.identifier = identifier
        self.brief = (
            f"RedisRetriever"
        )
        super().__init__(
            name="RedisRetriever",
            description=(
                "This retriever enables document storage and retrieval using Redis. "
                "It supports keyword-based searching and metadata filtering. "
                "Ideal for real-time caching and AI memory management."
            ),
            instruction="""
- Actions and Parameters:
    - `add_documents`: Add documents to Redis.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with keys `"key"`, `"text"`, and optional `"metadata"`.

    - `query`: Perform a keyword-based Redis search.
      - Parameters:
        - `query` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `delete`: Remove documents from Redis by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document keys to remove.

- Usage format:
```
execute_retriever:name|action|{"query": "Example text"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve documents related to a query:
```
execute_retriever:redis_retriever|query|{"query": "Customer feedback"}
```
        """
        )
        if any(var is None for var in (redis)):
            raise ValueError("Unsupported database. Make sure sqlite3 is installed.")
            
        self.client = redis.StrictRedis.from_url(redis_url)

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query', 'add_documents', or 'delete'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        elif action == "delete":
            return self.delete(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        for doc in documents:
            key = doc.get("key", "")
            value = doc.get("text", "")
            metadata = doc.get("metadata", {})
            self.client.set(key, str({"value": value, "metadata": metadata}))

    def query(self, query, filters=None):
        keys = self.client.keys("*")
        results = []
        for key in keys:
            entry = eval(self.client.get(key).decode())
            if query.lower() in entry["value"].lower():
                if filters and not all(
                    entry["metadata"].get(k) == v for k, v in filters.items()
                ):
                    continue
                results.append({"key": key.decode(), **entry})

        return self.standardize_output(
            text=[result["value"] for result in results],
            source="Redis",
            metadata=[result["metadata"] for result in results],
            id=[result["key"] for result in results]
        )

    def delete(self, document_ids):
        for doc_id in document_ids:
            self.client.delete(doc_id)

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": False,  # Redis requires vector extensions like RediSearch for this.
            "metadata_filtering": True,  # Supports metadata-based filtering if implemented.
            "semantic_search": False,  # No built-in semantic search support.
        }

    

class ChromaDBAdapter(DatabaseAdapter):
    """
    A high-performance vector database adapter for semantic search using ChromaDB.

    This retriever enables:
    - Storing and retrieving vector-embedded documents.
    - Performing semantic and metadata-based search.
    - Managing indexed collections efficiently.

    Use cases:
    - AI memory retrieval and context-aware responses.
    - Fast, scalable semantic search for LLMs.
    - Querying documents with metadata-based filtering.
    """

    def __init__(self, identifier, collection_name="shared_memory", persist_directory=None, brief=None):
        self.identifier = identifier
        self.brief = brief or (
            f"The {identifier} adapter enables semantic search in the {collection_name} collection"
        )
        super().__init__(
            name="ChromaDBRetriever",
            description=(
                f"{identifier} adapter enables semantic search using ChromaDB, in the {collection_name} collection."
            ),
            instruction="""
- Actions and Parameters:
    - `add_documents`: Store documents in ChromaDB.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with `"key"`, `"text"`, and `"metadata"`.

    - `query`: Perform a semantic search.
      - Parameters:
        - `query` (str): The search query.
        - `filters` (Dict, optional): Metadata filters for refining results.
        - `n` (int, optional): Number of results to retrieve (default: 5).

    - `delete`: Remove documents by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to delete.

- Usage format:
```
execute_retriever:name|action|{"query": "Find related research papers"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve the most relevant documents:
```
execute_retriever:chromadb_retriever|query|{"query": "Quantum computing advances"}
```
        """
        )
        if ChromaDB is None:
            raise ValueError("Unsupported database. Make sure ChromaDB is installed.")
        if persist_directory:
            self.client = ChromaDB(Settings(persist_directory=persist_directory))
        else:
            self.client = ChromaDB(Settings())
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query', 'add_documents', or 'delete'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        elif action == "delete":
            return self.delete(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        for doc in documents:
            key = doc.get("key", "")
            value = doc.get("text", "")
            metadata = doc.get("metadata", {})
            self.collection.add(ids=[key], documents=[value], metadatas=[metadata])

    def query(self, query, filters=None, n=5):
        results = self.collection.query(query_texts=query)
        if filters:
            return [
                {
                    "key": res["id"],
                    "text": res["document"],
                    "metadata": res["metadata"],
                }
                for res in results
                if all(
                    res["metadata"].get(k) == v for k, v in filters.items()
                )
            ]
        
        return self.standardize_output(
            text=results["documents"][0],
            source="ChromaDB",
            metadata=results["metadatas"][0],
            id=results["ids"][0]
        )

    def delete(self, document_ids):
        for doc_id in document_ids:
            self.collection.delete(ids=[doc_id])

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": True,  # Chroma supports vector-based search.
            "metadata_filtering": True,  # Metadata filtering is a core feature.
            "semantic_search": True,  # Supports embeddings for semantic search.
        }


class GCSAdapter(DatabaseAdapter):
    """
    A Google Cloud Storage (GCS) adapter for document storage and retrieval.

    This retriever enables:
    - Storing and retrieving textual data in GCS.
    - Metadata-based filtering for improved query results.
    - Secure cloud-based document management.

    Use cases:
    - Storing AI-generated context and memory snapshots.
    - Retrieving relevant stored documents for LLM interactions.
    - Metadata-filtered searches on stored text documents.
    """
    
    def __init__(self, identifier, bucket_name, prefix="shared_memory/"):
        self.identifier = identifier
        self.brief = (
            f"GCSRetriever"
        )
        super().__init__(
            name="GCSRetriever",
            description=(
                "This retriever enables document storage and retrieval using Google Cloud Storage (GCS). "
                "It supports metadata filtering and secure, scalable text storage for AI-driven applications."
            ),
            instruction="""
- Actions and Parameters:
    - `add_documents`: Store documents in GCS.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with `"key"`, `"text"`, and `"metadata"`.

    - `query`: Retrieve stored documents matching the query.
      - Parameters:
        - `query` (str): The search query.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `delete`: Remove documents from GCS.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to delete.

- Usage format:
```
execute_retriever:name|action|{"query": "Retrieve meeting notes"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve stored documents:
```
execute_retriever:gcs_retriever|query|{"query": "Financial reports Q4"}
```
        """
        )
        if any(var is None for var in (storage)):
            raise ValueError("Unsupported database. Make sure google cloud storage is installed.")
            
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.prefix = prefix

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query', 'add_documents', or 'delete'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        elif action == "delete":
            return self.delete(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        for doc in documents:
            key = f"{self.prefix}{doc.get('key', '')}"
            value = doc.get("text", "")
            metadata = doc.get("metadata", {})
            blob = self.bucket.blob(key)
            blob.upload_from_string(str({"value": value, "metadata": metadata}))

    def query(self, query, filters=None):
        blobs = list(self.client.list_blobs(self.bucket, prefix=self.prefix))
        results = []
        for blob in blobs:
            entry = eval(blob.download_as_text())
            if query.lower() in entry["value"].lower():
                if filters and not all(
                    entry["metadata"].get(k) == v for k, v in filters.items()
                ):
                    continue
                results.append({"key": blob.name[len(self.prefix):], **entry})

        return self.standardize_output(
            text=[result["value"] for result in results],
            source="GCS",
            metadata=[result["metadata"] for result in results],
            id=[result["key"] for result in results]
        )

    def delete(self, document_ids):
        for doc_id in document_ids:
            blob = self.bucket.blob(f"{self.prefix}{doc_id}")
            if blob.exists():
                blob.delete()

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": False,  # GCS is a storage solution, not a vector database.
            "metadata_filtering": True,  # Metadata filtering implemented via stored metadata.
            "semantic_search": False,  # Semantic capabilities not supported natively.
        }


class ElasticsearchAdapter(DatabaseAdapter):
    """
    An Elasticsearch adapter for document storage and retrieval.

    This retriever enables:
    - Full-text search and metadata-based filtering.
    - Vector search for similarity matching (if enabled).
    - Scalable storage for structured and unstructured data.

    Use cases:
    - Storing and retrieving AI-generated knowledge graphs.
    - Enabling hybrid search with metadata and embeddings.
    - Querying structured text data in real-time.
    """
    
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        self.brief = (
            f"ElasticsearchRetriever"
        )
        super().__init__(
            name="ElasticsearchRetriever",
            description=(
                "This retriever allows querying and storing documents in Elasticsearch. "
                "It supports full-text search, metadata filtering, and can be extended for vector search."
            ),
            instruction="""
- Actions and Parameters:
    - `add_documents`: Store documents in Elasticsearch.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with `"text"` and optional `"metadata"`.

    - `query`: Perform a search query.
      - Parameters:
        - `query` (str): The text query for full-text search.
        - `filters` (Dict, optional): Metadata-based filtering criteria.

    - `delete`: Remove documents by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to delete.

- Usage format:
```
execute_retriever:name|action|{"query": "Find recent articles on AI"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To perform a search:
```
execute_retriever:elasticsearch_retriever|query|{"query": "Latest advancements in deep learning"}
```
        """
        )
        if Elasticsearch:
            self.db = Elasticsearch(kwargs["connection_string"])
        else:
            raise ValueError("Elasticsearch package is not installed.")

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query', 'add_documents', or 'delete'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        elif action == "delete":
            return self.delete(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        for doc in documents:
            self.db.index(index="documents", body={"text": doc["text"], "metadata": doc.get("metadata", {})})

    def add_documents_with_metadata(self, documents, metadata):
        for doc, meta in zip(documents, metadata):
            self.db.index(index="documents", body={"text": doc, "metadata": meta})

    def query(self, query, filters=None):
        body = {"query": {"match": {"text": query}}}
        if filters:
            body["query"] = {"bool": {"must": [{"match": {"text": query}}], "filter": [{"term": filters}]}}
        result = self.db.search(index="documents", body=body)
        return self.standardize_output(
            text=result["_source"]["text"],
            source="Elasticsearch",
            metadata={k: v for k, v in result["_source"].items() if k != "text"},
            id=result["_id"],
            relevance_score=result.get("_score")
        )

    def query_by_metadata(self, metadata_query, top_k=5):
        body = {"query": {"bool": {"filter": [{"term": metadata_query}]}}}
        result = self.db.search(index="documents", body=body, size=top_k)
        return self.standardize_output(
            text=result["_source"]["text"],
            source="Elasticsearch",
            metadata={k: v for k, v in result["_source"].items() if k != "text"},
            id=result["_id"],
            relevance_score=result.get("_score")
        )

    def delete(self, document_ids):
        for doc_id in document_ids:
            self.db.delete(index="documents", id=doc_id)

    def delete_by_metadata(self, metadata_query):
        body = {"query": {"bool": {"filter": [{"term": metadata_query}]}}}
        self.db.delete_by_query(index="documents", body=body)

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": True,  # Elasticsearch supports vector search with extensions like dense_vector.
            "metadata_filtering": True,  # Strong metadata filtering capabilities.
            "semantic_search": True,  # Can be configured for semantic search using embeddings.
        }
