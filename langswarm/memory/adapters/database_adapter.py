from abc import ABC, abstractmethod
from typing import Dict, List, Any

# ToDo: Make sure all implementations of DatabaseAdapter.query accepts a k=n parameter.

class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.

    Defines the interface that all database adapters must implement.
    """
    
    def __init__(self, name, description, instruction):
        self.name = name
        self.description = description
        self.instruction = instruction

    def use(self, *args, **kwargs):
        """Redirects to the `run` method for rag."""
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """Override this method to execute the rag."""
        raise NotImplementedError("This method should be implemented in a subclass.")

    @abstractmethod
    def add_documents(self, data):
        """
        Insert data into the database.

        Args:
            data (dict): The data to insert.

        Returns:
            bool: True if the operation was successful, False otherwise.

        Raises:
            ValueError: If data is invalid.
        """
        pass

    @abstractmethod
    def query(self, query, filters):
        """
        Query the database using the given filters.

        Args:
            filters (dict): A dictionary of query filters.

        Returns:
            list: A list of results matching the filters.

        Raises:
            ValueError: If filters are invalid.
        """
        pass

    @abstractmethod
    def delete(self, identifier):
        """
        Delete a record from the database.

        Args:
            identifier (str): The unique identifier of the record to delete.

        Returns:
            bool: True if the operation was successful, False otherwise.

        Raises:
            KeyError: If the identifier does not exist.
        """
        pass

    @abstractmethod
    def capabilities(self) -> Dict[str, bool]:
        raise NotImplementedError
        
    def translate_filters(self, filters: Dict) -> Any:
        """
        Convert standardized filters into the adapter-specific format.
        
        Args:
            filters (Dict): Standardized filter structure.
        
        Returns:
            Adapter-specific filtering format.
        """
        raise NotImplementedError("Subclasses must implement `translate_filters`")

    # Adding get_relevant_documents() for LangChain integration
    def get_relevant_documents(self, query: str, k: int = 5, filters: Dict = None) -> List[Dict]:
        """
        Retrieve the most relevant documents using the query() method.

        Args:
            query (str): The query string for retrieval.
            k (int): The number of documents to retrieve (default is 5).
            filters (Dict): Additional filters for querying metadata (optional).

        Returns:
            List[Dict]: A list of relevant documents.
        """
        # Query the database and limit results to k
        results = self.query(query, filters=filters, k=k)
        return results
    
    def _has_stored_files(self, query):
        """Check if the vector database contains any stored files."""
        return bool(self.query(query, k=1))

    def standardize_output(self, text, source, metadata=None, id=None, relevance_score=None):
        return {
            "text": text,
            "metadata": metadata or [],
            "source": source,
            "id": id
        }
