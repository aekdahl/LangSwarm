from typing import Any, Optional, List, Dict
from itertools import chain


class RAGMixin:
    def __init__(self):
        """
        Initialize the RAGMixin with empty retrievers.
        """
        self.retrievers = {}  # A dictionary mapping retriever names to (adapter, collection_name)

    def add_retriever(self, name: str, adapter, collection_name: str):
        """
        Add a retriever dynamically.
        :param name: Name of the retriever.
        :param adapter: DatabaseAdapter instance.
        :param collection_name: Name of the collection.
        """
        if name in self.retrievers:
            raise ValueError(f"Retriever with name '{name}' already exists.")
        self.retrievers[name] = (adapter, collection_name)

    def remove_retriever(self, name: str):
        """
        Remove a retriever by name.
        :param name: Name of the retriever to remove.
        """
        if name not in self.retrievers:
            raise ValueError(f"Retriever with name '{name}' does not exist.")
        del self.retrievers[name]

    def query_retrievers(self, query: str, use_all: bool = True, retriever_names: Optional[List[str]] = None) -> List[Dict]:
        """
        Perform a RAG query using the selected retrievers.
        :param query: Query string.
        :param use_all: Whether to query all retrievers (default is True).
        :param retriever_names: List of retriever names to use if use_all is False.
        :return: Aggregated results from all queried retrievers.
        """
        if not self.retrievers:
            raise ValueError("No retrievers available. Please add at least one retriever before querying.")

        results = []

        if use_all:
            retrievers_to_query = self.retrievers.values()
        else:
            if not retriever_names:
                raise ValueError("Retriever names must be provided when 'use_all' is False.")
            retrievers_to_query = [
                self.retrievers[name] for name in retriever_names if name in self.retrievers
            ]

        for adapter, collection_name in retrievers_to_query:
            # Ensure adapter supports querying
            if not hasattr(adapter, "query"):
                raise ValueError(f"The adapter for collection '{collection_name}' does not support querying.")
            results.extend([adapter.query(query)])

        return results

    def use_rag(self, query: str, use_all: bool = True, retriever_names: Optional[List[str]] = None) -> str:
        """
        Perform RAG and return the most relevant information as a response.
        :param query: Query string.
        :param use_all: Whether to query all retrievers (default is True).
        :param retriever_names: List of retriever names to use if use_all is False.
        :return: The aggregated RAG result.
        """
        # ToDo: OptimizerManager holds a query expander if needed
        
        retrieved_docs = self.query_retrievers(query, use_all, retriever_names)

        # Aggregate and rank results (simplified ranking here)
        # ToDo: Add Rerank to get the best result first
        # ToDo: OptimizerManager holds a Reranker if needed
        
        responses = [doc["text"] for doc in retrieved_docs]
        merged_list = list(chain.from_iterable(responses))
        aggregated_response = "\n".join(merged_list)
        
        # Truncate to fit context
        # ToDo: OptimizerManager holds a summarizer if needed
        return self.utils.truncate_text_to_tokens(
            aggregated_response, 
            self.model_details["limit"], 
            tokenizer_name=self.model_details.get("name", "gpt2"),
            current_conversation=self.share_conversation()
        )

    def use_rag_with_adapter(self, query: str, adapter, collection_name: str, metadata_filter=None) -> str:
        """
        Perform RAG using an ad-hoc adapter and collection name.

        :param query: Query string.
        :param adapter: DatabaseAdapter instance.
        :param collection_name: Name of the collection in the adapter.
        :param metadata_filter: Optional metadata filter for the query.
        :return: The aggregated RAG result.
        """
        if not hasattr(adapter, "query"):
            raise ValueError(f"The provided adapter does not support querying.")

        # Query the adapter directly
        results = adapter.query(query, filters=metadata_filter)

        # Normalize and aggregate results
        aggregated_response = "\n".join([
            f"{res.get('key', '')}: {res.get('text', '')}" for res in results
        ])
        
        # ToDo: Add Rerank to get the best result first
        
        # Truncate to fit context
        return self.utils.truncate_text_to_tokens(
            aggregated_response, 
            self.model_details["limit"], 
            tokenizer_name=self.model_details.get("name", "gpt2"),
            current_conversation=self.share_conversation()
        )