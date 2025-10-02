from .database_adapter import DatabaseAdapter

try:
    from langchain.embeddings.openai import OpenAIEmbeddings
except ImportError:
    OpenAIEmbeddings = None
    
try:
    from langchain.vectorstores import Pinecone
    import pinecone
except ImportError:
    Pinecone = None

try:
    from langchain.vectorstores import Weaviate
except ImportError:
    Weaviate = None

try:
    from langchain.vectorstores import Milvus
except ImportError:
    Milvus = None

try:
    from langchain.vectorstores import Qdrant
except ImportError:
    Qdrant = None

try:
    from langchain.vectorstores import SQLite
except ImportError:
    SQLite = None

try:
    from langchain.vectorstores import Redis
    import redis
except ImportError:
    Redis = None

try:
    from langchain.vectorstores import Chroma
    import chromadb
except ImportError:
    Chroma = None


class PineconeAdapter(DatabaseAdapter):
    """
    A retriever for managing vector-based document retrieval with Pinecone.

    This retriever enables:
    - Adding and storing vectorized documents.
    - Querying using semantic similarity search.
    - Filtering results based on metadata.
    - Deleting documents by ID or metadata.

    Use cases:
    - Searching for relevant information within large document datasets.
    - Retrieving semantically similar text passages.
    - Filtering documents based on structured metadata queries.
    """
    
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        self.brief = (
            f"PineconeRetriever"
        )
        super().__init__(
            name="PineconeRetriever",
            description=(
                "This retriever enables searching for relevant documents using Pinecone's vector-based similarity search. "
                "Supports semantic search, metadata filtering, and structured retrieval. "
                "Ensure the Pinecone environment is correctly set up."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Add documents to the Pinecone index.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with keys `"text"` and optional `"metadata"`.

    - `query`: Perform similarity-based search.
      - Parameters:
        - `query` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `query_by_metadata`: Retrieve documents using metadata-based filtering.
      - Parameters:
        - `metadata_query` (Dict): The metadata criteria for filtering.
        - `top_k` (int, optional): The number of results to return (default: 5).

    - `delete`: Remove documents from the Pinecone index by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to remove.

    - `delete_by_metadata`: Remove documents based on metadata.
      - Parameters:
        - `metadata_query` (Dict): Metadata criteria to filter documents for deletion.

- **Usage format**:
    ```
    execute_retriever:name|action|{"query": "Example text"}
    ```
    Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve documents related to a query:
    ```
    execute_retriever:pinecone_retriever|query|{"query": "Latest advancements in AI"}
    ```
        """
        )
        if all(var is not None for var in (Pinecone, OpenAIEmbeddings)):
            pinecone.init(api_key=kwargs["api_key"], environment=kwargs["environment"])
            self.db = Pinecone(index_name=kwargs["index_name"], embedding_function=OpenAIEmbeddings())
        else:
            raise ValueError("Unsupported vector database. Make sure LangChain and Pinecone packages are installed.")

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query', 'query_by_metadata', 'add_documents', 'delete', or 'delete_by_metadata'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "query_by_metadata":
            return self.query_by_metadata(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        elif action == "delete":
            return self.delete(**payload)
        elif action == "delete_by_metadata":
            return self.delete_by_metadata(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        texts = [doc["text"] for doc in documents]
        metadata = [doc.get("metadata", {}) for doc in documents]
        self.db.add_texts(texts, metadatas=metadata)

    def add_documents_with_metadata(self, documents, metadata):
        self.db.add_texts(documents, metadatas=metadata)
    
    def query(self, query: str, filters: Dict = None, top_k: int = 5):
        translated_filters = self.translate_filters(filters) if filters else None
        result = self.db.similarity_search(query, filter=translated_filters, k=top_k)
        return [
            self.standardize_output(
                text=item["text"],
                source="Pinecone",
                metadata=item["metadata"],
                id=item["id"],
                relevance_score=item.get("score")
            )
            for item in result
        ]

    def query_by_metadata(self, metadata_query, top_k=5):
        result = self.db.similarity_search(query=None, filter=metadata_query, k=top_k)
        return self.standardize_output(
            text=result["text"],
            source="Pinecone",
            metadata=result["metadata"],
            id=result["id"],
            relevance_score=result.get("score")
        )
        
    def delete(self, document_ids):
        for doc_id in document_ids:
            self.db.delete(doc_id)

    def delete_by_metadata(self, metadata_query):
        results = self.db.similarity_search(query=None, filter=metadata_query, k=1000)
        ids_to_delete = [doc["id"] for doc in results]
        for doc_id in ids_to_delete:
            self.db.delete(doc_id)
            
    def translate_filters(self, filters: Dict):
        """
        Convert standardized filter format into Pinecone's filter format.
        """
        pinecone_filters = {}
        for condition in filters.get("conditions", []):
            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]

            if operator == "==":
                pinecone_filters[field] = {"$eq": value}
            elif operator == ">=":
                pinecone_filters[field] = {"$gte": value}
            elif operator == "<=":
                pinecone_filters[field] = {"$lte": value}
        
        return pinecone_filters
            
    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": True,  # Pinecone supports vector-based similarity search.
            "metadata_filtering": True,  # Metadata filtering is available.
            "semantic_search": True,  # Embedding-based semantic search supported via OpenAIEmbeddings.
        }


class WeaviateAdapter(DatabaseAdapter):
    """
    A retriever for managing vector-based document retrieval with Weaviate.

    This retriever enables:
    - Adding and storing vectorized documents.
    - Querying using semantic similarity search.
    - Filtering results based on metadata.
    - Deleting documents by ID or metadata.

    Use cases:
    - Searching for relevant information within large document datasets.
    - Retrieving semantically similar text passages.
    - Filtering documents based on structured metadata queries.
    """
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        self.brief = (
            f"WeaviateRetriever"
        )
        super().__init__(
            name="WeaviateRetriever",
            description=(
                "This retriever enables searching for relevant documents using Weaviate's vector-based similarity search. "
                "Supports semantic search, metadata filtering, and structured retrieval. "
                "Ensure the Weaviate environment is correctly set up."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Add documents to the Weaviate index.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with keys `"text"` and optional `"metadata"`.

    - `query`: Perform similarity-based search.
      - Parameters:
        - `query` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `query_by_metadata`: Retrieve documents using metadata-based filtering.
      - Parameters:
        - `metadata_query` (Dict): The metadata criteria for filtering.
        - `top_k` (int, optional): The number of results to return (default: 5).

    - `delete`: Remove documents from the Weaviate index by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to remove.

    - `delete_by_metadata`: Remove documents based on metadata.
      - Parameters:
        - `metadata_query` (Dict): Metadata criteria to filter documents for deletion.

- **Usage format**:
```
execute_retriever:name|action|{"query": "Example text"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve documents related to a query:
```
execute_retriever:weaviate_retriever|query|{"query": "Latest advancements in AI"}
```
        """
        )
        if all(var is not None for var in (Weaviate, OpenAIEmbeddings)):
            self.db = Weaviate(
                url=kwargs["weaviate_url"],
                embedding_function=OpenAIEmbeddings(),
                client=kwargs.get("weaviate_client", None)  # Optional: Add Weaviate client instance if needed
            )
        else:
            raise ValueError("Unsupported vector database. Make sure LangChain and Weaviate packages are installed.")

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query', 'query_by_metadata', 'add_documents', 'delete', or 'delete_by_metadata'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "query_by_metadata":
            return self.query_by_metadata(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        elif action == "delete":
            return self.delete(**payload)
        elif action == "delete_by_metadata":
            return self.delete_by_metadata(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        texts = [doc["text"] for doc in documents]
        metadata = [doc.get("metadata", {}) for doc in documents]
        self.db.add_texts(texts, metadatas=metadata)

    def add_documents_with_metadata(self, documents, metadata):
        for doc, meta in zip(documents, metadata):
            self.db.add_text(doc, metadata=meta)

    def query(self, query: str, filters: Dict = None, top_k: int = 5):
        """
        Perform a similarity-based search with optional metadata filtering.

        Args:
            query (str): The query string for retrieval.
            filters (Dict, optional): Metadata filters.
            top_k (int): Number of results to return (default: 5).

        Returns:
            List[Dict]: A list of standardized document results.
        """
        translated_filters = self.translate_filters(filters) if filters else None
        results = self.db.similarity_search(query, filter=translated_filters, k=top_k)

        return [
            self.standardize_output(
                text=item["properties"].get("text"),
                source="Weaviate",
                metadata={k: v for k, v in item["properties"].items() if k != "text"},
                id=item["id"],
                relevance_score=1 - item.get("distance", 0)
            )
            for item in results
        ]

    def translate_filters(self, filters: Dict):
        """
        Convert standardized filters into Weaviate's filtering format.

        Args:
            filters (Dict): Standardized filter structure.

        Returns:
            Dict: Weaviate-compatible filter query.
        """
        weaviate_filters = []
        for condition in filters.get("conditions", []):
            field, operator, value = condition["field"], condition["operator"], condition["value"]

            if operator == "==":
                weaviate_filters.append({"path": [field], "operator": "Equal", "valueText": value})
            elif operator == "!=":
                weaviate_filters.append({"path": [field], "operator": "NotEqual", "valueText": value})
            elif operator in [">=", "<="]:
                weaviate_filters.append({"path": [field], "operator": operator, "valueNumber": value})

        return {"operator": "And", "operands": weaviate_filters} if weaviate_filters else None

    def delete(self, document_ids):
        try:
            for doc_id in document_ids:
                self.db.delete_by_id(doc_id)
        except:
            # Not directly supported in LangChain's Weaviate implementation
            raise NotImplementedError("Document deletion is not yet supported in WeaviateAdapter.")

    def delete_by_metadata(self, metadata_query):
        self.db.delete_by_metadata(metadata_query)

    def capabilities(self) -> Dict[str, bool]:
        return {
            "vector_search": True,  # Weaviate supports vector-based similarity search.
            "metadata_filtering": True,  # Metadata filtering is available.
            "semantic_search": True,  # Semantic search is supported with embeddings.
        }


class MilvusAdapter(DatabaseAdapter):
    """
    A retriever for managing vector-based document retrieval using Milvus.

    This retriever enables:
    - Adding and storing vectorized documents.
    - Querying using semantic similarity search.
    - Filtering results based on metadata.
    - Deleting documents by ID or metadata.

    Use cases:
    - Searching for relevant information within large document datasets.
    - Retrieving semantically similar text passages.
    - Filtering documents based on structured metadata queries.
    """
    
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        self.brief = (
            f"MilvusRetriever"
        )
        super().__init__(
            name="MilvusRetriever",
            description=(
                "This retriever enables searching for relevant documents using Milvus' vector-based similarity search. "
                "Supports semantic search, metadata filtering, and structured retrieval. "
                "Ensure the Milvus environment is correctly set up."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Add documents to the Milvus index.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with keys `"text"` and optional `"metadata"`.

    - `query`: Perform similarity-based search.
      - Parameters:
        - `query` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `query_by_metadata`: Retrieve documents using metadata-based filtering.
      - Parameters:
        - `metadata_query` (Dict): The metadata criteria for filtering.
        - `top_k` (int, optional): The number of results to return (default: 5).

    - `delete`: Remove documents from the Milvus index by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to remove.

    - `delete_by_metadata`: Remove documents based on metadata.
      - Parameters:
        - `metadata_query` (Dict): Metadata criteria to filter documents for deletion.

- **Usage format**:
```
execute_retriever:name|action|{"query": "Example text"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve documents related to a query:
```
execute_retriever:milvus_retriever|query|{"query": "Latest advancements in AI"}
```
        """
        )
        if all(var is not None for var in (Milvus, OpenAIEmbeddings)):
            self.db = Milvus(
                embedding_function=OpenAIEmbeddings(),
                collection_name=kwargs["collection_name"],
                connection_args={
                    "host": kwargs["milvus_host"],
                    "port": kwargs["milvus_port"]
                }
            )
        else:
            raise ValueError("Unsupported vector database. Make sure LangChain and Milvus packages are installed.")

    def run(self, payload, action="query"):
        """
        Execute retrieval actions.
        :param payload: Dict - The input query parameters.
        :param action: str - The action to perform: 'query', 'query_by_metadata', 'add_documents', 'delete', or 'delete_by_metadata'.
        :return: str - The result of the action.
        """
        if action == "query":
            return self.query(**payload)
        elif action == "add_documents":
            return self.add_documents(**payload)
        elif action == "delete":
            return self.delete(**payload)
        elif action == "delete_by_metadata":
            return self.delete_by_metadata(**payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
    
    def add_documents(self, documents):
        texts = [doc["text"] for doc in documents]
        metadata = [doc.get("metadata", {}) for doc in documents]
        self.db.add_texts(texts, metadatas=metadata)

    def add_documents_with_metadata(self, documents, metadata):
        self.db.add_texts(documents, metadatas=metadata)

    def query(self, query: str, filters: Dict = None, top_k: int = 5):
        """
        Perform a similarity-based search with optional metadata filtering.

        Args:
            query (str): The query string for retrieval.
            filters (Dict, optional): Metadata filters.
            top_k (int): Number of results to return (default: 5).

        Returns:
            List[Dict]: A list of standardized document results.
        """
        translated_filters = self.translate_filters(filters) if filters else None
        results = self.db.similarity_search(query, filter=translated_filters, k=top_k)

        return [
            self.standardize_output(
                text=item["text"],
                source="Milvus",
                metadata=item["metadata"],
                id=item["id"],
                relevance_score=item.get("score")
            )
            for item in results
        ]

    def translate_filters(self, filters: Dict):
        """
        Convert standardized filters into Milvus' filtering format.

        Args:
            filters (Dict): Standardized filter structure.

        Returns:
            Dict: Milvus-compatible filter query.
        """
        milvus_filters = []
        for condition in filters.get("conditions", []):
            field, operator, value = condition["field"], condition["operator"], condition["value"]

            if operator == "==":
                milvus_filters.append(f"{field} = '{value}'")
            elif operator == "!=":
                milvus_filters.append(f"{field} != '{value}'")
            elif operator == ">=":
                milvus_filters.append(f"{field} >= {value}")
            elif operator == "<=":
                milvus_filters.append(f"{field} <= {value}")

        return " AND ".join(milvus_filters) if milvus_filters else None

    def delete(self, document_ids):
        try:
            for doc_id in document_ids:
                self.db.delete_by_id(doc_id)
        except:
            # Not directly supported in LangChain's Milvus implementation
            raise NotImplementedError("Document deletion is not yet supported in MilvusAdapter.")

    def delete_by_metadata(self, metadata_query):
        self.db.delete_by_metadata(metadata_query)


class QdrantAdapter(DatabaseAdapter):
    """
    A retriever for managing vector-based document retrieval using Qdrant.

    This retriever enables:
    - Adding and storing vectorized documents.
    - Querying using semantic similarity search.
    - Filtering results based on metadata.
    - Deleting documents by ID.

    Use cases:
    - Searching for relevant information within large document datasets.
    - Retrieving semantically similar text passages.
    - Filtering documents based on structured metadata queries.
    """
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        self.brief = (
            f"QdrantRetriever"
        )
        super().__init__(
            name="QdrantRetriever",
            description=(
                "This retriever enables searching for relevant documents using Qdrant's vector-based similarity search. "
                "Supports semantic search, metadata filtering, and structured retrieval. "
                "Ensure the Qdrant environment is correctly set up."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Add documents to the Qdrant index.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with keys `"text"` and optional `"metadata"`.

    - `query`: Perform similarity-based search.
      - Parameters:
        - `query` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `delete`: Remove documents from the Qdrant index by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to remove.

- **Usage format**:
```
execute_retriever:name|action|{"query": "Example text"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve documents related to a query:
```
execute_retriever:qdrant_retriever|query|{"query": "Latest advancements in AI"}
```
        """
        )
        if all(var is not None for var in (Qdrant, OpenAIEmbeddings)):
            self.db = Qdrant(
                host=kwargs["qdrant_host"],
                port=kwargs["qdrant_port"],
                embedding_function=OpenAIEmbeddings(),
                collection_name=kwargs["collection_name"]
            )
        else:
            raise ValueError("Unsupported vector database. Make sure LangChain and Qdrant packages are installed.")

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
        texts = [doc["text"] for doc in documents]
        metadata = [doc.get("metadata", {}) for doc in documents]
        self.db.add_texts(texts, metadatas=metadata)

    def query(self, query, filters=None):
        embedding = self.embedding_function.embed_query(query)
        translated_filters = self.translate_filters(filters) if filters else None
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=top_k,
            query_filter=translated_filters
        )

        return [
            self.standardize_output(
                text=hit.payload.get("text", ""),
                source="Qdrant",
                metadata=hit.payload,
                id=hit.id,
                relevance_score=hit.score
            )
            for hit in search_results
        ]

    def delete(self, document_ids):
        self.db.delete(ids=document_ids)
        
    def translate_filters(self, filters: Dict):
        """
        Convert standardized filter format into Qdrant's filtering structure.
        """
        conditions = []
        for condition in filters.get("conditions", []):
            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]

            if operator == "==":
                conditions.append(FieldCondition(key=field, match={"value": value}))
            elif operator == ">=":
                conditions.append(FieldCondition(key=field, range=Range(gte=value)))
            elif operator == "<=":
                conditions.append(FieldCondition(key=field, range=Range(lte=value)))

        return Filter(must=conditions)


class SQLiteAdapter(DatabaseAdapter):
    """
    A retriever for managing document storage and retrieval using SQLite.

    This retriever enables:
    - Adding and storing vectorized documents.
    - Querying using semantic similarity search.
    - Filtering results based on metadata.
    - Deleting documents by ID.

    Use cases:
    - Lightweight document storage and retrieval for small-scale applications.
    - Running similarity-based searches on structured text data.
    - Querying documents with both text and metadata constraints.
    """
    
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        self.brief = (
            f"SQLiteRetriever"
        )
        super().__init__(
            name="SQLiteRetriever",
            description=(
                "This retriever enables structured document retrieval using SQLite. "
                "Supports semantic search, metadata filtering, and efficient vector-based querying. "
                "Ensure the SQLite environment is correctly set up."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Add documents to the SQLite database.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with keys `"text"` and optional `"metadata"`.

    - `query`: Perform similarity-based search.
      - Parameters:
        - `query` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `delete`: Remove documents from the SQLite database by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to remove.

- **Usage format**:
```
execute_retriever:name|action|{"query": "Example text"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve documents related to a query:
```
execute_retriever:sqlite_retriever|query|{"query": "Latest advancements in AI"}
```
        """
        )
        if all(var is not None for var in (SQLite, OpenAIEmbeddings)):
            self.db = SQLite(
                embedding_function=OpenAIEmbeddings(),
                database_path=kwargs["database_path"],
                table_name=kwargs["table_name"]
            )
        else:
            raise ValueError("Unsupported database. Make sure LangChain and SQLite packages are installed.")
    
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
        texts = [doc["text"] for doc in documents]
        metadata = [doc.get("metadata", {}) for doc in documents]
        self.db.add_texts(texts, metadatas=metadata)

    def query(self, query: str, filters: Dict = None, top_k: int = 5):
        """
        Perform a similarity-based search with optional metadata filtering.

        Args:
            query (str): The query string for retrieval.
            filters (Dict, optional): Metadata filters for refining results.
            top_k (int): Number of results to return (default is 5).

        Returns:
            List[Dict]: A list of standardized document results.
        """
        translated_filters = self.translate_filters(filters) if filters else None
        results = self.db.similarity_search(query, filter=translated_filters, k=top_k)

        return [
            self.standardize_output(
                text=item["text"],
                source="SQLite",
                metadata=item["metadata"],
                id=item["id"],
                relevance_score=item.get("score")
            )
            for item in results
        ]

    def delete(self, document_ids):
        self.db.delete(ids=document_ids)
        
    def translate_filters(self, filters: Dict):
        """
        Convert standardized filters into SQLite's metadata filtering format.

        Args:
            filters (Dict): Standardized filter structure.

        Returns:
            Dict: SQLite-compatible filter dictionary.
        """
        sqlite_filters = []
        for condition in filters.get("conditions", []):
            field, operator, value = condition["field"], condition["operator"], condition["value"]

            if operator == "==":
                sqlite_filters.append(f"{field} = '{value}'")
            elif operator == "!=":
                sqlite_filters.append(f"{field} != '{value}'")
            elif operator == ">=":
                sqlite_filters.append(f"{field} >= {value}")
            elif operator == "<=":
                sqlite_filters.append(f"{field} <= {value}")

        return " AND ".join(sqlite_filters) if sqlite_filters else None


class RedisAdapter(DatabaseAdapter):
    """
    A retriever for managing document storage and retrieval using Redis.

    This retriever enables:
    - Adding and storing vectorized documents in Redis.
    - Querying using semantic similarity search.
    - Filtering results based on metadata.
    - Deleting documents by ID or metadata.

    Use cases:
    - Fast, real-time document storage and retrieval.
    - Running high-speed similarity-based searches on structured text data.
    - Querying documents with both text and metadata constraints.
    """
    
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        self.brief = (
            f"RedisRetriever"
        )
        super().__init__(
            name="RedisRetriever",
            description=(
                "This retriever enables real-time document retrieval using Redis. "
                "Supports semantic search, metadata filtering, and high-speed vector-based querying. "
                "Ensure the Redis instance is correctly configured."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Add documents to Redis.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with keys `"text"` and optional `"metadata"`.

    - `query`: Perform similarity-based search.
      - Parameters:
        - `query` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `delete`: Remove documents from Redis by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to remove.

- **Usage format**:
```
execute_retriever:name|action|{"query": "Example text"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve documents related to a query:
```
execute_retriever:redis_retriever|query|{"query": "Real-time AI applications"}
```
        """
        )
        if Redis:
            self.db = Redis(index_name=kwargs["index_name"], redis_url=kwargs["redis_url"])
        else:
            raise ValueError("Redis package is not installed.")

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
        texts = [doc["text"] for doc in documents]
        metadata = [doc.get("metadata", {}) for doc in documents]
        self.db.add_texts(texts, metadatas=metadata)

    def add_documents_with_metadata(self, documents, metadata):
        self.db.add_texts(documents, metadatas=metadata)

    def query(self, query: str, filters: Dict = None, top_k: int = 5):
        """
        Perform a similarity-based search with optional metadata filtering.

        Args:
            query (str): The query string for retrieval.
            filters (Dict, optional): Metadata filters.
            top_k (int): Number of results to return (default: 5).

        Returns:
            List[Dict]: A list of standardized document results.
        """
        translated_filters = self.translate_filters(filters) if filters else None
        results = self.db.similarity_search(query, filter=translated_filters, k=top_k)

        return [
            self.standardize_output(
                text=item["value"]["value"],
                source="Redis",
                metadata=item["value"]["metadata"],
                id=item["key"],
            )
            for item in results
        ]

    def translate_filters(self, filters: Dict):
        """
        Convert standardized filters into Redis' filtering format.

        Args:
            filters (Dict): Standardized filter structure.

        Returns:
            Dict: Redis-compatible filter query.
        """
        redis_filters = []
        for condition in filters.get("conditions", []):
            field, operator, value = condition["field"], condition["operator"], condition["value"]

            if operator == "==":
                redis_filters.append(f"@{field}:({value})")
            elif operator == "!=":
                redis_filters.append(f"-@{field}:({value})")
            elif operator in [">=", "<="]:
                redis_filters.append(f"@{field}:[{value} {operator}]")

        return " ".join(redis_filters) if redis_filters else None

    def delete(self, document_ids):
        for doc_id in document_ids:
            self.db.delete(doc_id)

    def delete_by_metadata(self, metadata_query):
        self.db.delete(filter=metadata_query)


class ChromaAdapter(DatabaseAdapter):
    """
    A retriever for managing document storage and retrieval using ChromaDB.

    This retriever enables:
    - Storing and retrieving vectorized documents efficiently.
    - Performing similarity-based searches on stored documents.
    - Filtering results based on metadata.
    - Deleting documents by ID or metadata.

    Use cases:
    - Storing knowledge bases for fast document retrieval.
    - Running high-accuracy similarity searches on structured text data.
    - Querying documents using embeddings and metadata constraints.
    """
    
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        self.brief = (
            f"ChromaRetriever"
        )
        super().__init__(
            name="ChromaRetriever",
            description=(
                "This retriever enables efficient document storage and retrieval using ChromaDB. "
                "Supports semantic search, metadata filtering, and high-speed vector-based querying. "
                "Ensure the ChromaDB instance is properly configured."
            ),
            instruction="""
- **Actions and Parameters**:
    - `add_documents`: Add documents to ChromaDB.
      - Parameters:
        - `documents` (List[Dict]): A list of dictionaries with keys `"text"` and optional `"metadata"`.

    - `query`: Perform similarity-based search.
      - Parameters:
        - `query` (str): The text query for retrieval.
        - `filters` (Dict, optional): Metadata filters for refining results.

    - `delete`: Remove documents from ChromaDB by ID.
      - Parameters:
        - `document_ids` (List[str]): A list of document IDs to remove.

- **Usage format**:
```
execute_retriever:name|action|{"query": "Example text"}
```
Replace `name`, `action`, and parameters as needed.

Example:
- To retrieve documents related to a query:
```
execute_retriever:chroma_retriever|query|{"query": "Machine learning concepts"}
```
        """
        )
        if Chroma:
            self.db = Chroma(
                collection_name=kwargs["collection_name"],
                embedding_function=kwargs["embedding_function"],
            )
        else:
            raise ValueError("Chroma package is not installed.")

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
        texts = [doc["text"] for doc in documents]
        metadata = [doc.get("metadata", {}) for doc in documents]
        self.db.add_texts(texts, metadatas=metadata)

    def query(self, query, filters=None, top_k=10):
        translated_filters = self.translate_filters(filters) if filters else None
        result = self.db.similarity_search(query, filter=translated_filters, k=top_k)
        
        return [
            self.standardize_output(
                text=item["text"],
                source="ChromaDB",
                metadata=item["metadata"],
                id=item["id"],
                relevance_score=item.get("score")
            )
            for item in result
        ]

    def delete(self, document_ids):
        for doc_id in document_ids:
            self.db.delete(doc_id)

    def delete_by_metadata(self, metadata_query):
        self.db.delete(filter=metadata_query)

    def translate_filters(self, filters: Dict):
        """
        Convert standardized filter format into ChromaDB’s filtering structure.
        """
        chroma_filters = {}
        for condition in filters.get("conditions", []):
            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]

            if operator == "==":
                chroma_filters[field] = {"$eq": value}
            elif operator == ">=":
                chroma_filters[field] = {"$gte": value}
            elif operator == "<=":
                chroma_filters[field] = {"$lte": value}

        return chroma_filters