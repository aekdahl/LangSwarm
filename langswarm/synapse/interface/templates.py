from .langswarm import LangSwarm

class Templates:
    """
    Predefined templates for common LangSwarm workflows.
    """

    @staticmethod
    def consensus(agents, query):
        """
        Predefined template for consensus workflow.

        Parameters:
        - agents (list): List of agents.
        - query (str): Query string.

        Returns:
        - str: Consensus result.
        """
        pipeline = LangSwarm.create(workflow="consensus", agents=agents)
        return pipeline.run(query)

    @staticmethod
    def voting(agents, query):
        """
        Predefined template for voting workflow.

        Parameters:
        - agents (list): List of agents.
        - query (str): Query string.

        Returns:
        - tuple: Voting result, group size, and responses.
        """
        pipeline = LangSwarm.create(workflow="voting", agents=agents)
        return pipeline.run(query)

    @staticmethod
    def branching(agents, query):
        """
        Predefined template for branching workflow.

        Parameters:
        - agents (list): List of agents.
        - query (str): Query string.

        Returns:
        - list: List of responses from the agents.
        """
        pipeline = LangSwarm.create(workflow="branching", agents=agents)
        return pipeline.run(query)

    @staticmethod
    def aggregation(agents, query):
        """
        Predefined template for aggregation workflow.

        Parameters:
        - agents (list): List of agents.
        - query (str): Query string.

        Returns:
        - str: Aggregated result.
        """
        pipeline = LangSwarm.create(workflow="aggregation", agents=agents)
        return pipeline.run(query)
