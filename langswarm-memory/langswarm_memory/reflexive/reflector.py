"""
The Reflector Agent (Write Path) for Reflexive Memory.
Analyzes failures and generates generalized rules.
"""
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from .models import Lesson

logger = logging.getLogger(__name__)

class ReflectorAgent:
    """
    Analyzes agent failures and generates generalized rules (Lessons).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", client: Any = None):
        """
        Initialize Reflector.
        Args:
            api_key: OpenAI API key (if using default client)
            model: Model to use (must be capable of reasoning, e.g. GPT-4o)
            client: Optional pre-configured AsyncOpenAI client
        """
        self.model = model
        self.client = client
        
        if not self.client and api_key:
            try:
                import openai
                self.client = openai.AsyncOpenAI(api_key=api_key)
            except ImportError:
                logger.warning("OpenAI library not installed. Reflector will fail unless client is provided.")

    async def analyze_failure(self, user_query: str, agent_response: str, user_correction: str, agent_role: str = "generic") -> Optional[Lesson]:
        """
        Analyze a failure and generate a Lesson.
        """
        if not self.client:
            logger.error("No OpenAI client available for Reflector.")
            return None

        prompt = f"""You are the System Architect. An agent failed a task.
Analyze the failure and generate a governance rule to prevent recurrence.

CONTEXT:
- Role: {agent_role}
- Query: "{user_query}"
- Failure: "{user_correction}"
- Agent Response Snippet: "{agent_response[:300]}"

DECISIONS:
1. Rule: Write a concise imperative instruction.
2. Scope:
   - 'GLOBAL' if this applies to ALL agents (e.g., safety, formatting).
   - 'ROLE' if this applies only to {agent_role}s.
3. Trigger: The phrasing of the user query that should trigger this rule.

OUTPUT JSON:
{{
  "rule_text": "...",
  "suggested_scope": "ROLE | GLOBAL",
  "trigger_vector_text": "The phrasing of the user query that should trigger this rule"
}}
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )

            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from Reflector LLM")
                return None

            data = json.loads(content)
            rule_text = data.get("rule_text")
            suggested_scope = data.get("suggested_scope", "GLOBAL").lower() # Normalize to lowercase
            trigger_vector_text = data.get("trigger_vector_text", user_query)

            if not rule_text:
                logger.error("No rule_text found in Reflector output")
                return None
            
            # Map scope
            if "role" in suggested_scope:
                scope = "role"
                target_role = agent_role
            else:
                scope = "global"
                target_role = None

            # Create Lesson
            lesson = Lesson(
                rule_content=rule_text,
                trigger_scenario_text=trigger_vector_text,
                scope=scope,
                target_role=target_role,
                source_incident=user_correction,
                metadata={
                    "original_query": user_query,
                    "agent_role": agent_role
                }
            )
            
            logger.info(f"Generated lesson: {rule_text} (Scope: {scope})")
            return lesson

        except Exception as e:
            logger.error(f"Reflector analysis failed: {e}")
            return None
