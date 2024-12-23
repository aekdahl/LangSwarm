from .swarm import Swarm

class LLMAggregation(Swarm):
    """
    A subclass of Swarm that focuses on aggregating outputs from multiple LLMs.

    This class requires:
    - A list of initialized LLM clients (`clients`) provided during instantiation.
    - A non-empty query string (`query`) for generating responses.

    Attributes:
        clients (list): List of LLM instances for aggregation.
        query (str): Query string to guide LLM responses.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize LLMAggregation with required attributes and validate inputs.

        Raises:
            ValueError: If `clients` is not set or `query` is empty.
        """
        super().__init__(*args, **kwargs)
        if len(self.clients) < 1:
            raise ValueError('Requires clients to be set as a list of LLMs at init.')
        if not self.query:
            raise ValueError('Requires query to be set as a string at init.')
        
    def generate_paragraphs(self):
        """
        Generate response paragraphs for the given query from all LLM clients.

        Returns:
            int: Number of clients that generated paragraphs.
        """
        for client in self.clients:
            self._create_paragraphs(client, erase_query=True)
        return len(self.clients)

    def instantiate(self):
        """
        Validate initialization and generate paragraphs.

        Returns:
            bool: True if successful, False otherwise.
        """
        if self.check_initialization():
            if self.verbose:
                print("\nInitialization successful.")

            created_clients = self.generate_paragraphs()

            if self.verbose:
                print("\nClients created:", created_clients)

            return True

        return False

    def aggregate_list(self, paragraphs, hb):
        """
        Merge and aggregate data into a deduplicated list.

        Args:
            paragraphs (list): List of paragraphs generated by LLM clients.
            hb: Helper bot instance for performing the aggregation task.

        Returns:
            str: Aggregated list as a single string.
        """
        query = f"""
        Merge and aggregate the data into a list.

        Data:
        ---
        {paragraphs}
        ---
        """
        return hb.aggregator_bot.chat(q=query, reset=True, erase_query=True)

    def run(self, hb):
        """
        Execute the aggregation workflow among LLM clients.

        Args:
            hb: Helper bot instance for performing the aggregation task.

        Returns:
            str: The aggregated paragraph or a message indicating failure.
        """
        aggregated_paragraph = 'No aggregation done.'

        if self.instantiate():
            if self.verbose:
                print("Class Instantiated.")

            # Aggregate the list of generated paragraphs
            aggregated_paragraph = self.aggregate_list(self.paragraphs, hb)

            if self.verbose:
                print("Aggregated list:", aggregated_paragraph)

        return aggregated_paragraph
