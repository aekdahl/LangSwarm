from .database_adapter import DatabaseAdapter

try:
    from llama_index import Document
except ImportError:
    Document = None
    
try:
    from llama_index import GPTSimpleVectorIndex
except ImportError:
    GPTSimpleVectorIndex = None

try:
    import pinecone
    from llama_index import PineconeIndex
except ImportError:
    pinecone = None
    PineconeIndex = None

try:
    from llama_index import WeaviateIndex
except ImportError:
    WeaviateIndex = None

try:
    from llama_index import FAISSIndex
except ImportError:
    FAISSIndex = None

try:
    from llama_index import SQLDatabase, SQLIndex
except ImportError:
    SQLDatabase = None
    SQLIndex = None


class LlamaIndexDiskAdapter(DatabaseAdapter):
    """
    An adapter for LlamaIndex (formerly GPT Index) that stores and retrieves documents from a local disk-based index.

    This retriever enables:
    - **Efficient vector-based search** for document retrieval.
    - **Metadata-based filtering** for structured queries.
    - **Persistent storage** to maintain an index across sessions.

    **Use Cases**:
    - Storing and retrieving AI-generated knowledge graphs.
    - Conducting semantic search over indexed text.
    - Running offline document retrieval for AI agents.
    """
    
    def __init__(self, identifier, index_path="index.json"):
        """
        Initialize the LlamaIndex adapter with a local index.

        :param index_path: str - Path to the stored LlamaIndex JSON file.
        """
        self.identifier = identifier
        self.brief = (
            f"LlamaIndexRetriever"
        )
        super().__init__(
            name="LlamaIndexRetriever",
            description=(
                "This retriever allows querying and storing documents using LlamaIndex. "
                "It supports vector-based search, metadata filtering, and persistent storage."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Store new documents in LlamaIndex.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries containing `"text"` and optional `"metadata"`.

    - `query`: Perform a search query.
      - Parameters:
        - `query` (str): The text query for semantic search.
        - `filters` (Dict, optional): Metadata-based filtering criteria.

    - `delete`: Not supported in LlamaIndex.

- **Usage format**:
```
execute_retriever:name|action|{"query": "Find documents about AI models"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To perform a search:
```
execute_retriever:llamaindex_retriever|query|{"query": "Explain reinforcement learning"}
```
        """
        )
        if all(var is not None for var in (GPTSimpleVectorIndex, Document)):
            try:
                self.index = GPTSimpleVectorIndex.load_from_disk(index_path)
            except FileNotFoundError:
                self.index = GPTSimpleVectorIndex([])
        else:
            raise ValueError("Unsupported database. Make sure LlamaIndex is installed.")

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query' or 'add_documents'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        docs = [Document(text=doc["text"], metadata=doc.get("metadata", {})) for doc in documents]
        self.index.insert(docs)
        self.index.save_to_disk()

    def query(self, query, filters=None):
        results = self.index.query(query)
        if filters:
            results = [res for res in results if all(res.extra_info.get(k) == v for k, v in filters.items())]
        
        return self.standardize_output(
            text=[result["content"] for result in results],
            source="LlamaIndex",
            metadata=[result["extra_info"] for result in results],
            id=[result["document_id"] for result in results],
            relevance_score=[result.get("score") for result in results]
        )

    def delete(self, document_ids):
        raise NotImplementedError("Delete functionality not implemented for LlamaIndex")

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": True,
            "metadata_filtering": True,
            "semantic_search": True,
        }


class LlamaIndexPineconeAdapter(LlamaIndexAdapter):
    """
    Adapter for Pinecone integration with LlamaIndex.

    This retriever enables:
    - **Efficient vector-based document retrieval** using Pinecone.
    - **Metadata-based filtering** for structured queries.
    - **Scalability** for handling large-scale vector search.

    **Use Cases**:
    - Storing and retrieving AI-generated knowledge graphs.
    - Performing semantic search over indexed text.
    - Leveraging cloud-hosted Pinecone for fast query performance.

    Setup:
        1. Install Pinecone: `pip install pinecone-client`.
        2. Initialize Pinecone with your API key and environment:
           ```
           pinecone.init(api_key="your-api-key", environment="your-environment")
           ```

    Usage:
        Add, query, and manage documents in a Pinecone-backed vector index.
    """
    def __init__(self, identifier, index_name="pinecone-index"):
        """
        Initialize the Pinecone-backed LlamaIndex retriever.

        :param index_name: str - Name of the Pinecone index.
        """
        self.identifier = identifier
        self.brief = (
            f"LlamaIndexPineconeRetriever"
        )
        super().__init__(
            name="LlamaIndexPineconeRetriever",
            description=(
                "This retriever integrates LlamaIndex with Pinecone for scalable vector-based retrieval. "
                "Supports metadata filtering, semantic search, and fast lookup."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Store new documents in the Pinecone-backed LlamaIndex.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries containing `"text"` and optional `"metadata"`.

    - `query`: Perform a semantic search query.
      - Parameters:
        - `query_text` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata-based filtering criteria.

    - `delete`: Remove specific documents from the index.
      - Parameters:
        - `document_ids` (List[str]): The list of document IDs to delete.

- **Usage format**:
```
execute_retriever:name|action|{"query_text": "Explain deep learning"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To perform a search:
```
execute_retriever:llamaindex_pinecone|query|{"query_text": "Explain reinforcement learning"}
```
        """
        )
        if pinecone is None or PineconeIndex is None:
            raise ImportError("Pinecone or LlamaIndex is not installed. Please install the required packages.")

        self.index_name = index_name
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(index_name, dimension=768)  # Update dimension based on your embedding model
        self.index = PineconeIndex(index_name=index_name)

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
        docs = [Document(text=doc["text"], metadata=doc.get("metadata", {})) for doc in documents]
        self.index.insert(docs)

    def query(self, query_text):
        results = self.index.query(query_text)
        return self.standardize_output(
            text=[result["content"] for result in results],
            source="LlamaIndex",
            metadata=[result["extra_info"] for result in results],
            id=[result["document_id"] for result in results],
            relevance_score=[result.get("score") for result in results]
        )

    def delete(self, document_ids):
        self.index.delete(document_ids)

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": True,
            "metadata_filtering": True,
            "semantic_search": True,
        }


class LlamaIndexWeaviateAdapter(LlamaIndexAdapter):
    """
    Adapter for Weaviate integration with LlamaIndex.
    
    This retriever enables:
    - **Efficient vector-based document retrieval** using Weaviate.
    - **Metadata-based filtering** for structured queries.
    - **Scalability** for handling large-scale vector search.

    **Use Cases**:
    - Storing and retrieving AI-generated knowledge graphs.
    - Performing semantic search over indexed text.
    - Leveraging cloud-hosted Weaviate for fast query performance.

    Setup:
        1. Install Weaviate client: `pip install weaviate-client`.
        2. Ensure you have a running Weaviate instance and its URL.

    Usage:
        Add, query, and manage documents in a Weaviate-backed vector index.
    """
    def __init__(self, identifier, weaviate_url):
        """
        Initialize the Weaviate-backed LlamaIndex retriever.

        :param weaviate_url: str - The URL of the Weaviate instance.
        """
        self.identifier = identifier
        self.brief = (
            f"LlamaIndexWeaviateRetriever"
        )
        super().__init__(
            name="LlamaIndexWeaviateRetriever",
            description=(
                "This retriever integrates LlamaIndex with Weaviate for scalable vector-based retrieval. "
                "Supports metadata filtering, semantic search, and fast lookup."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Store new documents in the Weaviate-backed LlamaIndex.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries containing `"text"` and optional `"metadata"`.

    - `query`: Perform a semantic search query.
      - Parameters:
        - `query_text` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata-based filtering criteria.

    - `delete`: Remove specific documents from the index.
      - Parameters:
        - `document_ids` (List[str]): The list of document IDs to delete.

- **Usage format**:
```
execute_retriever:name|action|{"query_text": "Explain deep learning"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To perform a search:
```
execute_retriever:llamaindex_weaviate|query|{"query_text": "Explain reinforcement learning"}
```
        """
        )
        if WeaviateIndex is None:
            raise ImportError("Weaviate or LlamaIndex is not installed. Please install the required packages.")

        self.index = WeaviateIndex(weaviate_url=weaviate_url)

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query' or 'add_documents'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        docs = [Document(text=doc["text"], metadata=doc.get("metadata", {})) for doc in documents]
        self.index.insert(docs)

    def query(self, query_text):
        results = self.index.query(query_text)
        return self.standardize_output(
            text=[result["content"] for result in results],
            source="LlamaIndex",
            metadata=[result["extra_info"] for result in results],
            id=[result["document_id"] for result in results],
            relevance_score=[result.get("score") for result in results]
        )

    def delete(self, document_ids):
        raise NotImplementedError("Document deletion is not yet supported for Weaviate.")

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": True,
            "metadata_filtering": True,
            "semantic_search": True,
        }


class LlamaIndexFAISSAdapter(LlamaIndexAdapter):
    """
    Adapter for FAISS integration with LlamaIndex.

    This retriever enables:
    - **Local vector-based document retrieval** using FAISS.
    - **Fast and scalable similarity search** with dense embeddings.
    - **Efficient storage of vectors** without external dependencies.

    **Use Cases**:
    - Performing **fast** nearest-neighbor search on local text embeddings.
    - Running **offline** similarity-based retrieval for AI applications.
    - Storing **high-dimensional vector representations** in a local database.

    Setup:
        1. Install FAISS: `pip install faiss-cpu`.
        2. Initialize a FAISS index for local vector storage.

    Usage:
        Add, query, and manage documents in a FAISS-backed vector index.
    """
    def __init__(self, identifier, index_path="faiss_index.json"):
        """
        Initialize the FAISS-backed LlamaIndex retriever.

        :param index_path: str - The file path for storing FAISS index data.
        """
        self.identifier = identifier
        self.brief = (
            f"LlamaIndexFAISSRetriever"
        )
        super().__init__(
            name="LlamaIndexFAISSRetriever",
            description=(
                "This retriever integrates LlamaIndex with FAISS for high-speed local vector-based retrieval. "
                "Supports semantic search and offline similarity queries."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Store new documents in the FAISS-backed LlamaIndex.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries containing `"text"` and optional `"metadata"`.

    - `query`: Perform a semantic search query.
      - Parameters:
        - `query_text` (str): The text query for retrieval.

    - `delete`: Not supported in FAISS.
      - FAISS does not support deletion of specific vectors.

- **Usage format**:
```
execute_retriever:name|action|{"query_text": "Explain transformers in NLP"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To perform a search:
```
execute_retriever:llamaindex_faiss|query|{"query_text": "Explain reinforcement learning"}
```
        """
        )
        if FAISSIndex is None:
            raise ImportError("FAISS or LlamaIndex is not installed. Please install the required packages.")

        try:
            self.index = FAISSIndex.load_from_disk(index_path)
        except FileNotFoundError:
            self.index = FAISSIndex([])

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query' or 'add_documents'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        docs = [Document(text=doc["text"], metadata=doc.get("metadata", {})) for doc in documents]
        self.index.insert(docs)
        self.index.save_to_disk("faiss_index.json")

    def query(self, query_text):
        results = self.index.query(query_text)
        return self.standardize_output(
            text=[result["content"] for result in results],
            source="LlamaIndex",
            metadata=[result["extra_info"] for result in results],
            id=[result["document_id"] for result in results],
            relevance_score=[result.get("score") for result in results]
        )

    def delete(self, document_ids):
        raise NotImplementedError("Document deletion is not yet supported for FAISS.")

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": True,
            "metadata_filtering": False,  # FAISS lacks native metadata filtering.
            "semantic_search": True,
        }


class LlamaIndexSQLAdapter(LlamaIndexAdapter):
    """
    Adapter for SQL integration with LlamaIndex.

    This retriever enables:
    - **Storing and retrieving structured text data** in SQL databases.
    - **Efficient metadata filtering** through relational queries.
    - **Indexing textual documents** for future retrieval.

    **Use Cases**:
    - Storing AI-generated summaries, reports, or user interactions.
    - Querying structured text documents with SQL-based filtering.
    - Combining **text retrieval with traditional relational data**.

    **Supported Databases**:
    - PostgreSQL, MySQL, SQLite, and other SQLAlchemy-compatible databases.

    Setup:
        1. Install a SQL database driver (e.g., `pip install sqlite`).
        2. Create and configure your database URI.

    Usage:
        Add, query, and manage documents in a SQL-backed index.
    """
    def __init__(self, identifier, database_uri, index_path="sql_index.json"):
        """
        Initialize the SQL-backed LlamaIndex retriever.

        :param database_uri: str - The SQLAlchemy-compatible database connection URI.
        :param index_path: str - The file path for storing SQL index metadata.
        """
        self.identifier = identifier
        self.brief = (
            f"LlamaIndexSQLRetriever"
        )
        super().__init__(
            name="LlamaIndexSQLRetriever",
            description=(
                "This retriever integrates LlamaIndex with SQL databases, allowing efficient storage, retrieval, "
                "and structured filtering of text-based documents."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Store new documents in the SQL-backed index.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries containing `"text"` and optional `"metadata"`.

    - `query`: Retrieve stored documents based on text similarity.
      - Parameters:
        - `query_text` (str): The text query for retrieval.

    - `delete`: Not supported for SQL-based retrieval.

- **Usage format**:
```
execute_retriever:name|action|{"query_text": "Find reports on climate change"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To perform a search:
```
execute_retriever:llamaindex_sql|query|{"query_text": "Summarize user conversations"}
```
        """
        )
        if SQLDatabase is None or SQLIndex is None:
            raise ImportError("SQLDatabase or LlamaIndex is not installed. Please install the required packages.")

        self.sql_db = SQLDatabase(database_uri=database_uri)
        try:
            self.index = SQLIndex.load_from_disk(index_path)
        except FileNotFoundError:
            self.index = SQLIndex([], sql_database=self.sql_db)

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query' or 'add_documents'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        for doc in documents:
            self.sql_db.insert({"text": doc["text"], **doc.get("metadata", {})})
        self.index.refresh()

    def query(self, query_text):
        results = self.index.query(query_text)
        return self.standardize_output(
            text=[result["content"] for result in results],
            source="LlamaIndex",
            metadata=[result["extra_info"] for result in results],
            id=[result["document_id"] for result in results],
            relevance_score=[result.get("score") for result in results]
        )

    def delete(self, document_ids):
        raise NotImplementedError("Document deletion is not yet supported for SQL.")

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": False,
            "metadata_filtering": True,
            "semantic_search": False,
        }
