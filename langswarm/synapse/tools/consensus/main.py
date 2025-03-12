"""
LangSwarmConsensusTool: A LangChain-compatible tool that uses the LLMConsensus
class to achieve consensus among multiple LLM agents for a given query.

Purpose:
- Integrates LLMConsensus into LangChain workflows as a reusable tool.
- Allows developers to use consensus-building as a modular step in pipelines.
"""
from ..base import BaseTool
from .config import ToolSettings
from langswarm.synapse.swarm.consensus import LLMConsensus

class LangSwarmConsensusTool(BaseTool):
    consensus: LLMConsensus = Field(..., description="ToDo: Add field description.")
    
    def __init__(
        self, 
        identifier,
        agents,
        **kwargs
    ):
        self.identifier = identifier
        self.brief = (
            f"A tool to reach consensus among multiple agents for a given query."
        )

        super().__init__(
            name="LangSwarmConsensusTool",
            description=(
                f"A tool to reach consensus among multiple agents for a given query."
            ),
            instruction=ToolSettings.instructions
        )
        
        self.consensus = LLMConsensus(clients=agents, **kwargs)

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
        Executes the consensus workflow with the given query.

        Parameters:
        - query (str): The query to process.

        Returns:
        - str: The consensus result.
        """
        self.consensus.query = query
        return self.consensus.run()

    def _help(self):
        return self.instruction