"""
BranchingChain: A LangChain-compatible chain that uses the LLMBranching
class to generate multiple responses from a set of LLM agents for a given query.

Purpose:
- Provides a reusable chain for branching workflows within LangChain.
- Enables chaining branching with other tools or agents in pipelines.
"""

from langchain.chains.base import Chain
from langchain.pydantic_v1 import Extra
from langswarm.synapse.swarm.branching import LLMBranching

class BranchingChain(Chain):
    class Config:
      extra = Extra.allow

    def __init__(self, agents, **kwargs):
        """
        Initializes the BranchingChain.

        Parameters:
        - agents (list): List of agents to use in the branching process.
        - kwargs: Additional parameters for the LLMBranching class.
        """
        super().__init__(branching = LLMBranching(clients=agents, **kwargs))
        
    @property
    def input_keys(self):
        """Define input keys for the chain."""
        return ["query"]

    @property
    def output_keys(self):
        """Define output keys for the chain."""
        return ["responses"]

    def _call(self, inputs):
        """
        Processes the input query and returns a list of responses.

        Parameters:
        - inputs (dict): Dictionary containing the query.

        Returns:
        - dict: Dictionary containing the list of responses.
        """
        query = inputs["query"]
        self.branching.query = query
        responses = self.branching.run()
        return {"responses": responses}
