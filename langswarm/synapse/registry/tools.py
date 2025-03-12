import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer


class ToolRegistry:
    """
    A registry for managing agent-specific tools with semantic search support.
    Stores tools in a dictionary and uses embeddings for similarity-based queries.
    """

    def __init__(self, embedding_model=None):
        """
        Initialize the ToolRegistry.

        :param embedding_model: A callable that generates embeddings for a given text.
                                Defaults to SentenceTransformer's 'all-MiniLM-L6-v2'.
        """
        self.embedding_model = embedding_model or SentenceTransformer('all-MiniLM-L6-v2').encode
        self.tools = {}
        self.embeddings = {}

    def register_tool(self, tool):
        """
        Register a new tool and generate its embedding.

        :param tool_name: Name of the tool to register.
        :param tool: A callable object or function representing the tool. 
                           It must have a `description` attribute.
        :raises ValueError: If the tool is already registered or lacks a description.
        """
        tool_name = tool.identifier
        if tool_name in self.tools:
            raise ValueError(f"Tool '{tool_name}' is already registered.")
        if not hasattr(tool, "description"):
            raise ValueError(f"Tool '{tool_name}' must have a 'description' attribute.")
        
        self.tools[tool_name] = tool
        self.embeddings[tool_name] = self.embedding_model(tool.description)

    def get_tool(self, tool_name: str):
        """
        Retrieve a tool by its name.

        :param tool_name: Name of the tool to retrieve.
        :return: The registered tool if found, otherwise None.
        """
        return self.tools.get(tool_name)

    def count_tools(self):
        """
        Count all registered tools.

        :return: A count of tools.
        """
        return len(self.tools)

    def list_tools(self):
        """
        List all registered tools.

        :return: A list of tool names and briefs.
        """
        return [f"{k} - {v.brief}" for k, v in self.tools.items()]

    def remove_tool(self, tool_name: str):
        """
        Remove a tool by its name.

        :param tool_name: Name of the tool to remove.
        :raises ValueError: If the tool does not exist.
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' is not registered.")
        del self.tools[tool_name]
        del self.embeddings[tool_name]

    def search_tools(self, query: str, top_k: int = 5):
        """
        Search for tools using semantic similarity based on their descriptions.

        :param query: A string to match against tool descriptions.
        :param top_k: Number of top results to return.
        :return: A list of matching tools, sorted by similarity score.
        """
        # Check if query is a single word and exists in tools
        if query.isalnum() and query in self.tools:
            tool = self.tools.get(query)
            if tool:
                return [{"name": query, "description": tool.description, "instruction": tool.instruction}]

        query_embedding = self.embedding_model(query)
        tool_names = list(self.embeddings.keys())
        tool_embeddings = np.array([self.embeddings[name] for name in tool_names])

        # Compute cosine similarity
        similarities = cosine_similarity([query_embedding], tool_embeddings)[0]
        ranked_indices = np.argsort(similarities)[::-1][:top_k]

        return [
            {
                "name": tool_names[i],
                "description": self.tools[tool_names[i]].description,
                "instruction": self.tools[tool_names[i]].instruction,
                #"score": similarities[i],
            }
            for i in ranked_indices
        ]
