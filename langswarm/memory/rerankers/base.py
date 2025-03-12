class BaseReranker:
    """
    A base class for all rerankers in LangSwarm.

    Methods:
        rerank(query: str, documents: list) -> list:
            Rerank the provided documents based on the query.
    """
    def rerank(self, query, documents):
        raise NotImplementedError("Subclasses must implement the `rerank` method.")
