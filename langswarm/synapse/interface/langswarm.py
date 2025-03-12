class LangSwarm:
    """
    LangSwarm High-Level API for initializing and configuring workflows.

    This class provides a unified interface for creating pipelines using LangSwarm modules.
    """

    @staticmethod
    def create(workflow, agents, **kwargs):
        """
        Create a LangSwarm pipeline based on the specified workflow.

        Parameters:
        - workflow (str): The type of workflow (e.g., 'consensus', 'voting', 'branching', 'aggregation').
        - agents (list): List of agents to be used in the workflow.
        - kwargs: Additional parameters for specific workflows.

        Returns:
        - object: Initialized pipeline or tool based on the selected workflow.
        """
        if workflow == "consensus":
            from langswarm.synapse.swarm.consensus import LangSwarmConsensusTool
            return LangSwarmConsensusTool(agents=agents, **kwargs)

        elif workflow == "voting":
            from langswarm.synapse.swarm.voting import LangSwarmVotingTool
            return LangSwarmVotingTool(agents=agents, **kwargs)

        elif workflow == "branching":
            from langswarm.synapse.swarm.branching import LangSwarmBranchingTool
            return LangSwarmBranchingTool(agents=agents, **kwargs)

        elif workflow == "aggregation":
            from langswarm.synapse.swarm.aggregation import LangSwarmAggregationTool
            return LangSwarmAggregationTool(agents=agents, **kwargs)

        else:
            raise ValueError(f"Unsupported workflow type: {workflow}")
