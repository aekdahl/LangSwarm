"""
The Lesson Retriever (Read Path) for Reflexive Memory.
Retrieves relevant rules for inference.
"""
import logging
from typing import List

from .models import Lesson
from .store import LessonStore

logger = logging.getLogger(__name__)

class LessonRetriever:
    """
    Retrieves and formats lessons for prompt injection.
    """

    def __init__(self, store: LessonStore):
        self.store = store

    async def get_system_prompt(self, user_query: str, current_agent_role: str, limit_per_tier: int = 3, threshold: float = 0.85) -> str:
        """
        Assemble the 'Reflexive Onion' system prompt.
        Retrieves Global and Role-specific rules and layers them.
        """
        # 1. Fetch Global Rules (Tier 1)
        global_rules = await self.store.search_lessons(
            query_text=user_query,
            limit=limit_per_tier,
            threshold=threshold,
            scope="global"
        )

        # 2. Fetch Role Rules (Tier 2)
        role_rules = await self.store.search_lessons(
            query_text=user_query,
            limit=limit_per_tier,
            threshold=threshold,
            scope="role",
            target_role=current_agent_role
        )
        
        # Increment hit counts (fire & forget)
        all_lessons = global_rules + role_rules
        for lesson in all_lessons:
            try:
                await self.store.increment_hit_count(lesson.lesson_id)
            except Exception:
                pass

        return self.construct_prompt(global_rules, role_rules, current_agent_role)

    def construct_prompt(self, global_rules: List[Lesson], role_rules: List[Lesson], agent_role: str) -> str:
        """
        Format the System Constitution with tiers.
        """
        if not global_rules and not role_rules:
            return ""

        prompt_parts = [f"### SYSTEM CONSTITUTION\nYou are an AI agent acting as: {agent_role}\n"]

        if global_rules:
            prompt_parts.append("### TIER 1: GLOBAL COMMANDMENTS (NON-NEGOTIABLE)\nThese rules apply to every interaction.")
            for i, rule in enumerate(global_rules):
                prompt_parts.append(f"{i+1}. {rule.rule_content}")
            prompt_parts.append("")

        if role_rules:
            prompt_parts.append("### TIER 2: ROLE GUIDELINES\nFollow these unless they contradict Tier 1.")
            for i, rule in enumerate(role_rules):
                prompt_parts.append(f"{i+1}. {rule.rule_content}")
            prompt_parts.append("")
            
        return "\n".join(prompt_parts)

    async def get_relevant_rules(self, query: str, limit: int = 3, threshold: float = 0.85) -> List[Lesson]:
        """
        Legacy/Simple method. Used if just needing a flat list.
        """
        return await self.store.search_lessons(query, limit=limit, threshold=threshold)
