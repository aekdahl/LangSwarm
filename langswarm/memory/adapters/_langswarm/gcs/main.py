from typing import Dict  # For typing annotations
from langswarm.memory.adapters.database_adapter import DatabaseAdapter

try:
    from google.cloud import storage
except ImportError:
    storage = None

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
    
    - Usage format:

Replace `action` and parameters as needed.
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

Replace `action` and parameters as needed.
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
    
    def query(self, query: str, filters: Dict = None, top_k: int = 5):
        """
        Perform a search query with optional metadata filtering.

        Args:
            query (str): The search query.
            filters (Dict, optional): Metadata filters for refining results.
            top_k (int): Number of results to return (default: 5).

        Returns:
            List[Dict]: A list of standardized document results.
        """
        blobs = list(self.client.list_blobs(self.bucket, prefix=self.prefix))
        results = []

        for blob in blobs:
            try:
                entry = eval(blob.download_as_text())
                if query.lower() in entry["value"].lower():
                    if filters and not self.match_filters(entry["metadata"], filters):
                        continue
                    results.append({"key": blob.name[len(self.prefix):], **entry})
            except Exception as e:
                print(f"Error processing blob {blob.name}: {e}")
        
        sorted_results = sorted(results, key=lambda x: x.get("relevance_score", 1.0), reverse=True)[:top_k]

        return [
            self.standardize_output(
                text=result["value"],
                source="GCS",
                metadata=result["metadata"],
                id=result["key"]
            ) for result in sorted_results
        ]

    def match_filters(self, metadata: Dict, filters: Dict):
        """
        Check if metadata matches the provided filters.

        Args:
            metadata (Dict): The metadata to check.
            filters (Dict): The filter conditions.

        Returns:
            bool: True if metadata matches filters, False otherwise.
        """
        return all(metadata.get(k) == v for k, v in filters.items())

    def delete(self, document_ids):
        for doc_id in document_ids:
            blob = self.bucket.blob(f"{self.prefix}{doc_id}")
            if blob.exists():
                blob.delete()


