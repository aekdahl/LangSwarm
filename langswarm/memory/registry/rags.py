
class RAGRegistry:
    """
    A registry for managing agent-specific rags.
    """

    def __init__(self):
        """
        Initialize the RAGRegistry.
        """
        self.rags = {}

    def register_rag(self, rag):
        """
        Register a new rag.

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
