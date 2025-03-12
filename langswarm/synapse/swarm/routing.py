import re

from .swarm import Swarm
from .branching import LLMBranching
from .consensus import LLMConsensus

class LLMRouting:
    """
    A class for dynamic routing of tasks to different LLM-based workflows.

    Available Routes:
    - Route 0: Regular route
    - Route 1: LLMBranching with consolidation
    - Route 2: LLMConsensus
    - Route 3: Prompt reformulator
    - Route 4: Prompt to inline

    Attributes:
        route (int): The selected routing strategy.
        bots: Container for different LLM bots.
        main_bot (LLM): The main bot instance for processing queries.
        query (str): Input query to be processed.
        remove_chat (bool): Flag to determine whether to remove chat history after processing.
        verbose (bool): Enable detailed logs.
    """

    def __init__(self, route, bots, main_bot, query, remove_chat=False, verbose=False):
        """
        Initialize the LLMRouting class with the specified route and parameters.

        Args:
            route (int): The selected routing strategy.
            bots: Container for different LLM bots.
            main_bot (LLM): The main bot instance for processing queries.
            query (str): Input query to be processed.
            remove_chat (bool): Whether to remove chat history after processing.
            verbose (bool): Enable detailed logs.
        """
        self.route = route
        self.bots = bots
        self.main_bot = main_bot
        self.query = query
        self.remove_chat = remove_chat
        self.verbose = verbose

    def call(self, _bot, _query):
        """
        Process a query using the specified bot.

        Args:
            _bot (LLM): The bot instance to use for processing.
            _query (str): The query to process.

        Returns:
            str: The response from the bot.
        """
        response = _bot.chat(q=_query)
        if self.remove_chat:
            _bot.remove()
        else:
            _bot.add_response(response)

        return response

    def safe_str_to_int(self, s):
        """
        Safely convert a string to an integer by extracting numeric parts.

        Args:
            s (str): The string to convert.

        Returns:
            int: The extracted integer, or 0 if no valid number is found.
        """
        match = re.search(r"[-+]?\d*\.?\d+", s)
        if match:
            return int(float(match.group()))
        return 0

    def run(self):
        """
        Execute the selected routing strategy.

        Returns:
            str: The result of the routing workflow.
        """
        if self.route == 0:
            # Route 0: Regular route
            if self.verbose:
                print('\nRunning Route 0: Regular route')
            return self.call(self.main_bot, self.query)

        elif self.route == 1:
            # Route 1: LLMBranching with consolidation
            if self.verbose:
                print('\nRunning Route 1: LLMBranching with consolidation')

            swarm = LLMBranching(
                query=self.query,
                verbose=self.verbose,
                clients=self.bots
            )

            responses = swarm.run()

            query = f"""
            Below is a query and a list of LLM agent's responses to that query. Your goal is to select the best response to the query.

            Instructions:
            Select only one response from the list and answer with the index of that response only.
            The index starts at 0 for the first response.

            ---

            Task:
            {self.query}

            ---

            Response:
            {responses}

            ---

            Output only the number (index).

            Example output: '7'.
            """

            consensus_swarm = LLMConsensus(
                query=query,
                verbose=True,
                clients=self.bots
            )

            run_result = consensus_swarm.run()
            index = self.safe_str_to_int(run_result)

            try:
                return responses[index]
            except IndexError as e:
                if self.verbose:
                    print('IndexError:', e)
                return "Error: Invalid response index."

        elif self.route == 2:
            # Route 2: LLMConsensus
            if self.verbose:
                print('\nRunning Route 2: LLMConsensus')

            swarm = LLMConsensus(
                query=self.query,
                verbose=self.verbose,
                clients=self.bots
            )

            return swarm.run()

        elif self.route == 3:
            # Route 3: Prompt reformulator
            if self.verbose:
                print('\nRunning Route 3: Prompt reformulator')

            response = self.call(self.bots.prompt.prompt_reformulator_llm, self.query)

            if self.verbose:
                print('\nUpdated query via route 3:', response)

            return self.call(self.main_bot, response)

        elif self.route == 4:
            # Route 4: Prompt to inline
            if self.verbose:
                print('\nRunning Route 4: Prompt to inline')

            response = self.call(self.bots.prompt.remarks_to_inline_bot, self.query)

            if self.verbose:
                print('\nUpdated query via route 4:', response)

            return self.call(self.main_bot, response)
