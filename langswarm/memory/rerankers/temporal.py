class TemporalRetriever:
    """
    Retrieve documents based on temporal constraints (e.g., by timestamps).
    """
    def __init__(self, retriever, timestamp_field):
        """
        Args:
            retriever (object): Base retriever (e.g., dense, sparse).
            timestamp_field (str): Field containing document timestamps.
        """
        self.retriever = retriever
        self.timestamp_field = timestamp_field

    def query(self, query, start_time=None, end_time=None):
        """
        Retrieve documents within a temporal range.

        Args:
            query (str): Query string.
            start_time (str): Start time in ISO 8601 format.
            end_time (str): End time in ISO 8601 format.

        Returns:
            list: Retrieved documents matching the temporal range.
        """
        all_results = self.retriever.query(query)
        filtered_results = [
            doc for doc in all_results
            if self._is_within_range(doc[self.timestamp_field], start_time, end_time)
        ]
        return filtered_results

    def _is_within_range(self, timestamp, start_time, end_time):
        """Helper function to check if a timestamp is within a given range."""
        if start_time and timestamp < start_time:
            return False
        if end_time and timestamp > end_time:
            return False
        return True
