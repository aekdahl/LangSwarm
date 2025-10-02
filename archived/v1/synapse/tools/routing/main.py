"""
LangSwarmRoutingTool: A LangChain-compatible tool that uses the LLMRouting
class to dynamically route tasks to the appropriate agents or workflows.

Purpose:
- Integrates LLMRouting into LangChain workflows as a dynamic routing tool.
- Allows tasks to be routed based on predefined logic.
"""

from ..base import BaseTool
from .config import ToolSettings
from langswarm.synapse.swarm.routing import LLMRouting

class LangSwarmRoutingTool(BaseTool):
        
    def __init__(
        self, 
        identifier,
        route,
        bots,
        main_bot,
        **kwargs
    ):
        """
        Initializes the LangSwarmRoutingTool.

        Parameters:
        - route (int): The routing logic to apply.
        - bots (dict): Dictionary of bots to route tasks.
        - main_bot: The primary bot for routing decisions.
        - kwargs: Additional parameters for the LLMRouting class.
        """
        self.identifier = identifier
        self.brief = (
            f"A tool to dynamically route tasks to the appropriate agents."
        )

        super().__init__(
            name="LangSwarmRoutingTool",
            description=(
                f"A tool to dynamically route tasks to the appropriate agents."
            ),
            instruction=ToolSettings.instructions
        )
        
        self.routing = LLMRouting(route=route, bots=bots, main_bot=main_bot, **kwargs)

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
        Executes the routing workflow with the given query.

        Parameters:
        - query (str): The query to process.

        Returns:
        - str: The result from the routed agent.
        """
        self.routing.query = query
        return self.routing.run()

    def _help(self):
        return self.instruction
