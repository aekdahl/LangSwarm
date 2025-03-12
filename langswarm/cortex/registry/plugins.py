import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


class PluginRegistry:
    """
    A registry for managing agent-specific plugins with semantic search support.
    Stores plugins in a dictionary and uses embeddings for similarity-based queries.
    """

    def __init__(self, embedding_model=None):
        """
        Initialize the PluginRegistry.

        :param embedding_model: A callable that generates embeddings for a given text.
                                Defaults to SentenceTransformer's 'all-MiniLM-L6-v2'.
        """
        self.embedding_model = embedding_model or SentenceTransformer('all-MiniLM-L6-v2').encode
        self.plugins = {}
        self.embeddings = {}

    def register_plugin(self, plugin):
        """
        Register a new plugin and generate its embedding.

        :param plugin_name: Name of the plugin to register.
        :param plugin: A callable object or function representing the plugin. 
                           It must have a `description` attribute.
        :raises ValueError: If the plugin is already registered or lacks a description.
        """
        plugin_name = plugin.identifier
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' is already registered.")
        if not hasattr(plugin, "description"):
            raise ValueError(f"Plugin '{plugin_name}' must have a 'description' attribute.")
        
        self.plugins[plugin_name] = plugin
        self.embeddings[plugin_name] = self.embedding_model(plugin.description)

    def get_plugin(self, plugin_name: str):
        """
        Retrieve a plugin by its name.

        :param plugin_name: Name of the plugin to retrieve.
        :return: The registered plugin if found, otherwise None.
        """
        return self.plugins.get(plugin_name)
    
    def count_plugins(self):
        """
        Count all registered plugins.

        :return: A count of plugins.
        """
        return len(self.plugins)

    def list_plugins(self):
        """
        List all registered plugins.

        :return: A list of plugin names and briefs.
        """
        return [f"{k} - {v.brief}" for k, v in self.plugins.items()]

    def remove_plugin(self, plugin_name: str):
        """
        Remove a plugin by its name.

        :param plugin_name: Name of the plugin to remove.
        :raises ValueError: If the plugin does not exist.
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' is not registered.")
        del self.plugins[plugin_name]
        del self.embeddings[plugin_name]

    def search_plugins(self, query: str, top_k: int = 5):
        """
        Search for plugins using semantic similarity based on their descriptions.

        :param query: A string to match against plugin descriptions.
        :param top_k: Number of top results to return.
        :return: A list of matching plugins, sorted by similarity score.
        """
        # Check if query is a single word and exists in rags
        if query.isalnum() and query in self.plugins:
            plugin = self.plugins.get(query)
            if plugin:
                return [{"name": query, "description": plugin.description, "instruction": plugin.instruction}]

        query_embedding = self.embedding_model(query)
        plugin_names = list(self.embeddings.keys())
        plugin_embeddings = np.array([self.embeddings[name] for name in plugin_names])

        # Compute cosine similarity
        similarities = cosine_similarity([query_embedding], plugin_embeddings)[0]
        ranked_indices = np.argsort(similarities)[::-1][:top_k]

        return [
            {
                "name": plugin_names[i],
                "description": self.plugins[plugin_names[i]].description,
                "instruction": self.plugins[plugin_names[i]].instruction,
                #"score": similarities[i],
            }
            for i in ranked_indices
        ]
