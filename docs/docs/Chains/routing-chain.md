---
title: RoutingChain
sidebar_position: 33
---

# RoutingChain

---

## **Overview**
The `RoutingChain` class is a custom, LangChain-compatible chain designed to dynamically route tasks to the most appropriate agents or workflows based on predefined routing logic. It leverages the `LLMRouting` class to manage task distribution, enabling efficient handling of diverse queries within a LangChain pipeline.

This chain is particularly useful for workflows that require decisions about which agent or workflow is best suited to process a given task.

---

## **Purpose**
The primary purpose of the `RoutingChain` class is:
- **Dynamic Task Routing**: To intelligently route queries or tasks to the appropriate agents or workflows.
- **Pipeline Integration**: To act as a reusable chain within LangChain workflows, facilitating seamless interaction with other tools or agents.
- **Customization**: To allow flexibility in defining routing logic and configuring the chain for specific use cases.

---

## **Class Definition**

```python
class RoutingChain(Chain):
    def __init__(self, route, bots, main_bot, **kwargs):
        """
        Initializes the RoutingChain.

        Parameters:
        - route (int): The routing logic to apply.
        - bots (dict): Dictionary of bots to route tasks.
        - main_bot: The primary bot for routing decisions.
        - kwargs: Additional parameters for the LLMRouting class.
        """
        self.routing = LLMRouting(route=route, bots=bots, main_bot=main_bot, **kwargs)

    @property
    def input_keys(self):
        """Define input keys for the chain."""
        return ["query"]

    @property
    def output_keys(self):
        """Define output keys for the chain."""
        return ["routed_result"]

    def _call(self, inputs):
        """
        Processes the input query and returns the routed result.

        Parameters:
        - inputs (dict): Dictionary containing the query.

        Returns:
        - dict: Dictionary containing the routed result.
        """
        query = inputs["query"]
        self.routing.query = query
        result = self.routing.run()
        return {"routed_result": result}
```

---

## **Key Components**

1. **`__init__` Method**
   - Initializes the chain with routing logic, a dictionary of bots, and a primary bot for decision-making.
   - Parameters:
     - `route`: Integer defining the routing logic to use.
     - `bots`: A dictionary mapping bot identifiers to their respective instances.
     - `main_bot`: The primary bot responsible for making routing decisions.
     - `kwargs`: Optional parameters passed to configure the `LLMRouting` class.

2. **`input_keys` Property**
   - Specifies the input keys required by the chain.
   - Inputs:
     - `query`: The user query to be routed to an appropriate agent or workflow.

3. **`output_keys` Property**
   - Specifies the output keys returned by the chain.
   - Outputs:
     - `routed_result`: The result of the routed task.

4. **`_call` Method**
   - Core logic for executing the chain.
   - Workflow:
     - Accepts a `query` input.
     - Assigns the `query` to the `LLMRouting` instance.
     - Calls the `run` method of `LLMRouting` to route the query and obtain the result.
     - Returns the routed result as a dictionary.

---

## **Usage**

1. **Initialization**
   ```python
   from langswarm.swarm.routing import LLMRouting
   from mymodule import RoutingChain

   # Define bots and routing logic
   bots = {
       "bot1": agent1,
       "bot2": agent2,
       "bot3": agent3,
   }
   main_bot = central_decision_maker

   # Initialize the RoutingChain
   chain = RoutingChain(route=1, bots=bots, main_bot=main_bot, param1=value1)
   ```

2. **Execution**
   ```python
   # Input data
   inputs = {
       "query": "What is the weather forecast for tomorrow in New York?",
   }

   # Get the routed result
   result = chain(inputs)
   print("Routed Result:", result["routed_result"])
   ```

3. **Integration with LangChain Pipelines**
   - The `RoutingChain` can be integrated into LangChain workflows as a standalone chain or in combination with other chains and tools.
   ```python
   from langchain.chains import SequentialChain

   # Example pipeline
   pipeline = SequentialChain(chains=[chain, another_chain])
   pipeline.run(inputs)
   ```

---

## **Customization**
- **Custom Routing Logic**: Modify the `route` parameter or extend the `LLMRouting` class to define more sophisticated routing strategies.
- **Dynamic Bots**: Update the `bots` dictionary dynamically to add or remove agents based on task requirements.
- **Extending the Chain**: Subclass `RoutingChain` to customize the `_call` method or introduce additional input and output keys.

---

## **Use Cases**
1. **Task Specialization**:
   - Route queries to agents specialized in different domains (e.g., weather, finance, or healthcare).
2. **Workflow Optimization**:
   - Dynamically assign tasks to agents based on workload or performance metrics.
3. **Context-Aware Decisions**:
   - Use the primary bot (`main_bot`) to analyze the context and make routing decisions.
4. **Load Balancing**:
   - Distribute tasks across multiple agents to ensure even workload distribution.

---

## **Comparison with Other Chains**
- **RoutingChain**: Dynamically routes queries to specific agents or workflows based on predefined logic.
- **VotingChain**: Aggregates multiple responses and determines the result based on a voting mechanism.
- **BranchingChain**: Generates multiple diverse responses without routing queries to specific agents.

---

This documentation provides a detailed explanation of the `RoutingChain` class, including its purpose, structure, and usage. Let me know if you’d like further clarifications or refinements!
