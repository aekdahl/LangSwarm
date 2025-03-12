from .swarm import Swarm

class LLMConsensus(Swarm):
    """
    A subclass of Swarm that facilitates consensus generation among multiple LLMs.

    This class requires:
    - A list of initialized LLM clients (`clients`) provided during instantiation.
    - A non-empty query string (`query`) for generating responses.

    Attributes:
        clients (list): List of LLM instances for consensus generation.
        query (str): Query string to guide LLM responses.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize LLMConsensus with required attributes and validate inputs.

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

    def create_embeddings(self, paragraphs):
        """
        Generate embeddings for the given paragraphs.

        Args:
            paragraphs (list): List of response paragraphs.

        Returns:
            tuple: Original paragraphs and their embeddings.
        """
        paragraph_embeddings = self.model.encode(paragraphs)
        return paragraphs, paragraph_embeddings

    def run(self):
        """
        Execute the consensus workflow among LLM clients.

        Returns:
            str: The consensus paragraph or a message indicating failure.
        """
        consensus_paragraph = 'No consensus found.'

        if self.instantiate():
            if self.verbose:
                print("Class instantiated.")

            # Calculate global average similarity among all responses
            global_average_similarity = self.calculate_global_similarity(self.paragraphs, self.paragraphs)

            if self.verbose:
                print("Global Average Similarity:", global_average_similarity)

            # Adjust similarity thresholds dynamically
            dynamic_threshold = self.dynamic_threshold(global_average_similarity, self.threshold, adjustment_factor=0.8)

            if self.verbose:
                print("Dynamic Threshold:", dynamic_threshold)

            dynamic_paraphrase_threshold = self.dynamic_threshold(global_average_similarity, self.paraphrase_threshold, adjustment_factor=0.8)

            if self.verbose:
                print("Dynamic Paraphrase Threshold:", dynamic_paraphrase_threshold)

            # Generate embeddings for paragraphs
            paragraphs, paragraph_embeddings = self.create_embeddings(self.paragraphs)

            if self.verbose:
                print("Created embeddings.")

            # Detect paraphrase groups based on similarity
            paraphrase_groups = self.detect_paraphrases(paragraphs, paragraph_embeddings, dynamic_paraphrase_threshold)

            # Determine consensus from paraphrase groups
            consensus_paragraph, highest_similarity, group_size_of_best = self.get_consensus(
                paraphrase_groups, paragraphs, paragraph_embeddings
            )

            if self.verbose:
                print("\nParagraphs:", self.paragraphs)
                print("\nHighest Similarity:", highest_similarity)
                print("\nConsensus Paragraph:", consensus_paragraph)
                print("\nConsensus Group Size:", group_size_of_best)

        return consensus_paragraph
