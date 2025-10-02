from typing import Dict  # For typing annotations
from langswarm.memory.adapters.database_adapter import DatabaseAdapter

try:
    from chromadb import Client as ChromaDB
    from chromadb.config import Settings
    from chromadb import HttpClient as ChromaHttp
    from chromadb import AsyncHttpClient as ChromaAsync
except ImportError:
    ChromaDB = None

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
    
    - Usage format:

Replace `action` and parameters as needed.
    """
    
    def __init__(self, identifier, collection_name="shared_memory", persist_directory=None, brief=None, host=None, port=8000):
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

Replace `action` and parameters as needed.
            """
        )
        if ChromaDB is None:
            raise ValueError("Unsupported database. Make sure ChromaDB is installed.")
        if persist_directory:
            self.client = ChromaDB(Settings(persist_directory=persist_directory))
        elif host:
            self.client = ChromaHttp(host=host, port=port)
        else:
            self.client = ChromaDB(Settings())
            
        # ToDo: Add abilit to set distance metric.
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
            self.collection.delete(ids=[doc_id])

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