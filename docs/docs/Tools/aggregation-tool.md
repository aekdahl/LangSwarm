---
title: LangSwarmAggregationTool
sidebar_position: 90
---

# LangSwarmAggregationTool

---

## **Overview**
The `LangSwarmAggregationTool` is a LangChain-compatible tool designed to merge and aggregate responses from multiple Large Language Model (LLM) agents. It uses the `LLMAggregation` class to synthesize diverse responses into a unified output, making it a valuable component for workflows that require consensus or synthesis of information from multiple agents.

---

## **Purpose**
The primary purpose of the `LangSwarmAggregationTool` is:
- **Response Aggregation**: To collect, merge, and aggregate responses from multiple agents into a cohesive output.
- **Pipeline Integration**: To provide a reusable tool within LangChain workflows, enabling smooth integration into broader pipelines.
- **Customization**: To allow flexible configuration of the aggregation process using additional parameters.

---

## **Class Definition**

```python
class LangSwarmAggregationTool(Tool):
    def __init__(self, agents, **kwargs):
        """
        Initializes the LangSwarmAggregationTool.

        Parameters:
        - agents (list): List of agents to use in the aggregation process.
        - kwargs: Additional parameters for the LLMAggregation class.
        """
        self.aggregation = LLMAggregation(clients=agents, **kwargs)
        super().__init__(
            name="LangSwarm Aggregation",
            func=self.run,
            description="A tool to merge and aggregate responses from multiple agents."
        )

    def run(self, query, hb):
        """
        Executes the aggregation workflow with the given query.

        Parameters:
        - query (str): The query to process.
        - hb: Additional aggregation handler, if required.

        Returns:
        - str: The aggregated result.
        """
        self.aggregation.query = query
        return self.aggregation.run(hb)
```

---

## **Key Components**

1. **`__init__` Method**
   - Initializes the tool with a list of agents and additional parameters.
   - Creates an instance of the `LLMAggregation` class to manage the aggregation process.
   - Parameters:
     - `agents`: A list of LLM agents contributing to the aggregation process.
     - `kwargs`: Optional parameters passed to configure the `LLMAggregation` class.
   - Inherits from the `Tool` class, defining the tool's name and description.

2. **`run` Method**
   - Executes the aggregation workflow.
   - Parameters:
     - `query`: The query string to be processed.
     - `hb`: An additional handler (if required) for the aggregation process.
   - Workflow:
     - Assigns the query to the `LLMAggregation` instance.
     - Calls the `run` method of `LLMAggregation` to generate the aggregated result.
   - Returns the aggregated result as a string.

---

## **Usage**

1. **Initialization**
   ```python
   from langswarm.swarm.aggregation import LLMAggregation
   from mymodule import LangSwarmAggregationTool

   # Example list of agents (LLM clients)
   agents = [agent1, agent2, agent3]

   # Initialize the LangSwarmAggregationTool
   tool = LangSwarmAggregationTool(agents=agents, param1=value1, param2=value2)
   ```

2. **Execution**
   ```python
   # Input query and handler
   query = "Summarize the advantages of renewable energy."
   handler = some_handler_object

   # Get the aggregated result
   result = tool.run(query, handler)
   print("Aggregated Result:", result)
   ```

3. **Integration with LangChain Workflows**
   - The `LangSwarmAggregationTool` can be directly used as a tool in LangChain workflows.
   ```python
   from langchain.agents import initialize_agent

   tools = [tool]
   agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

   # Run the agent with the tool
   result = agent.run("Summarize the benefits of AI in education.")
   print(result)
   ```

---

## **Customization**
- **Adding Custom Parameters**: Additional parameters can be passed to `LLMAggregation` during initialization to customize the aggregation logic.
- **Extending the Tool**: Subclass `LangSwarmAggregationTool` to introduce additional functionality, such as pre- or post-processing of responses.

---

## **Use Cases**
1. **Consensus Building**:
   - Aggregate responses from multiple agents to derive a consensus-driven answer.
2. **Data Synthesis**:
   - Merge diverse information from different agents into a single cohesive output.
3. **Summarization**:
   - Generate summaries by aggregating multiple perspectives on a given topic.

---

## **Comparison with Other Tools**
- **LangSwarmAggregationTool**: Focuses on merging and synthesizing responses into a unified output.
- **BranchingChain**: Explores diverse responses without merging them into a single result.
- **VotingChain**: Selects the most popular response among agents based on a voting mechanism.
