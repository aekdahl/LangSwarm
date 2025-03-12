"""
ConsensusChain: A LangChain-compatible chain that leverages the LLMConsensus
class to achieve consensus among multiple LLM agents for a given query.

Purpose:
- Provides a reusable chain for consensus-building within LangChain workflows.
- Enables chaining consensus with other LangChain tools or agents.
"""

from langchain.chains.base import Chain
from langchain.pydantic_v1 import Extra
from langswarm.synapse.swarm.consensus import LLMConsensus

class ConsensusChain(Chain):
    class Config:
      extra = Extra.allow
        
    def __init__(self, agents, **kwargs):
        """
        Initializes the ConsensusChain.

        Parameters:
        - agents (list): List of agents to use in the consensus process.
        - kwargs: Additional parameters for the LLMConsensus class.
        """
        super().__init__(consensus = LLMConsensus(clients=agents, **kwargs))

    @property
    def input_keys(self):
        """Define input keys for the chain."""
        return ["query"]

    @property
    def output_keys(self):
        """Define output keys for the chain."""
        return ["consensus_result"]

    def _call(self, inputs):
        """
        Processes the input query and returns the consensus result.

        Parameters:
        - inputs (dict): Dictionary containing the query.

        Returns:
        - dict: Dictionary containing the consensus result.
        """
        query = inputs["query"]
        self.consensus.query = query
        result = self.consensus.run()
        return {"consensus_result": result}
