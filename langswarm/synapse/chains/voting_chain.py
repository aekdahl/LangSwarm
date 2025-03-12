"""
VotingChain: A LangChain-compatible chain that uses the LLMVoting
class to enable voting-based decision-making among multiple agents.

Purpose:
- Provides a reusable chain for voting workflows within LangChain.
- Enables chaining voting with other tools or agents in pipelines.
"""

from langchain.chains.base import Chain
from langchain.pydantic_v1 import Extra
from langswarm.synapse.swarm.voting import LLMVoting

class VotingChain(Chain):
    class Config:
      extra = Extra.allow
        
    def __init__(self, agents, **kwargs):
        """
        Initializes the VotingChain.

        Parameters:
        - agents (list): List of agents to use in the voting process.
        - kwargs: Additional parameters for the LLMVoting class.
        """
        super().__init__(voting = LLMVoting(clients=agents, **kwargs))

    @property
    def input_keys(self):
        """Define input keys for the chain."""
        return ["query"]

    @property
    def output_keys(self):
        """Define output keys for the chain."""
        return ["voting_result", "group_size", "responses"]

    def _call(self, inputs):
        """
        Processes the input query and returns the voting result.

        Parameters:
        - inputs (dict): Dictionary containing the query.

        Returns:
        - dict: Dictionary containing the voting result, group size, and responses.
        """
        query = inputs["query"]
        result, group_size, responses = self.voting.run()
        return {
            "voting_result": result,
            "group_size": group_size,
            "responses": responses,
        }
