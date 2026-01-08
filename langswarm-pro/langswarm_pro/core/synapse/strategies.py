from typing import List, Dict, Any
from .protocol import SwarmProtocol, SwarmConfig

class VotingStrategy(SwarmProtocol):
    """
    Strategy where agents 'vote' (implicitly via consensus) on the best answer.
    """
    async def run(self, responses: List[str]) -> Dict[str, Any]:
        """
        Analyze responses and return the consensus winner.
        """
        return self.detect_consensus(responses)

class AggregationStrategy(SwarmProtocol):
    """
    Strategy that attempts to merge unique information from all responses.
    """
    async def run(self, responses: List[str]) -> str:
        """
        Aggregate unique responses into a single summary.
        """
        # 1. Deduplicate based on semantic similarity
        unique_responses = []
        embeddings = self.model.encode(responses)
        used_indices = set()
        
        for i in range(len(responses)):
            if i in used_indices:
                continue
            
            unique_responses.append(responses[i])
            used_indices.add(i)
            
            # Mark similar responses as used
            similarities = self.calculate_similarity(responses[i], responses)
            # Todo: optimize this O(N^2) loop with matrix if needed, keeping simple for now
            # Implementation details similar to legacy code
            pass 
        
        # In a real implementation, we would use an LLM to merge these.
        # For this port, we will just join them.
        return "\n\n".join(set(responses)) # Simple set dedupe for now as MVP
