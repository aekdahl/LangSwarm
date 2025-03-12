from abc import ABC, abstractmethod

class BaseOptimizer(ABC):
    @abstractmethod
    def summarize(self, documents):
        """
        Summarize a list of documents.
        Args:
            documents: List of text documents to summarize.
        Returns:
            List of summaries.
        """
        pass

    @abstractmethod
    def rerank(self, query, documents):
        """
        Rerank documents based on the query.
        Args:
            query: The query to rank against.
            documents: List of documents to rank.
        Returns:
            Ranked list of documents.
        """
        pass

    @abstractmethod
    def expand_query(self, query):
        """
        Expand a query to improve retrieval.
        Args:
            query: The original query string.
        Returns:
            Expanded query string.
        """
        pass
