---
title: LangSwarmBranchingTool
sidebar_position: 91
---

# LangSwarmBranchingTool

---

## **Overview**
The `LangSwarmBranchingTool` is a LangChain-compatible tool designed to generate multiple responses from a set of Large Language Model (LLM) agents. By leveraging the `LLMBranching` class, this tool enables workflows that require exploration of diverse outputs from multiple agents for a given query.

---

## **Purpose**
The primary purpose of the `LangSwarmBranchingTool` is:
- **Diverse Output Generation**: To collect and present multiple responses from different agents for a single query.
- **Pipeline Integration**: To provide a modular tool within LangChain workflows, enabling smooth integration with other tools or agents.
- **Flexibility**: To allow configuration of the branching process through additional parameters.

---

## **Class Definition**

```python
class LangSwarmBranchingTool(Tool):
    def __init__(self, agents, **kwargs):
        """
        Initializes the LangSwarmBranchingTool.

        Parameters:
        - agents (list): List of agents to use in the branching process.
        - kwargs: Additional parameters for the LLMBranching class.
        """
        self.branching = LLMBranching(clients=agents, **kwargs)
        super().__init__(
            name="LangSwarm Branching",
            func=self.run,
            description="A tool to generate multiple responses from a set of agents."
        )

    def run(self, query):
        """
        Executes the branching workflow with the given query.

        Parameters:
        - query (str): The query to process.

        Returns:
        - list: A list of responses from the agents.
        """
        self.branching.query = query
        return self.branching.run()
```

---

## **Key Components**

1. **`__init__` Method**
   - Initializes the tool with a list of agents and additional parameters.
   - Creates an instance of the `LLMBranching` class to manage the branching process.
   - Parameters:
     - `agents`: A list of LLM agents contributing to the branching process.
     - `kwargs`: Optional parameters passed to configure the `LLMBranching` class.
   - Inherits from the `Tool` class, defining the tool's name and description.

2. **`run` Method**
   - Executes the branching workflow.
   - Parameters:
     - `query`: The query string to be processed.
   - Workflow:
     - Assigns the query to the `LLMBranching` instance.
     - Calls the `run` method of `LLMBranching` to generate diverse responses.
   - Returns a list of responses from the agents.

---

## **Usage**

1. **Initialization**
   ```python
   from langswarm.swarm.branching import LLMBranching
   from mymodule import LangSwarmBranchingTool

   # Example list of agents (LLM clients)
   agents = [agent1, agent2, agent3]

   # Initialize the LangSwarmBranchingTool
   tool = LangSwarmBranchingTool(agents=agents, param1=value1, param2=value2)
   ```

2. **Execution**
   ```python
   # Input query
   query = "Provide different approaches to improve work-life balance."

   # Get the list of responses
   responses = tool.run(query)
   print("Responses:", responses)
   ```

3. **Integration with LangChain Workflows**
   - The `LangSwarmBranchingTool` can be directly used as a tool in LangChain workflows.
   ```python
   from langchain.agents import initialize_agent

   tools = [tool]
   agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

   # Run the agent with the tool
   result = agent.run("Suggest creative solutions for reducing traffic congestion.")
   print(result)
   ```

---

## **Customization**
- **Adding Custom Parameters**: Additional parameters can be passed to `LLMBranching` during initialization to customize the branching logic.
- **Extending the Tool**: Subclass `LangSwarmBranchingTool` to introduce additional functionality, such as filtering or post-processing of responses.

---

## **Use Cases**
1. **Creative Ideation**:
   - Generate multiple creative solutions or ideas for brainstorming.
2. **Exploring Diverse Perspectives**:
   - Obtain varied viewpoints or interpretations for open-ended questions.
3. **Scenario Analysis**:
   - Generate different hypothetical scenarios or approaches to a given problem.

---

## **Comparison with Other Tools**
- **LangSwarmBranchingTool**: Focuses on generating multiple diverse responses without merging or synthesizing them.
- **LangSwarmAggregationTool**: Merges and synthesizes responses into a single unified result.
- **LangSwarmVotingTool**: Selects the most popular or supported response among multiple agents.
