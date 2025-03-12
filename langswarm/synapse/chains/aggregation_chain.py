"""
AggregationChain: A LangChain-compatible chain that uses the LLMAggregation
class to merge and aggregate responses from multiple LLM agents.

Purpose:
- Provides a reusable chain for aggregation workflows within LangChain.
- Enables chaining aggregation with other tools or agents in pipelines.
"""
from langchain.chains.base import Chain
from langchain.pydantic_v1 import Extra
from langswarm.synapse.swarm.aggregation import LLMAggregation

class AggregationChain(Chain):
    class Config:
        extra = Extra.allow

    def __init__(self, agents, **kwargs):
        """
        Initializes the AggregationChain.

        Parameters:
        - agents (list): List of agents to use in the aggregation process.
        - kwargs: Additional parameters for the LLMAggregation class.
        """
        #self.aggregation = LLMAggregation(clients=agents, **kwargs)
        super().__init__(aggregation = LLMAggregation(clients=agents, **kwargs))

    @property
    def input_keys(self):
        """Define input keys for the chain."""
        return ["query"]

    @property
    def output_keys(self):
        """Define output keys for the chain."""
        return ["aggregated_result"]

    def _call(self, inputs):
        """
        Processes the input query and returns the aggregated result.

        Parameters:
        - inputs (dict): Dictionary containing the query and handler.

        Returns:
        - dict: Dictionary containing the aggregated result.
        """
        query = inputs["query"]
        hb = inputs.get("hb")
        self.aggregation.query = query
        result = self.aggregation.run(hb)
        return {"aggregated_result": result}
