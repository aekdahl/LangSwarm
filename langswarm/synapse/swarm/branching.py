from .swarm import Swarm

class LLMBranching(Swarm):
    """
    A subclass of Swarm that enables branching workflows for multiple LLMs.

    This class requires:
    - A list of initialized LLM clients (`clients`) provided during instantiation.
    - A non-empty query string (`query`) for generating responses.

    Attributes:
        clients (list): List of LLM instances for branching workflows.
        query (str): Query string to guide LLM responses.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize LLMBranching with required attributes and validate inputs.

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

    def run(self):
        """
        Execute the branching workflow among LLM clients.

        Returns:
            list: List of paragraphs generated by LLM clients.
        """
        if self.instantiate():
            if self.verbose:
                print("Class Instantiated.")

        return self.paragraphs
