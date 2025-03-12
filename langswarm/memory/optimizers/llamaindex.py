class LlamaIndexOptimizer(BaseOptimizer):
    def __init__(self, index):
        """
        Initialize with an existing LlamaIndex instance.
        Args:
            index: The LlamaIndex instance to use.
        """
        self.index = index

    def summarize(self, documents):
        """
        Summarize documents using LlamaIndex's query engine.
        Args:
            documents: List of text documents to summarize.
        Returns:
            List of summaries.
        """
        summaries = []
        for doc in documents:
            response = self.index.query(doc, response_mode="summarize")
            summaries.append(response.response)  # Assume response object contains 'response' as text
        return summaries

    def rerank(self, query, documents):
        """
        Rerank documents using LlamaIndex's reranking method.
        Args:
            query: The query to rank against.
            documents: List of documents to rank.
        Returns:
            Ranked list of documents.
        """
        response = self.index.query(query, documents=documents, response_mode="ranking")
        return response.ranked_results

    def expand_query(self, query):
        """
        Expand a query to improve retrieval using LlamaIndex's capabilities.
        Args:
            query: The original query string.
        Returns:
            Expanded query string.
        """
        response = self.index.query(
            f"Expand the query to improve search accuracy: {query}", response_mode="default"
        )
        return response.response  # Assume response object contains 'response' as text
