from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

class LangChainOptimizer(BaseOptimizer):
    def __init__(self, agent):
        """
        Initialize with an existing LangChain agent.
        Args:
            agent: The LangChain agent instance to use.
        """
        self.agent = agent

    def summarize(self, documents):
        """
        Summarize a list of documents using the agent's summarization capability.
        Args:
            documents: List of text documents to summarize.
        Returns:
            List of summaries.
        """
        summaries = []
        for doc in documents:
            response = self.agent.run({"task": "summarize", "document": doc})
            summaries.append(response)
        return summaries

    def rerank(self, query, documents):
        """
        Rerank documents using the existing LangChain reranking method.
        Args:
            query: The query to rank against.
            documents: List of documents to rank.
        Returns:
            Ranked list of documents.
        """
        return self.agent.rerank(query, documents)

    def expand_query(self, query):
        """
        Expand a query to improve retrieval using the LangChain agent.
        Args:
            query: The original query string.
        Returns:
            Expanded query string.
        """
        prompt = (
            "Expand the following query to improve information retrieval by "
            "adding synonyms, related terms, or clarifying phrases:\n\nQuery: {query}"
        )
        chain = LLMChain(
            llm=self.agent.llm,
            prompt=PromptTemplate(input_variables=["query"], template=prompt)
        )
        return chain.run({"query": query})
