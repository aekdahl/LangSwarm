"""
LangSwarmAggregationTool: A LangChain-compatible tool that uses the LLMAggregation
class to merge and aggregate responses from multiple LLM agents.

Purpose:
- Integrates LLMAggregation into LangChain workflows as a reusable tool.
- Enables aggregation of diverse responses into a unified output.
"""

from ..base import BaseTool
from .config import ToolSettings
from langswarm.synapse.swarm.aggregation import LLMAggregation

class LangSwarmAggregationTool(BaseTool):
    
    def __init__(
        self, 
        identifier,
        agents,
        **kwargs
    ):
        self.identifier = identifier
        self.brief = (
            f"A tool to merge and aggregate responses from multiple agents."
        )

        super().__init__(
            name="LangSwarmAggregationTool",
            description=(
                f"A tool to merge and aggregate responses from multiple agents."
            ),
            instruction=ToolSettings.instructions
        )
        
        self.aggregation = LLMAggregation(clients=agents, **kwargs)

    def run(self, payload = {}, action="query"):
        """Handles file operations based on the provided action and parameters."""
        
        # Map actions to corresponding functions
        action_map = {
            "help": self._help,
            "query": self.query,
        }

        # Execute the corresponding action
        if action in action_map: 
            return self._safe_call(action_map[action], **payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )

    def query(self, query, hb):
        """
        Executes the aggregation workflow with the given query.

        Parameters:
        - query (str): The query to process.
        - hb: Additional aggregation handler, if required.

        Returns:
        - str: The aggregated result.
        """
        self.aggregation.query = query
        return self.aggregation.run(hb)

    def _help(self):
        return self.instruction
