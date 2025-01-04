---
title: AggregationChain
sidebar_position: 30
---

# AggregationChain

---

## **Overview**
The `AggregationChain` class is a custom, LangChain-compatible chain designed to facilitate response aggregation from multiple Large Language Model (LLM) agents. It integrates with LangChain's ecosystem and uses the `LLMAggregation` class for merging and synthesizing responses.

This class is suitable for scenarios where multiple LLM agents contribute responses, and a unified or aggregated result is needed. The `AggregationChain` can be seamlessly integrated into complex pipelines involving other tools or agents.

---

## **Purpose**
The primary purpose of the `AggregationChain` class is:
- **Aggregation Workflows**: To aggregate and synthesize responses from multiple LLM agents.
- **Pipeline Integration**: To act as a reusable chain within LangChain pipelines, enabling smooth interoperability with other chains, tools, or agents.
- **Customization**: To allow flexible configurations of the aggregation process through additional parameters.

---

## **Class Definition**

```python
class AggregationChain(Chain):
    def __init__(self, agents, **kwargs):
        """
        Initializes the AggregationChain.

        Parameters:
        - agents (list): List of agents to use in the aggregation process.
        - kwargs: Additional parameters for the LLMAggregation class.
        """
        self.aggregation = LLMAggregation(clients=agents, **kwargs)

    @property
    def input_keys(self):
        """Define input keys for the chain."""
        return ["query", "hb"]

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
        hb = inputs["hb"]
        self.aggregation.query = query
        result = self.aggregation.run(hb)
        return {"aggregated_result": result}
```

---

## **Key Components**

1. **`__init__` Method**
   - Initializes the chain with a list of agents and additional parameters.
   - Creates an instance of the `LLMAggregation` class to handle the aggregation process.
   - Parameters:
     - `agents`: A list of LLM agents used for aggregation.
     - `kwargs`: Optional parameters passed to configure the `LLMAggregation` class.

2. **`input_keys` Property**
   - Specifies the input keys required by the chain.
   - Inputs:
     - `query`: The user query or task to be processed.
     - `hb`: Handler or additional parameter used during the aggregation process.

3. **`output_keys` Property**
   - Specifies the output key returned by the chain.
   - Outputs:
     - `aggregated_result`: The synthesized result from multiple agents.

4. **`_call` Method**
   - Core logic for executing the chain.
   - Workflow:
     - Accepts `query` and `hb` as inputs.
     - Assigns the `query` to the `LLMAggregation` instance.
     - Calls the `run` method of `LLMAggregation` to generate the aggregated result.
     - Returns the aggregated result as a dictionary.

---

## **Usage**

1. **Initialization**
   ```python
   from langswarm.swarm.aggregation import LLMAggregation
   from mymodule import AggregationChain

   # Example list of agents (LLM clients)
   agents = [agent1, agent2, agent3]

   # Initialize the AggregationChain
   chain = AggregationChain(agents=agents, param1=value1, param2=value2)
   ```

2. **Execution**
   ```python
   # Input data
   inputs = {
       "query": "What are the benefits of renewable energy?",
       "hb": some_handler_object,
   }

   # Get the aggregated result
   result = chain(inputs)
   print(result["aggregated_result"])
   ```

3. **Integration with LangChain Pipelines**
   - The `AggregationChain` can be integrated into LangChain workflows as a standalone chain or in combination with other chains and tools.
   ```python
   from langchain.chains import SequentialChain

   # Example pipeline
   pipeline = SequentialChain(chains=[chain, another_chain])
   pipeline.run(inputs)
   ```

---

## **Customization**
- **Adding Custom Parameters**: You can pass additional parameters to `LLMAggregation` via the `kwargs` argument when initializing the chain.
- **Extending the Chain**: Subclass `AggregationChain` to override methods like `_call` or introduce new logic.

---

## **Use Cases**
1. **Consensus and Review**:
   - Aggregate opinions or insights from multiple LLMs to derive a consensus-based response.
2. **Data Synthesis**:
   - Combine and refine data or outputs from multiple sources.
3. **Toolchain Integration**:
   - Use as part of a broader workflow where aggregation of results is required.

---

This documentation provides a detailed understanding of the purpose, structure, and usage of the `AggregationChain` class. Let me know if you'd like to enhance or tailor it further!
