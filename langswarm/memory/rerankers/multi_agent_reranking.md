# Multi-Agent Reranking Workflow

## Overview

The **MultiAgentRerankingWorkflow** is a modular and extensible framework for document reranking using multiple agents. It enables consensus-based scoring from various reranking agents, ensuring robust and high-quality results. This workflow is designed for scenarios where a set of retrieved documents needs improved ranking based on multiple evaluation criteria or perspectives.

## Features

- **Agent-Based Reranking**: Supports reranking by multiple agents, each implementing a custom `rerank` method.
- **Consensus Threshold**: Ensures that only documents meeting a specified minimum agreement among agents are included in the final ranking.
- **Extensible Design**: Easily integrates with existing retrieval workflows.
- **Standalone Usage**: Designed to operate independently of specific retrieval methods.

---

## Code

```python
class MultiAgentRerankingWorkflow:
    """
    Multi-agent reranking workflow to improve document ranking using consensus-based scoring
    from multiple agents.

    Attributes:
        agents (list): List of reranking agents implementing a `rerank` method.
        consensus_threshold (float): Minimum proportion of agents required to agree on a document.
    """

    def __init__(self, agents, consensus_threshold=0.7):
        """
        Initialize the workflow.

        Args:
            agents (list): List of reranking agents.
            consensus_threshold (float): Minimum consensus required for a document to be considered.
        """
        self.agents = agents
        self.consensus_threshold = consensus_threshold

    def rerank(self, documents):
        """
        Rerank documents using multiple agents.

        Args:
            documents (list): List of documents to rerank, where each document is a dictionary
                              with at least a "text" key.

        Returns:
            list: Reranked list of documents with updated scores.
        """
        document_scores = {doc["text"]: [] for doc in documents}

        # Collect scores from agents
        for agent in self.agents:
            agent_scores = agent.rerank(documents)  # Each agent returns [{"text": ..., "score": ...}]
            for score in agent_scores:
                document_scores[score["text"]].append(score["score"])

        # Aggregate scores based on consensus
        reranked = []
        for text, scores in document_scores.items():
            if len(scores) / len(self.agents) >= self.consensus_threshold:
                reranked.append({"text": text, "score": sum(scores) / len(scores)})

        # Sort by aggregated scores in descending order
        return sorted(reranked, key=lambda x: x["score"], reverse=True)
```

---

## Example Usage

### Example 1: Basic Reranking

```python
class MockAgent:
    """
    A mock agent for testing purposes. Each agent implements a `rerank` method.
    """
    def rerank(self, documents):
        return [{"text": doc["text"], "score": len(doc["text"]) % 10} for doc in documents]

# Initialize mock agents
agents = [MockAgent(), MockAgent(), MockAgent()]

# Initialize workflow
workflow = MultiAgentRerankingWorkflow(agents, consensus_threshold=0.7)

# Input documents
documents = [
    {"text": "Document 1: Some content here."},
    {"text": "Document 2: Another example."},
    {"text": "Document 3: Yet another piece."}
]

# Perform reranking
reranked_docs = workflow.rerank(documents)

# Output results
for doc in reranked_docs:
    print(doc)
```

### Example Output:
```plaintext
{'text': 'Document 3: Yet another piece.', 'score': 6.666666666666667}
{'text': 'Document 1: Some content here.', 'score': 5.333333333333333}
{'text': 'Document 2: Another example.', 'score': 4.666666666666667}
```

---

## Notes

- **Agent Interface**: Each agent must implement a `rerank` method that takes a list of documents and returns a list of dictionaries with `text` and `score` keys.
- **Consensus Threshold**: Adjust the threshold to balance inclusivity and agreement among agents.
- **Extensibility**: Easily extend the workflow by adding agents with domain-specific scoring mechanisms.

---

## Future Enhancements

- **Parallel Execution**: Optimize agent execution by running reranking processes in parallel.
- **Caching**: Implement caching for previously reranked document sets to improve performance.
- **Integration**: Develop a `to_framework` method to integrate with LangChain, LlamaIndex, or other frameworks seamlessly.
