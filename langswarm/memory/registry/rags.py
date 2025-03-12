import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


class RAGRegistry:
    """
    A registry for managing agent-specific rags with semantic search support.
    Stores rags in a dictionary and uses embeddings for similarity-based queries.
    """

    def __init__(self, embedding_model=None):
        """
        Initialize the RAGRegistry.

        :param embedding_model: A callable that generates embeddings for a given text.
                                Defaults to SentenceTransformer's 'all-MiniLM-L6-v2'.
        """
        self.embedding_model = embedding_model or SentenceTransformer('all-MiniLM-L6-v2').encode
        self.rags = {}
        self.embeddings = {}

    def register_rag(self, rag):
        """
        Register a new rag and generate its embedding.

        :param rag_name: Name of the rag to register.
        :param rag: A callable object or function representing the rag. 
                           It must have a `description` attribute.
        :raises ValueError: If the rag is already registered or lacks a description.
        """
        rag_name = rag.identifier
        if rag_name in self.rags:
            raise ValueError(f"RAG '{rag_name}' is already registered.")
        if not hasattr(rag, "description"):
            raise ValueError(f"RAG '{rag_name}' must have a 'description' attribute.")
        
        self.rags[rag_name] = rag
        self.embeddings[rag_name] = self.embedding_model(rag.description)

    def get_rag(self, rag_name: str):
        """
        Retrieve a rag by its name.

        :param rag_name: Name of the rag to retrieve.
        :return: The registered rag if found, otherwise None.
        """
        return self.rags.get(rag_name)
    
    def count_rags(self):
        """
        Count all registered rags.

        :return: A count of rags.
        """
        return len(self.rags)

    def list_rags(self):
        """
        List all registered rags.

        :return: A list of rag names and briefs.
        """
        return [f"{k} - {v.brief}" for k, v in self.rags.items()]

    def remove_rag(self, rag_name: str):
        """
        Remove a rag by its name.

        :param rag_name: Name of the rag to remove.
        :raises ValueError: If the rag does not exist.
        """
        if rag_name not in self.rags:
            raise ValueError(f"RAG '{rag_name}' is not registered.")
        del self.rags[rag_name]
        del self.embeddings[rag_name]

    def search_rags(self, query: str, top_k: int = 5):
        """
        Search for rags using semantic similarity based on their descriptions.

        :param query: A string to match against rag descriptions.
        :param top_k: Number of top results to return.
        :return: A list of matching rags, sorted by similarity score.
        """
        # Check if query is a single word and exists in rags
        if query.isalnum() and query in self.rags:
            rag = self.rags.get(query)
            if rag:
                return [{"name": query, "description": rag.description, "instruction": rag.instruction}]

        query_embedding = self.embedding_model(query)
        rag_names = list(self.embeddings.keys())
        rag_embeddings = np.array([self.embeddings[name] for name in rag_names])

        # Compute cosine similarity
        similarities = cosine_similarity([query_embedding], rag_embeddings)[0]
        ranked_indices = np.argsort(similarities)[::-1][:top_k]

        return [
            {
                "name": rag_names[i],
                "description": self.rags[rag_names[i]].description,
                "instruction": self.rags[rag_names[i]].instruction,
                #"score": similarities[i],
            }
            for i in ranked_indices
        ]
