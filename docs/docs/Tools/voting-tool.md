---
title: LangSwarmVotingTool
sidebar_position: 94
---

# LangSwarmVotingTool

---

## **Overview**
The `LangSwarmVotingTool` is a LangChain-compatible tool designed to facilitate voting-based decision-making among multiple Large Language Model (LLM) agents. It uses the `LLMVoting` class to aggregate responses from multiple agents, tally votes, and determine a consensus result.

---

## **Purpose**
The primary purpose of the `LangSwarmVotingTool` is:
- **Collaborative Decision-Making**: To enable developers to use a voting mechanism as a step in LangChain workflows for determining the best or most popular response among agents.
- **Pipeline Integration**: To serve as a modular voting tool that integrates seamlessly into broader LangChain pipelines.
- **Transparency**: To provide detailed insights into the voting process, including the group size and all individual responses.

---

## **Class Definition**

```python
class LangSwarmVotingTool(Tool):
    def __init__(self, agents, **kwargs):
        """
        Initializes the LangSwarmVotingTool.

        Parameters:
        - agents (list): List of agents to use in the voting process.
        - kwargs: Additional parameters for the LLMVoting class.
        """
        self.voting = LLMVoting(clients=agents, **kwargs)
        super().__init__(
            name="LangSwarm Voting",
            func=self.run,
            description="A tool to enable voting-based decision-making among agents."
        )

    def run(self, query):
        """
        Executes the voting workflow with the given query.

        Parameters:
        - query (str): The query to process.

        Returns:
        - tuple: The consensus result, group size, and list of responses.
        """
        self.voting.query = query
        return self.voting.run()
```

---

## **Key Components**

1. **`__init__` Method**
   - Initializes the tool with a list of agents and additional parameters.
   - Creates an instance of the `LLMVoting` class to handle the voting process.
   - Parameters:
     - `agents`: A list of LLM agents contributing to the voting process.
     - `kwargs`: Optional parameters passed to configure the `LLMVoting` class.
   - Inherits from the `Tool` class, defining the tool's name and description.

2. **`run` Method**
   - Executes the voting workflow.
   - Parameters:
     - `query`: The query string to be processed.
   - Workflow:
     - Assigns the query to the `LLMVoting` instance.
     - Calls the `run` method of `LLMVoting` to tally votes and determine a consensus result.
   - Returns a tuple containing:
     - `consensus_result`: The final result based on the votes.
     - `group_size`: The number of agents participating in the voting process.
     - `responses`: A list of all responses from the agents.

---

## **Usage**

1. **Initialization**
   ```python
   from langswarm.swarm.voting import LLMVoting
   from mymodule import LangSwarmVotingTool

   # Example list of agents (LLM clients)
   agents = [agent1, agent2, agent3]

   # Initialize the LangSwarmVotingTool
   tool = LangSwarmVotingTool(agents=agents, param1=value1, param2=value2)
   ```

2. **Execution**
   ```python
   # Input query
   query = "What is the best renewable energy source?"

   # Get the voting result
   consensus_result, group_size, responses = tool.run(query)
   print("Consensus Result:", consensus_result)
   print("Group Size:", group_size)
   print("All Responses:", responses)
   ```

3. **Integration with LangChain Workflows**
   - The `LangSwarmVotingTool` can be directly used as a tool in LangChain workflows.
   ```python
   from langchain.agents import initialize_agent

   tools = [tool]
   agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

   # Run the agent with the tool
   result = agent.run("How should governments incentivize green energy?")
   print(result)
   ```

---

## **Customization**
- **Adding Custom Parameters**: Additional parameters can be passed to `LLMVoting` during initialization to customize the voting logic.
- **Extending the Tool**: Subclass `LangSwarmVotingTool` to modify or enhance the voting logic, such as weighting votes or applying additional filters.

---

## **Use Cases**
1. **Decision-Making**:
   - Use voting among agents to identify the best or most popular solution to a problem.
2. **Validation**:
   - Validate outputs by requiring a majority agreement among agents.
3. **Ranking**:
   - Rank multiple responses based on agent votes, highlighting the top result.
4. **Bias Mitigation**:
   - Aggregate diverse perspectives to reduce individual agent biases.

---

## **Comparison with Other Tools**
- **LangSwarmVotingTool**: Uses a voting mechanism to determine the most agreed-upon response among agents.
- **LangSwarmConsensusTool**: Focuses on achieving a unified result through consensus but without explicitly tallying votes.
- **LangSwarmBranchingTool**: Generates diverse responses without reconciling them into a single result.
- **LangSwarmAggregationTool**: Merges responses into a unified result without requiring strict agreement or tallying.
