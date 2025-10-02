"""
LangSwarmVotingTool: A LangChain-compatible tool that uses the LLMVoting
class to enable voting-based decision-making among multiple agents.

Purpose:
- Integrates LLMVoting into LangChain workflows as a voting tool.
- Facilitates collaborative decision-making by tallying agent responses.
"""
from ..base import BaseTool
from .config import ToolSettings
from langswarm.synapse.swarm.voting import LLMVoting

class LangSwarmVotingTool(BaseTool):
        
    def __init__(
        self, 
        identifier,
        route,
        bots,
        main_bot,
        **kwargs
    ):
        """
        Initializes the LangSwarmVotingTool.

        Parameters:
        - agents (list): List of agents to use in the voting process.
        - kwargs: Additional parameters for the LLMVoting class.
        """
        self.identifier = identifier
        self.brief = (
            f"A tool to enable voting-based decision-making among agents."
        )

        super().__init__(
            name="LangSwarmVotingTool",
            description=(
                f"A tool to enable voting-based decision-making among agents."
            ),
            instruction=ToolSettings.instructions
        )
        
        self.voting = LLMVoting(clients=agents, **kwargs)

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
        Executes the voting workflow with the given query.

        Parameters:
        - query (str): The query to process.

        Returns:
        - tuple: The consensus result, group size, and list of responses.
        """
        self.voting.query = query
        return self.voting.run()

    def _help(self):
        return self.instruction
