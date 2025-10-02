from typing import Dict  # For typing annotations
from langswarm.memory.adapters.database_adapter import DatabaseAdapter

try:
    import redis
except ImportError:
    redis = None

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
    
    - Usage format:

Replace `action` and parameters as needed.
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

Replace `action` and parameters as needed.
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
            self.client.delete(doc_id)
