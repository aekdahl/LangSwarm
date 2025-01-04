---
title: LangSwarmRoutingTool
sidebar_position: 93
---

# Documentation for `LangSwarmRoutingTool` Class

---

## **Overview**
The `LangSwarmRoutingTool` is a LangChain-compatible tool designed to dynamically route tasks to the most appropriate agents or workflows based on predefined routing logic. By leveraging the `LLMRouting` class, it enables efficient task delegation, ensuring that queries are processed by the best-suited agent or workflow.

---

## **Purpose**
The primary purpose of the `LangSwarmRoutingTool` is:
- **Dynamic Task Routing**: To intelligently route tasks to the appropriate agents or workflows based on routing logic.
- **Pipeline Integration**: To serve as a dynamic routing tool within LangChain workflows, enabling modular and efficient task delegation.
- **Customizability**: To allow developers to define and customize routing logic for diverse use cases.

---

## **Class Definition**

```python
class LangSwarmRoutingTool(Tool):
    def __init__(self, route, bots, main_bot, **kwargs):
        """
        Initializes the LangSwarmRoutingTool.

        Parameters:
        - route (int): The routing logic to apply.
        - bots (dict): Dictionary of bots to route tasks.
        - main_bot: The primary bot for routing decisions.
        - kwargs: Additional parameters for the LLMRouting class.
        """
        self.routing = LLMRouting(route=route, bots=bots, main_bot=main_bot, **kwargs)
        super().__init__(
            name="LangSwarm Routing",
            func=self.run,
            description="A tool to dynamically route tasks to the appropriate agents."
        )

    def run(self, query):
        """
        Executes the routing workflow with the given query.

        Parameters:
        - query (str): The query to process.

        Returns:
        - str: The result from the routed agent.
        """
        self.routing.query = query
        return self.routing.run()
```

---

## **Key Components**

1. **`__init__` Method**
   - Initializes the tool with routing logic, a dictionary of bots, and a primary bot for decision-making.
   - Parameters:
     - `route`: Integer defining the routing logic to apply.
     - `bots`: A dictionary mapping bot identifiers to their respective instances.
     - `main_bot`: The primary bot responsible for making routing decisions.
     - `kwargs`: Optional parameters passed to configure the `LLMRouting` class.
   - Inherits from the `Tool` class, defining the tool's name and description.

2. **`run` Method**
   - Executes the routing workflow.
   - Parameters:
     - `query`: The query string to be processed.
   - Workflow:
     - Assigns the query to the `LLMRouting` instance.
     - Calls the `run` method of `LLMRouting` to route the query to the appropriate agent or workflow.
   - Returns the result from the routed agent.

---

## **Usage**

1. **Initialization**
   ```python
   from langswarm.swarm.routing import LLMRouting
   from mymodule import LangSwarmRoutingTool

   # Define bots and routing logic
   bots = {
       "bot1": agent1,
       "bot2": agent2,
       "bot3": agent3,
   }
   main_bot = central_decision_maker

   # Initialize the LangSwarmRoutingTool
   tool = LangSwarmRoutingTool(route=1, bots=bots, main_bot=main_bot, param1=value1)
   ```

2. **Execution**
   ```python
   # Input query
   query = "What is the best approach for starting a small business?"

   # Get the result from the routed agent
   result = tool.run(query)
   print("Routed Result:", result)
   ```

3. **Integration with LangChain Workflows**
   - The `LangSwarmRoutingTool` can be directly used as a tool in LangChain workflows.
   ```python
   from langchain.agents import initialize_agent

   tools = [tool]
   agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

   # Run the agent with the tool
   result = agent.run("How do I calculate the ROI for my startup?")
   print(result)
   ```

---

## **Customization**
- **Custom Routing Logic**: Modify the `route` parameter or extend the `LLMRouting` class to define more advanced routing strategies.
- **Dynamic Bots**: The `bots` dictionary can be updated dynamically to add or remove agents based on task requirements.
- **Extending the Tool**: Subclass `LangSwarmRoutingTool` to add pre- or post-processing logic for the routed tasks.

---

## **Use Cases**
1. **Domain-Specific Task Assignment**:
   - Route queries to agents specialized in different domains (e.g., legal, technical, or financial queries).
2. **Workflow Optimization**:
   - Delegate tasks to agents or workflows based on efficiency, capacity, or expertise.
3. **Context-Aware Routing**:
   - Use the `main_bot` to analyze the query context and make intelligent routing decisions.
4. **Load Balancing**:
   - Distribute tasks across multiple agents to balance workloads and prevent bottlenecks.

---

## **Comparison with Other Tools**
- **LangSwarmRoutingTool**: Dynamically routes tasks to specific agents or workflows based on routing logic.
- **LangSwarmConsensusTool**: Aggregates responses from multiple agents to produce a consensus-driven result.
- **LangSwarmBranchingTool**: Generates diverse responses from multiple agents without routing tasks.
- **LangSwarmAggregationTool**: Merges responses into a unified result without requiring routing.
