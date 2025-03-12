class FederatedRetriever:
    """
    Retrieve documents from multiple retrievers (federated search).
    """
    def __init__(self, retrievers):
        """
        Args:
            retrievers (list): List of retrievers to federate.
        """
        self.retrievers = retrievers

    def query(self, query):
        """
        Federate queries across all retrievers.

        Args:
            query (str): Query string.

        Returns:
            list: Combined results from all retrievers.
        """
        results = []
        for retriever in self.retrievers:
            results.extend(retriever.query(query))
        return self._deduplicate_results(results)

    def _deduplicate_results(self, results):
        """Remove duplicates based on document IDs."""
        seen = set()
        deduplicated = []
        for result in results:
            doc_id = result.get("id")
            if doc_id not in seen:
                seen.add(doc_id)
                deduplicated.append(result)
        return deduplicated
