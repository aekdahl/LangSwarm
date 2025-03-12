import threading

class ThreadSafeAdapter:
    def __init__(self, adapter):
        """
        Wraps an existing adapter to make it thread-safe.

        Args:
            adapter: The adapter to wrap (e.g., FAISSBackend, PineconeBackend, etc.).
        """
        self.adapter = adapter
        self.lock = threading.RLock()

    def add_documents(self, documents):
        """
        Thread-safe method to add documents to the underlying adapter.

        Args:
            documents (list): List of documents to add.

        Raises:
            ValueError: If the input is not a list or documents lack required fields.
        """
        if not isinstance(documents, list):
            raise ValueError("Documents must be provided as a list.")
        for doc in documents:
            if not isinstance(doc, dict) or "text" not in doc:
                raise ValueError("Each document must be a dictionary with at least a 'text' key.")

        with self.lock:
            try:
                self.adapter.add_documents(documents)
            except Exception as e:
                raise RuntimeError(f"Failed to add documents: {e}")

    def query(self, query, top_k=5):
        """
        Thread-safe method to query the underlying adapter.

        Args:
            query (str): Query string.
            top_k (int): Number of top results to retrieve.

        Returns:
            list: Query results.

        Raises:
            ValueError: If query is not a string or top_k is not a positive integer.
            RuntimeError: If querying the adapter fails.
        """
        if not isinstance(query, str):
            raise ValueError("Query must be a string.")
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        with self.lock:
            try:
                return self.adapter.query(query, top_k)
            except Exception as e:
                raise RuntimeError(f"Failed to query adapter: {e}")

    def delete(self, ids):
        """
        Thread-safe method to delete documents from the underlying adapter.

        Args:
            ids (list): List of document IDs to delete.

        Raises:
            ValueError: If ids is not a list or is empty.
            RuntimeError: If deletion fails.
        """
        if not isinstance(ids, list) or not ids:
            raise ValueError("IDs must be provided as a non-empty list.")

        with self.lock:
            try:
                self.adapter.delete(ids)
            except Exception as e:
                raise RuntimeError(f"Failed to delete documents: {e}")

    def __getattr__(self, attr):
        """
        Delegate any other methods or attributes to the underlying adapter.

        This allows access to other methods (if needed) without redefining them.

        Args:
            attr (str): Attribute name.

        Returns:
            Any: The corresponding attribute from the adapter.

        Raises:
            AttributeError: If the attribute does not exist in the adapter.
        """
        try:
            return getattr(self.adapter, attr)
        except AttributeError as e:
            raise AttributeError(f"Attribute '{attr}' not found in the underlying adapter: {e}")
