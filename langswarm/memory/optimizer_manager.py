.optimizers.langchain import LangChainOptimizer
.optimizers.llamaindex import LlamaIndexOptimizer

class OptimizerManager:
    def __init__(self, backend, agent_or_index):
        """
        Initialize the optimizer manager with a specific backend.
        Args:
            backend: 'langchain' or 'llamaindex'.
            agent_or_index: LangChain agent or LlamaIndex instance.
        """
        self.backend = backend
        if backend == "langchain":
            self.optimizer = LangChainOptimizer(agent_or_index)
        elif backend == "llamaindex":
            self.optimizer = LlamaIndexOptimizer(agent_or_index)
        else:
            raise ValueError("Invalid backend. Choose 'langchain' or 'llamaindex'.")

    def summarize(self, documents):
        """
        Summarize documents using the selected backend.
        Args:
            documents: List of text documents to summarize.
        Returns:
            List of summaries.
        """
        return self.optimizer.summarize(documents)

    def rerank(self, query, documents):
        """
        Rerank documents using the selected backend.
        Args:
            query: The query to rank against.
            documents: List of documents to rank.
        Returns:
            Ranked list of documents.
        """
        return self.optimizer.rerank(query, documents)

    def expand_query(self, query):
        """
        Expand a query to improve retrieval using the selected backend.
        Args:
            query: The original query string.
        Returns:
            Expanded query string.
        """
        return self.optimizer.expand_query(query)

    
"""
# Example for LangChain
langchain_agent = ExistingLangChainAgent()  # Replace with your actual agent instance
lc_manager = OptimizerManager(backend="langchain", agent_or_index=langchain_agent)

# Summarize documents
summaries = lc_manager.summarize(["Document 1", "Document 2"])
print("Summaries:", summaries)

# Rerank documents
ranked_results = lc_manager.rerank("What is _abc()?", ["Doc 1 content", "Doc 2 content"])
print("Ranked Results:", ranked_results)

# Expand query
expanded_query = lc_manager.expand_query("What is _abc()?")
print("Expanded Query:", expanded_query)

# ---

# Example for LlamaIndex
llama_index = ExistingLlamaIndex()  # Replace with your actual index instance
li_manager = OptimizerManager(backend="llamaindex", agent_or_index=llama_index)

# Summarize documents
summaries = li_manager.summarize(["Document 1", "Document 2"])
print("Summaries:", summaries)

# Rerank documents
ranked_results = li_manager.rerank("What is _abc()?", ["Doc 1 content", "Doc 2 content"])
print("Ranked Results:", ranked_results)

# Expand query
expanded_query = li_manager.expand_query("What is _abc()?")
print("Expanded Query:", expanded_query)

"""