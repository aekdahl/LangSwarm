"""
RoutingChain: A LangChain-compatible chain that uses the LLMRouting
class to dynamically route tasks to the appropriate agents or workflows.

Purpose:
- Provides a reusable chain for dynamic routing within LangChain.
- Enables chaining routing with other tools or agents in pipelines.
"""

from langchain.chains.base import Chain
from langchain.pydantic_v1 import Extra
from langswarm.synapse.swarm.routing import LLMRouting

class RoutingChain(Chain):
    class Config:
      extra = Extra.allow
        
    def __init__(self, route, bots, main_bot, **kwargs):
        """
        Initializes the RoutingChain.

        Parameters:
        - route (int): The routing logic to apply.
        - bots (dict): Dictionary of bots to route tasks.
        - main_bot: The primary bot for routing decisions.
        - kwargs: Additional parameters for the LLMRouting class.
        """
        super().__init__(routing = LLMRouting(route=route, bots=bots, main_bot=main_bot, **kwargs))

    @property
    def input_keys(self):
        """Define input keys for the chain."""
        return ["query"]

    @property
    def output_keys(self):
        """Define output keys for the chain."""
        return ["routed_result"]

    def _call(self, inputs):
        """
        Processes the input query and returns the routed result.

        Parameters:
        - inputs (dict): Dictionary containing the query.

        Returns:
        - dict: Dictionary containing the routed result.
        """
        query = inputs["query"]
        self.routing.query = query
        result = self.routing.run()
        return {"routed_result": result}
