class CombinedRerankingWorkflow:
    """
    Combines multiple reranking strategies (e.g., semantic similarity and metadata-based scoring)
    into a unified reranking workflow.

    Attributes:
        rerankers (list): A list of reranker instances.
        weights (list): Corresponding weights for each reranker.
    """
    def __init__(self, rerankers, weights=None):
        """
        Initialize the workflow with rerankers and their weights.

        Args:
            rerankers (list): List of reranker instances (subclasses of BaseReranker).
            weights (list): List of weights for each reranker (default: equal weights).
        """
        self.rerankers = rerankers
        if weights is None:
            self.weights = [1.0 / len(rerankers)] * len(rerankers)
        else:
            self.weights = weights

    def run(self, query, documents):
        """
        Perform combined reranking.

        Args:
            query (str): The query string.
            documents (list): List of documents to rerank.

        Returns:
            list: Documents sorted by combined scores.
        """
        # Initialize scores for each document
        scores = {doc["text"]: 0.0 for doc in documents}

        # Iterate over each reranker and aggregate scores
        for reranker, weight in zip(self.rerankers, self.weights):
            ranked_docs = reranker.rerank(query, documents)
            for doc in ranked_docs:
                scores[doc["text"]] += doc["score"] * weight

        # Sort documents by combined scores
        combined_results = [{"text": doc, "score": score} for doc, score in scores.items()]
        return sorted(combined_results, key=lambda x: x["score"], reverse=True)


class MultiAgentRerankingWorkflow:
    """
    Multi-agent reranking strategy that utilizes multiple agents to score and aggregate
    reranking results for improved consensus-based reranking.

    Attributes:
        agents (list): A list of reranking agent instances.
        aggregation_function (callable): A function to combine scores (default: weighted average).
    """

    def __init__(self, agents, aggregation_function=None):
        """
        Initialize the multi-agent reranking workflow.

        Args:
            agents (list): List of reranking agent instances (subclasses of BaseReranker).
            aggregation_function (callable): Function to aggregate scores (default: weighted average).
        """
        self.agents = agents
        self.aggregation_function = aggregation_function or self.default_aggregation_function

    def default_aggregation_function(self, scores):
        """
        Default aggregation function (weighted average of scores).

        Args:
            scores (list): List of scores from all agents.

        Returns:
            float: Aggregated score.
        """
        total_weight = sum(weight for _, weight in scores)
        return sum(score * weight for score, weight in scores) / total_weight

    def run(self, query, documents):
        """
        Perform multi-agent reranking.

        Args:
            query (str): The query string.
            documents (list): List of documents to rerank.

        Returns:
            list: Documents sorted by aggregated scores.
        """
        # Collect scores from all agents
        scores = {doc["text"]: [] for doc in documents}

        for agent in self.agents:
            agent_ranking = agent.rerank(query, documents)
            for idx, doc in enumerate(agent_ranking):
                scores[doc["text"]].append((doc["score"], 1 / (idx + 1)))  # Weight based on rank

        # Aggregate scores
        aggregated_scores = {
            doc: self.aggregation_function(scores[doc])
            for doc in scores
        }

        # Sort documents by aggregated scores
        sorted_documents = sorted(
            [{"text": doc, "score": score} for doc, score in aggregated_scores.items()],
            key=lambda x: x["score"],
            reverse=True
        )
        return sorted_documents
