"""
Lineage Tracking for Retrospective Validation

Tracks artifact dependencies and provenance to enable:
- Impact analysis (what's affected by a failure)
- Replay from checkpoints
- Audit trails
- Reproducibility
"""

import logging
import hashlib
from typing import Dict, List, Optional, Set
from collections import deque

from .models import Provenance, Checkpoint

logger = logging.getLogger(__name__)


class LineageGraph:
    """
    Directed acyclic graph (DAG) of artifact dependencies.
    
    Tracks:
    - Artifact provenance (how was it created)
    - Parent/child relationships
    - Content hashes for immutability
    
    Enables:
    - Impact analysis (downstream_of)
    - Replay point identification (find_earliest_valid_ancestor)
    - Audit trails
    """
    
    def __init__(self):
        self.nodes: Dict[str, Provenance] = {}  # artifact_id -> Provenance
        self.edges: Dict[str, List[str]] = {}  # artifact_id -> [child_ids]
        self.checkpoints: Dict[str, Checkpoint] = {}  # step_id -> Checkpoint
        self.invalid_artifacts: Set[str] = set()
    
    def add_node(self, provenance: Provenance) -> None:
        """
        Add artifact node to lineage graph.
        
        Args:
            provenance: Artifact provenance record
        """
        self.nodes[provenance.artifact_id] = provenance
        
        # Build forward edges (parent -> children)
        for parent_id in provenance.inputs:
            if parent_id not in self.edges:
                self.edges[parent_id] = []
            if provenance.artifact_id not in self.edges[parent_id]:
                self.edges[parent_id].append(provenance.artifact_id)
        
        logger.debug(
            f"Added lineage node: {provenance.artifact_id} "
            f"with {len(provenance.inputs)} parents"
        )
    
    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        """
        Add checkpoint for replay capability.
        
        Args:
            checkpoint: Checkpoint with artifact and provenance
        """
        self.checkpoints[checkpoint.step_id] = checkpoint
        self.add_node(checkpoint.provenance)
        
        logger.debug(f"Added checkpoint for step: {checkpoint.step_id}")
    
    def get_provenance(self, artifact_id: str) -> Optional[Provenance]:
        """Get provenance for artifact"""
        return self.nodes.get(artifact_id)
    
    def get_checkpoint(self, step_id: str) -> Optional[Checkpoint]:
        """Get checkpoint for step"""
        return self.checkpoints.get(step_id)
    
    def downstream_of(self, artifact_id: str) -> List[str]:
        """
        Get all downstream artifacts (transitive closure).
        
        This identifies all artifacts that depend on the given artifact,
        directly or indirectly. Used for impact analysis when an artifact
        is invalidated.
        
        Args:
            artifact_id: Source artifact ID
            
        Returns:
            List of downstream artifact IDs (excluding source)
        """
        visited = set()
        queue = deque([artifact_id])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            # Add children to queue
            children = self.edges.get(current, [])
            queue.extend(children)
        
        # Remove source artifact from results
        visited.discard(artifact_id)
        
        logger.debug(
            f"Found {len(visited)} downstream artifacts from {artifact_id}"
        )
        
        return list(visited)
    
    def upstream_of(self, artifact_id: str) -> List[str]:
        """
        Get all upstream artifacts (transitive closure).
        
        This identifies all artifacts that the given artifact depends on,
        directly or indirectly.
        
        Args:
            artifact_id: Target artifact ID
            
        Returns:
            List of upstream artifact IDs (excluding target)
        """
        visited = set()
        queue = deque([artifact_id])
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            # Add parents to queue
            provenance = self.nodes.get(current)
            if provenance:
                queue.extend(provenance.inputs)
        
        # Remove target artifact from results
        visited.discard(artifact_id)
        
        return list(visited)
    
    def find_earliest_valid_ancestor(self, invalid_ids: List[str]) -> Optional[str]:
        """
        Find earliest checkpoint that is not in the invalid set.
        
        Used to determine replay point after invalidation.
        Walks backwards from invalid nodes to find the last valid checkpoint.
        
        Args:
            invalid_ids: List of invalid artifact IDs
            
        Returns:
            Step ID of earliest valid checkpoint, or None
        """
        invalid_set = set(invalid_ids)
        
        # Get all checkpoints in reverse chronological order
        sorted_checkpoints = sorted(
            self.checkpoints.items(),
            key=lambda x: x[1].created_at,
            reverse=True
        )
        
        # Find first checkpoint not in invalid set
        for step_id, checkpoint in sorted_checkpoints:
            artifact_id = checkpoint.provenance.artifact_id
            if artifact_id not in invalid_set:
                logger.info(
                    f"Found earliest valid ancestor: {step_id} ({artifact_id})"
                )
                return step_id
        
        logger.warning("No valid ancestor found, would need to replay from start")
        return None
    
    def mark_invalid(self, artifact_id: str) -> None:
        """Mark artifact as invalid"""
        self.invalid_artifacts.add(artifact_id)
        logger.debug(f"Marked artifact invalid: {artifact_id}")
    
    def mark_valid(self, artifact_id: str) -> None:
        """Mark artifact as valid"""
        self.invalid_artifacts.discard(artifact_id)
        logger.debug(f"Marked artifact valid: {artifact_id}")
    
    def is_valid(self, artifact_id: str) -> bool:
        """Check if artifact is valid"""
        return artifact_id not in self.invalid_artifacts
    
    def get_stats(self) -> Dict[str, int]:
        """Get lineage graph statistics"""
        return {
            "nodes": len(self.nodes),
            "checkpoints": len(self.checkpoints),
            "edges": sum(len(children) for children in self.edges.values()),
            "invalid": len(self.invalid_artifacts)
        }
    
    def visualize_path(self, from_artifact: str, to_artifact: str) -> List[str]:
        """
        Find path between two artifacts (for debugging).
        
        Args:
            from_artifact: Source artifact ID
            to_artifact: Target artifact ID
            
        Returns:
            List of artifact IDs in path, or empty if no path
        """
        # BFS to find path
        queue = deque([(from_artifact, [from_artifact])])
        visited = {from_artifact}
        
        while queue:
            current, path = queue.popleft()
            
            if current == to_artifact:
                return path
            
            for child in self.edges.get(current, []):
                if child not in visited:
                    visited.add(child)
                    queue.append((child, path + [child]))
        
        return []  # No path found


def compute_artifact_hash(artifact: Dict) -> str:
    """
    Compute content hash for artifact (SHA-256).
    
    Artifacts are immutable and content-addressed.
    
    Args:
        artifact: Artifact data
        
    Returns:
        SHA-256 hash as hex string
    """
    import json
    
    # Serialize artifact deterministically
    serialized = json.dumps(artifact, sort_keys=True)
    
    # Compute SHA-256
    hash_obj = hashlib.sha256(serialized.encode('utf-8'))
    return hash_obj.hexdigest()


def create_artifact_id(step_id: str, artifact_name: str, hash_value: str) -> str:
    """
    Create content-addressed artifact ID.
    
    Format: step_id/artifact_name@sha256:hash
    
    Args:
        step_id: Step that produced artifact
        artifact_name: Name of artifact
        hash_value: Content hash
        
    Returns:
        Artifact ID string
    """
    return f"{step_id}/{artifact_name}@sha256:{hash_value}"




