from typing import List, Optional, Any, Dict
from pydantic import BaseModel
try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None

class SwarmConfig(BaseModel):
    model_name: str = "all-MiniLM-L6-v2"
    threshold: float = 0.75
    paraphrase_threshold: float = 0.8
    verbose: bool = False

class SwarmProtocol:
    """
    Base protocol for Swarm Intelligence.
    Implements semantic similarity and consensus logic.
    """
    def __init__(self, config: SwarmConfig = SwarmConfig()):
        self.config = config
        self._model = None
        
    @property
    def model(self):
        if self._model is None:
            if SentenceTransformer is None:
                raise ImportError("sentence-transformers is required for SwarmProtocol")
            self._model = SentenceTransformer(self.config.model_name)
        return self._model

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        embeddings = self.model.encode([text1, text2])
        return util.cos_sim(embeddings[0], embeddings[1]).item()

    def detect_consensus(self, texts: List[str]) -> Dict[str, Any]:
        """
        Detect consensus among a list of texts (agent outputs).
        Returns the best text and its support score.
        """
        if not texts:
            return {"consensus": None, "score": 0.0, "group_size": 0}
            
        embeddings = self.model.encode(texts)
        
        # Simple clustering based on paraphrase threshold
        # Find the text with highest average similarity to all others
        best_text = None
        best_score = -1.0
        best_group_size = 0
        
        for i, text in enumerate(texts):
            similarities = util.cos_sim(embeddings[i], embeddings).squeeze()
            # Count how many pass the paraphrase threshold
            group_size = (similarities >= self.config.paraphrase_threshold).sum().item()
            avg_score = similarities.mean().item()
            
            if group_size > best_group_size or (group_size == best_group_size and avg_score > best_score):
                best_group_size = group_size
                best_score = avg_score
                best_text = text
                
        return {
            "consensus": best_text,
            "score": best_score,
            "group_size": best_group_size
        }
