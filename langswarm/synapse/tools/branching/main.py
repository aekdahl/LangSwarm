"""
LangSwarmBranchingTool: A LangChain-compatible tool that uses the LLMBranching
class to generate multiple responses from a set of LLM agents for a given query.

Purpose:
- Integrates LLMBranching into LangChain workflows as a modular tool.
- Enables generation of diverse outputs from multiple agents.
"""

from ..base import BaseTool
from .config import ToolSettings
from langswarm.synapse.swarm.branching import LLMBranching


class LangSwarmBranchingTool(BaseTool):
    
    def __init__(
        self, 
        identifier,
        agents,
        **kwargs
    ):
        self.identifier = identifier
        self.brief = (
            f"A tool to generate multiple responses from a set of agents."
        )

        super().__init__(
            name="LangSwarmBranchingTool",
            description=(
                f"A tool to generate multiple responses from a set of agents."
            ),
            instruction=ToolSettings.instructions
        )
        
        self.branching = LLMBranching(clients=agents, **kwargs)

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

    def query(self, query):
        """
        Executes the branching workflow with the given query.

        Parameters:
        - query (str): The query to process.

        Returns:
        - list: A list of responses from the agents.
        """
        self.branching.query = query
        return self.branching.run()

    def _help(self):
        return self.instruction
