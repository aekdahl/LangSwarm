
class EmbeddingModelRegistry:
    """Global registry for managing embedding models."""

    _instance = None  # Singleton instance
    _registry = {}  # Stores user-defined embedding models
    _default_model_name = "all-MiniLM-L6-v2"  # Default model

    PREDEFINED_MODELS = {
        "all-MiniLM-L6-v2": "Compact, efficient model for general-purpose text embeddings.",
        "multi-qa-mpnet-base-dot-v1": "Optimized for QA retrieval tasks.",
        "all-mpnet-base-v2": "Larger model for more accurate sentence embeddings.",
    }

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(EmbeddingModelRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name, model):
        """Register a new embedding model."""
        if name in cls._registry:
            raise ValueError(f"Model '{name}' is already registered.")
        cls._registry[name] = model

    @classmethod
    def get_model(cls, name=None):
        """Retrieve an explicitly registered embedding model."""
        if name is None:
            name = cls._default_model_name
        if name in cls._registry:
            return cls._registry[name]
        raise ValueError(
            f"Model '{name}' is not registered. Available models: {list(cls._registry.keys())}.\n"
            f"Please register it using `EmbeddingModelRegistry.register(name, model_instance)`."
        )

    @classmethod
    def list_registered(cls):
        """List all user-registered models."""
        return list(cls._registry.keys())

    @classmethod
    def list_predefined(cls):
        """List all predefined models (must be registered before use)."""
        return cls.PREDEFINED_MODELS
