from typing import Dict  # For typing annotations
from langswarm.memory.adapters.database_adapter import DatabaseAdapter

try:
    from elasticsearch import Elasticsearch
except ImportError:
    storage = None

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
    
    - Usage format:

Replace `action` and parameters as needed.
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

Replace `action` and parameters as needed.
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

    def query(self, query: str, filters: Dict = None, top_k: int = 5):
        """
        Perform a search query with optional metadata filtering.

        Args:
            query (str): The text query for full-text search.
            filters (Dict, optional): Metadata-based filtering criteria.
            top_k (int): Number of results to return (default: 5).

        Returns:
            List[Dict]: A list of standardized document results.
        """
        body = {
            "query": {
                "bool": {
                    "must": [{"match": {"text": query}}],
                    "filter": self.build_filter_query(filters) if filters else []
                }
            },
            "size": top_k
        }

        try:
            response = self.db.search(index=self.index_name, body=body)
            results = response.get("hits", {}).get("hits", [])

            return [
                self.standardize_output(
                    text=result["_source"]["text"],
                    source="Elasticsearch",
                    metadata={k: v for k, v in result["_source"].items() if k != "text"},
                    id=result["_id"],
                    relevance_score=result["_score"]
                ) for result in results
            ]
        except Exception as e:
            print(f"Error during Elasticsearch query: {e}")
            return []

    def build_filter_query(self, filters: Dict):
        """
        Construct an Elasticsearch filter query from a dictionary of filters.

        Args:
            filters (Dict): Dictionary of metadata filters.

        Returns:
            List[Dict]: List of Elasticsearch filter queries.
        """
        return [{"term": {k: v}} for k, v in filters.items()]

    def delete(self, document_ids):
        for doc_id in document_ids:
            self.db.delete(index="documents", id=doc_id)

    def delete_by_metadata(self, metadata_query):
        body = {"query": {"bool": {"filter": [{"term": metadata_query}]}}}
        self.db.delete_by_query(index="documents", body=body)
