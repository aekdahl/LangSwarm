---
title: LangSwarmConsensusTool
sidebar_position: 92
---

# LangSwarmConsensusTool

---

## **Overview**
The `LangSwarmConsensusTool` is a LangChain-compatible tool designed to achieve consensus among multiple Large Language Model (LLM) agents for a given query. It uses the `LLMConsensus` class to aggregate opinions, reconcile differences, and produce a unified, consensus-driven result.

---

## **Purpose**
The primary purpose of the `LangSwarmConsensusTool` is:
- **Consensus Building**: To enable developers to use consensus-building as a modular step in LangChain workflows.
- **Pipeline Integration**: To seamlessly integrate consensus mechanisms into broader LangChain pipelines.
- **Flexibility**: To allow configuration of the consensus-building process through additional parameters.

---

## **Class Definition**

```python
class LangSwarmConsensusTool(Tool):
    def __init__(self, agents, **kwargs):
        """
        Initializes the LangSwarmConsensusTool.

        Parameters:
        - agents (list): List of agents to use in the consensus process.
        - kwargs: Additional parameters for the LLMConsensus class.
        """
        self.consensus = LLMConsensus(clients=agents, **kwargs)
        super().__init__(
            name="LangSwarm Consensus",
            func=self.run,
            description="A tool to reach consensus among multiple agents for a given query."
        )

    def run(self, query):
        """
        Executes the consensus workflow with the given query.

        Parameters:
        - query (str): The query to process.

        Returns:
        - str: The consensus result.
        """
        self.consensus.query = query
        return self.consensus.run()
```

---

## **Key Components**

1. **`__init__` Method**
   - Initializes the tool with a list of agents and additional parameters.
   - Creates an instance of the `LLMConsensus` class to manage the consensus-building process.
   - Parameters:
     - `agents`: A list of LLM agents contributing to the consensus process.
     - `kwargs`: Optional parameters passed to configure the `LLMConsensus` class.
   - Inherits from the `Tool` class, defining the tool's name and description.

2. **`run` Method**
   - Executes the consensus workflow.
   - Parameters:
     - `query`: The query string to be processed.
   - Workflow:
     - Assigns the query to the `LLMConsensus` instance.
     - Calls the `run` method of `LLMConsensus` to generate a consensus result.
   - Returns the consensus result as a string.

---

## **Usage**

1. **Initialization**
   ```python
   from langswarm.swarm.consensus import LLMConsensus
   from mymodule import LangSwarmConsensusTool

   # Example list of agents (LLM clients)
   agents = [agent1, agent2, agent3]

   # Initialize the LangSwarmConsensusTool
   tool = LangSwarmConsensusTool(agents=agents, param1=value1, param2=value2)
   ```

2. **Execution**
   ```python
   # Input query
   query = "What is the most important factor for economic growth?"

   # Get the consensus result
   result = tool.run(query)
   print("Consensus Result:", result)
   ```

3. **Integration with LangChain Workflows**
   - The `LangSwarmConsensusTool` can be directly used as a tool in LangChain workflows.
   ```python
   from langchain.agents import initialize_agent

   tools = [tool]
   agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

   # Run the agent with the tool
   result = agent.run("How should we prioritize renewable energy policies?")
   print(result)
   ```

---

## **Customization**
- **Adding Custom Parameters**: Additional parameters can be passed to `LLMConsensus` during initialization to customize the consensus logic.
- **Extending the Tool**: Subclass `LangSwarmConsensusTool` to add functionality such as pre- or post-processing of results or adapting the consensus logic for specific use cases.

---

## **Use Cases**
1. **Decision Making**:
   - Use consensus to determine the most supported solution among multiple agents.
2. **Validation**:
   - Verify the accuracy or agreement of responses from multiple agents before presenting a result.
3. **Conflict Resolution**:
   - Resolve differing outputs by finding the most consistent or agreed-upon response.
4. **Collaborative Problem-Solving**:
   - Aggregate insights from diverse agents to tackle complex problems.

---

## **Comparison with Other Tools**
- **LangSwarmConsensusTool**: Focuses on achieving a unified result through consensus among agents.
- **LangSwarmBranchingTool**: Generates diverse responses without necessarily reconciling them into a single output.
- **LangSwarmAggregationTool**: Merges responses into a cohesive output, but without requiring strict agreement or consensus.
