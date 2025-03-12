from memory.retrievers.temporal_federated import TemporalRetriever, FederatedRetriever

class TemporalFederatedWorkflow:
    """
    Workflow combining temporal and federated retrieval.
    """

    def __init__(self, dense_config, sparse_config, timestamp_field, retriever_configs):
        """
        Initialize the workflow.

        Args:
            dense_config (dict): Configuration for dense retriever.
            sparse_config (dict): Configuration for sparse retriever.
            timestamp_field (str): Field with timestamps.
            retriever_configs (list): List of federated retriever configs.
        """
        # Initialize temporal retrievers
        self.dense_retriever = TemporalRetriever(**dense_config, timestamp_field=timestamp_field)
        self.sparse_retriever = TemporalRetriever(**sparse_config, timestamp_field=timestamp_field)

        # Initialize federated retriever
        retrievers = [config["retriever"](**config["params"]) for config in retriever_configs]
        self.federated_retriever = FederatedRetriever(retrievers)

    def run(self, query, start_time=None, end_time=None):
        """
        Execute temporal and federated retrieval.

        Args:
            query (str): User query.
            start_time (str): Start time.
            end_time (str): End time.

        Returns:
            list: Retrieved documents.
        """
        # Perform temporal retrieval
        dense_results = self.dense_retriever.query(query, start_time, end_time)
        sparse_results = self.sparse_retriever.query(query, start_time, end_time)

        # Combine temporal results
        temporal_results = dense_results + sparse_results

        # Perform federated retrieval
        federated_results = self.federated_retriever.query(query)

        # Merge all results
        return temporal_results + federated_results
