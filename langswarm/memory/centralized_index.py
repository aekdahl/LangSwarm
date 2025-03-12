import importlib
from datetime import datetime, timedelta

try:
    from llama_index import GPTSimpleVectorIndex, Document
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    GPTSimpleVectorIndex = None
    Document = None
    LLAMA_INDEX_AVAILABLE = False


class CentralizedIndex:
    def __init__(self, index_path="memory_index.json", expiration_days=None):
        """
        Centralized index for long-term memory and shared knowledge.

        :param index_path: Path to store the index file.
        :param expiration_days: Number of days before memory fades (optional).
        """
        self.index_path = index_path
        self.expiration_days = expiration_days
        self._indexing_is_available = LLAMA_INDEX_AVAILABLE

        if not LLAMA_INDEX_AVAILABLE:
            self.index = None
            print("LlamaIndex is not installed. Memory indexing features are disabled.")
            return

        # Try to load an existing index or create a new one
        try:
            self.index = GPTSimpleVectorIndex.load_from_disk(index_path)
        except FileNotFoundError:
            self.index = GPTSimpleVectorIndex([])

    @property
    def indexing_is_available(self):
        """Check if indexing is available."""
        return self._indexing_is_available

    def _clean_expired_documents(self):
        """
        Internal method to clean up expired documents.
        """
        if not self.indexing_is_available or self.expiration_days is None:
            return
    
        now = datetime.now()
        valid_documents = []
        for doc in self.index.documents:
            timestamp = doc.extra_info.get("timestamp")
            if timestamp:
                doc_time = datetime.fromisoformat(timestamp)
                if (now - doc_time) <= timedelta(days=self.expiration_days):
                    valid_documents.append(doc)
    
        # Update the index with valid documents only
        self.index = GPTSimpleVectorIndex(valid_documents)
        self.index.save_to_disk(self.index_path)
    
    def _validate_and_normalize_metadata(self, metadata):
        """
        Validates and normalizes metadata.
    
        Args:
            metadata (dict): Metadata dictionary.
    
        Returns:
            dict: Normalized metadata with lowercase keys.
        """
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary.")
    
        return {str(key).lower(): value for key, value in metadata.items()}
    
    def add_documents(self, docs):
        """
        Add documents to the centralized index with metadata validation.
    
        :param docs: List of documents with text and optional metadata.
        """
        if not self.indexing_is_available:
            print("Indexing features are unavailable.")
            return
    
        self._clean_expired_documents()
    
        documents = [
            Document(text=doc["text"], metadata={
                **self._validate_and_normalize_metadata(doc.get("metadata", {})),
                "timestamp": datetime.now().isoformat()  # Add a timestamp to each document
            })
            for doc in docs
        ]
        self.index.insert(documents)
        self.index.save_to_disk(self.index_path)
    
    def query(self, query_text, metadata_filter=None):
        """
        Query the index with metadata validation and filtering.
    
        :param query_text: The text query.
        :param metadata_filter: Dictionary of metadata filters (optional).
        :return: Filtered results based on the query and metadata.
        """
        self._clean_expired_documents()
    
        if not self.indexing_is_available:
            print("Indexing features are unavailable.")
            return []
    
        results = self.index.query(query_text)
    
        # Apply metadata filtering if specified
        if metadata_filter:
            normalized_filter = self._validate_and_normalize_metadata(metadata_filter)
            results = [
                res for res in results
                if all(res.extra_info.get(key) == value for key, value in normalized_filter.items())
            ]
        return results


    def purge_expired_documents(self):
        """
        Remove documents from the index that have exceeded the expiration period.
        """
        self._clean_expired_documents()





class HybridCentralizedIndex:
    def __init__(self, adapters: List[Any] = None):
        self.adapters = adapters or []

    def add_adapter(self, adapter: Any):
        """Add a new adapter to the hybrid index."""
        self.adapters.append(adapter)

    def remove_adapter(self, adapter_name: str):
        """Remove an adapter by name."""
        self.adapters = [a for a in self.adapters if a.__class__.__name__ != adapter_name]

    def query(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Query all adapters that support the specified type."""
        query_type = kwargs.get("type", "default")
        results = []

        for adapter in self.adapters:
            capabilities = adapter.capabilities()
            if (query_type == "vector_search" and capabilities.get("vector_search")) or \
               (query_type == "metadata_filtering" and capabilities.get("metadata_filtering")) or \
               query_type == "default":
                try:
                    results.extend(adapter.query(query, **kwargs))
                except Exception as e:
                    print(f"Adapter {adapter.__class__.__name__} failed: {e}")

        return self._deduplicate_and_sort(results)

    def _deduplicate_and_sort(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate and sort results by score."""
        unique_results = {res["id"]: res for res in results}  # Deduplicate by ID
        return sorted(unique_results.values(), key=lambda x: x["score"], reverse=True)

"""
# Example Usage
if __name__ == "__main__":
    # Initialize existing adapters
    faiss_adapter = FAISSAdapter(index_path="path/to/faiss")
    es_adapter = ElasticsearchAdapter(host="localhost", port=9200)
    pinecone_adapter = PineconeAdapter(api_key="api_key", environment="us-west")

    # Initialize Hybrid Centralized Index
    hybrid_index = HybridCentralizedIndex([faiss_adapter, es_adapter, pinecone_adapter])

    # Query for vector search
    vector_results = hybrid_index.query("What is AI?", type="vector_search", top_k=5)
    print("Vector Search Results:", vector_results)

    # Query for metadata filtering
    metadata_results = hybrid_index.query("What is AI?", type="metadata_filtering", metadata={"tag": "AI"})
    print("Metadata Filtering Results:", metadata_results)
"""
