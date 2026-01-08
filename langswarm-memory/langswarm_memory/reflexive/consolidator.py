"""
The Consolidator (Maintenance Path) for Reflexive Memory.
Clusters and merges redundant lessons.
"""
import logging
import json
import math
from typing import List, Dict, Any, Optional

from .models import Lesson
from .store import LessonStore

logger = logging.getLogger(__name__)

class LessonConsolidator:
    """
    Background job to cluster and merge similar lessons.
    """

    def __init__(self, store: LessonStore, api_key: Optional[str] = None, model: str = "gpt-4o", client: Any = None):
        self.store = store
        self.model = model
        self.client = client
        
        if not self.client and api_key:
            try:
                import openai
                self.client = openai.AsyncOpenAI(api_key=api_key)
            except ImportError:
                logger.warning("OpenAI library not installed. Consolidator will fail unless client is provided.")

    async def run_maintenance(self):
        """
        Run the full maintenance cycle: Cluster -> Synthesize -> Prune.
        """
        logger.info("Starting Reflexive Memory maintenance...")
        
        # 1. Fetch All
        lessons = await self.store.get_all_lessons()
        if not lessons:
            logger.info("No lessons to maintain.")
            return

        # 2. Cluster
        clusters = self._cluster_lessons(lessons)
        logger.info(f"Found {len(clusters)} clusters from {len(lessons)} lessons.")

        # 3. Synthesize & Prune
        for cluster in clusters:
            if len(cluster) > 1:
                await self._merge_cluster(cluster)
            else:
                # Optionally handle decay/pruning for single items here
                pass
        
        logger.info("Maintenance complete.")

    def _cluster_lessons(self, lessons: List[Lesson], threshold: float = 0.95) -> List[List[Lesson]]:
        """
        Simple greedy clustering based on cosine similarity of vectors.
        """
        clusters: List[List[Lesson]] = []
        
        # Filter lessons without vectors
        valid_lessons = [l for l in lessons if l.vector]
        
        for lesson in valid_lessons:
            added = False
            for cluster in clusters:
                # Compare with the first element (centroid approximation) or average
                # Using first element for simplicity/MVP
                representative = cluster[0]
                similarity = self._cosine_similarity(lesson.vector, representative.vector)
                
                if similarity > threshold:
                    cluster.append(lesson)
                    added = True
                    break
            
            if not added:
                clusters.append([lesson])
                
        return clusters

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)

    async def _merge_cluster(self, cluster: List[Lesson]):
        """
        Merge a cluster of lessons into a single canonical lesson.
        """
        if not self.client:
            logger.warning("Skipping merge due to missing LLM client")
            return

        variations = "\n".join([f"- {l.rule_content}" for l in cluster])
        
        prompt = f"""Role: You are a System Architect condensing operational rules.

Task:
Here are {len(cluster)} variations of a rule/instruction.
Merge them into one single, robust, canonical rule.
The rule must be an imperative instruction suitable for a System Prompt.
Discard any duplicates or specific noise, keep the general principle.

Variations:
{variations}

Output just the merged rule text. No JSON."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )

            merged_rule = response.choices[0].message.content.strip()
            if not merged_rule:
                return

            logger.info(f"Merging {len(cluster)} rules into: {merged_rule[:50]}...")

            # Create new canonical lesson
            # We use the representative (first) lesson's vector/trigger as a base, 
            # or ideally re-embed the new rule? 
            # The spec says: Prune old, insert new. 
            # The new rule needs a trigger vector. We can use the centroid of the cluster 
            # or the trigger of the most representative one.
            # Using the first one's trigger text/vector for now usually works for "similar" queries.
            
            representative = cluster[0]
            
            new_lesson = Lesson(
                rule_content=merged_rule,
                feedback_source="Maintenance Merge",
                trigger_scenario_text=representative.trigger_scenario_text,
                vector=representative.vector, # Reuse vector of representative or centroid
                hit_count=sum(l.hit_count for l in cluster),
                metadata={"merged_from_count": len(cluster)}
            )

            # Insert new
            await self.store.add_lesson(new_lesson)

            # Delete old
            for old_lesson in cluster:
                await self.store.delete_lesson(old_lesson.lesson_id)

        except Exception as e:
            logger.error(f"Failed to merge cluster: {e}")
