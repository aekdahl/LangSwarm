import functools

class MemoryManager:
    def __init__(self, backends=None, **kwargs):
        """
        Initialize MemoryManager with multiple backends.

        Args:
            backends (list): List of backend configurations. Each entry can specify
                            the backend type (e.g., "langchain", "llama_index") and
                            corresponding parameters.
        """
        self.adapters = []
        if backends:
            for backend in backends:
                if backend["type"] == "langchain":
                    self.adapters.append(LangChainAdapter(**backend.get("params", {})))
                elif backend["type"] == "llama_index":
                    self.adapters.append(LlamaIndexAdapter(**backend.get("params", {})))
                else:
                    raise ValueError(f"Unsupported backend: {backend['type']}")

    # ToDo: Now a document is written to all backends, do we want that?
    # ToDo: Add a parameter for which backends we want to write the document.
    def add_documents(self, documents):
        for adapter in self.adapters:
            adapter.add_documents(documents)

    def query(self, query, filters=None, sort_key=None, top_k=None):
        """
        Query all backends and aggregate results with deduplication and sorting.
    
        Args:
            query (str): Query string.
            filters (dict): Optional filters for querying.
            sort_key (str): Optional key for sorting results.
            top_k (int): Optional number of top results to return.
    
        Returns:
            list: Deduplicated and sorted query results.
        """
        results = []
        for adapter in self.adapters:
            results.extend(adapter.query(query, filters))
    
        # Deduplicate results by text (or other unique key)
        unique_results = {res["text"]: res for res in results}.values()
    
        # Sort results if a sort key is provided
        if sort_key:
            unique_results = sorted(unique_results, key=lambda x: x.get(sort_key), reverse=True)
    
        # Limit to top_k results if specified
        if top_k:
            unique_results = list(unique_results)[:top_k]
    
        return list(unique_results)


    def delete(self, document_ids):
        for adapter in self.adapters:
            adapter.delete(document_ids)



"""
The SharedMemoryManager will unify and orchestrate memory backends, enabling seamless integration with the LangSwarm ecosystem. Its primary role is to handle shared memory operations across multiple backends and provide a consistent interface for:

Centralized and Federated Memory: Supporting both centralized memory (e.g., for global indices) and federated memory (e.g., agent-specific memory).
Thread-Safe Operations: Ensuring safe concurrent access to shared memory.
Multi-Backend Orchestration: Allowing flexible switching and management of memory backends (e.g., FAISS, Pinecone, Elasticsearch).
"""
class SharedMemoryManager:
    def __init__(self, backend_configs, thread_safe=True):
        """
        Initializes the shared memory manager.

        Args:
            backend_configs (list): List of backend configurations. Each entry specifies the backend type 
                                    (e.g., "faiss", "pinecone") and its parameters.
            thread_safe (bool): Whether to make the manager thread-safe.
        """
        self.backends = self._initialize_backends(backend_configs)
        self.lock = threading.RLock() if thread_safe else None

    def _initialize_backends(self, backend_configs):
        """
        Initializes memory backends based on configurations.

        Args:
            backend_configs (list): List of configurations for each backend.

        Returns:
            list: List of initialized backend instances.
        """
        initialized_backends = []
        for config in backend_configs:
            if config["type"] == "faiss":
                initialized_backends.append(FaissAdapter(**config.get("params", {})))
            elif config["type"] == "pinecone":
                initialized_backends.append(PineconeAdapter(**config.get("params", {})))
            else:
                raise ValueError(f"Unsupported backend type: {config['type']}")
        return initialized_backends

    def _example_usage(self):
        """
        Example usage of the SharedMemoryManager.
        """
        backend_configs = [
            {"type": "faiss", "params": {"dimension": 128}},
            {"type": "pinecone", "params": {"api_key": "your-api-key", "environment": "us-west1"}}
        ]
        manager = SharedMemoryManager(backend_configs)
        documents = [{"text": "Document 1"}, {"text": "Document 2"}]
        manager.add_documents(documents)
        results = manager.query("query text")
        print("Results:", results)

    def _thread_safe(method):
        """Decorator to add thread-safety to methods if enabled."""
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'lock') and self.lock:  # Ensure instance has a lock attribute
                with self.lock:
                    return method(self, *args, **kwargs)
            return method(self, *args, **kwargs)
        return wrapper

    @_thread_safe
    def add_documents(self, documents):
        for backend in self.backends:
            backend.add_documents(documents)

    @_thread_safe
    def query(self, query_params, deduplicate=True, sort_key=None, sort_reverse=False):
        """
        Query shared memory segments for matching results.

        Args:
            query_params (dict): Parameters to filter the query.
            deduplicate (bool): Whether to deduplicate results. Default is True.
            sort_key (str): Key to sort results by (e.g., 'timestamp').
            sort_reverse (bool): Whether to reverse the sorting order. Default is False.

        Returns:
            list: A list of query results.
        """
        results = []
        
        # Aggregate results from all shared memory segments
        for segment in self._segments:
            results.extend(segment.query(query_params))

        # Deduplicate results if required
        if deduplicate:
            # Assuming each result is hashable (e.g., dictionaries with immutable keys/values)
            results = list({frozenset(item.items()): item for item in results}.values())

        # Sort results if a sort key is provided
        if sort_key:
            try:
                results.sort(key=lambda x: x.get(sort_key), reverse=sort_reverse)
            except KeyError:
                raise ValueError(f"Sort key '{sort_key}' not found in results.")

        return results

    @_thread_safe
    def delete(self, ids):
        for backend in self.backends:
            backend.delete(ids)

