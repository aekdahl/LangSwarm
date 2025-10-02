from typing import List, Dict  # For typing annotations
from langswarm.memory.adapters.database_adapter import DatabaseAdapter

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, Filter, FieldCondition, Range
    from langchain.embeddings import OpenAIEmbeddings
except ImportError:
    QdrantClient = None

class QdrantAdapter(DatabaseAdapter):
    """
    Adapter for integrating Qdrant as a vector database.
    Supports adding, querying, and deleting documents with metadata filtering.
    
    Args:
        host (str): Qdrant server URL.
        port (int): Qdrant server port.
        collection_name (str): Name of the Qdrant collection.
        embedding_function (Callable): Embedding function for document vectorization.
    """
    
    def __init__(self, identifier, *args, **kwargs):
        self.identifier = identifier
        self.brief = (
            f"QdrantRetriever"
        )
        super().__init__(
            name="QdrantRetriever",
            description=(
                "This retriever allows querying and storing documents in Qdrant. "
                "It supports full-text search, metadata filtering, and vector search."
            ),
            instruction="""
- Actions and Parameters:
    - `add_documents`: Store documents in Qdrant.
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

Replace `action` and parameters as needed.
            """
        )
        
        if QdrantClient:
            self.client = QdrantClient(host=kwargs["host"], port=kwargs["port"])  
            self.collection_name = kwargs["collection"]
            self.embedding_function = OpenAIEmbeddings()
        else:
            raise ValueError("Qdrant package is not installed.")

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

    def add_documents(self, documents: List[Dict]):
        """
        Insert documents into Qdrant.
        
        Args:
            documents (List[Dict]): List of documents with 'text' and optional 'metadata'.

        Returns:
            bool: True if successful, False otherwise.
        """
        points = []
        for idx, doc in enumerate(documents):
            embedding = self.embedding_function.embed_query(doc["text"])
            metadata = doc.get("metadata", {})
            points.append(
                PointStruct(id=idx, vector=embedding, payload=metadata)
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        return True

    def query(self, query: str, filters: Dict = None, top_k: int = 5):
        """
        Retrieve relevant documents based on semantic similarity.
        
        Args:
            query (str): Search query text.
            filters (Dict): Metadata filters (optional).
            top_k (int): Number of results to retrieve.
        
        Returns:
            List[Dict]: Retrieved documents in a standardized format.
        """
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

    def delete(self, identifier: str):
        """
        Delete a record from Qdrant by its identifier.
        
        Args:
            identifier (str): Unique document ID.
        
        Returns:
            bool: True if deletion was successful.
        """
        self.client.delete(collection_name=self.collection_name, points_selector=[identifier])
        return True

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
