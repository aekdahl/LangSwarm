class MultiAgentRerankingTool:
    """
    Wrapper for MultiAgentRerankingWorkflow, exposing it as a tool for deeper reranking.

    Attributes:
        workflow (MultiAgentRerankingWorkflow): The underlying reranking workflow.
        description (str): Description of the tool for agent decision-making.
    """

    def __init__(self, agents, consensus_threshold=0.7):
        self.workflow = MultiAgentRerankingWorkflow(agents, consensus_threshold)
        self.description = (
            "Use this tool to perform deep reranking of search results using multiple agents. "
            "Best suited for uncovering more precise results."
        )

    def run(self, query, results):
        """
        Execute the workflow.

        Args:
            query (str): The search query.
            results (list): Initial set of results to rerank.

        Returns:
            list: Reranked results.
        """
        return self.workflow.rerank(results)
