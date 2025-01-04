---
title: ConsensusChain
sidebar_position: 32
---

# ConsensusChain

---

## **Overview**
The `ConsensusChain` class is a custom, LangChain-compatible chain designed to facilitate consensus-building among multiple Large Language Model (LLM) agents. It integrates seamlessly into LangChain workflows, leveraging the `LLMConsensus` class to determine the most agreed-upon response from multiple agents.

This chain is particularly useful in scenarios where multiple agents provide diverse responses, and a unified, consensus-driven answer is required.

---

## **Purpose**
The primary purpose of the `ConsensusChain` class is:
- **Consensus-Building**: To determine a single, consensus-driven output from multiple LLM agents.
- **Pipeline Integration**: To act as a reusable chain within LangChain pipelines, enabling smooth integration with other chains, tools, or agents.
- **Flexibility**: To allow customization of the consensus-building process through configurable parameters.

---

## **Class Definition**

```python
class ConsensusChain(Chain):
    def __init__(self, agents, **kwargs):
        """
        Initializes the ConsensusChain.

        Parameters:
        - agents (list): List of agents to use in the consensus process.
        - kwargs: Additional parameters for the LLMConsensus class.
        """
        self.consensus = LLMConsensus(clients=agents, **kwargs)

    @property
    def input_keys(self):
        """Define input keys for the chain."""
        return ["query"]

    @property
    def output_keys(self):
        """Define output keys for the chain."""
        return ["consensus_result"]

    def _call(self, inputs):
        """
        Processes the input query and returns the consensus result.

        Parameters:
        - inputs (dict): Dictionary containing the query.

        Returns:
        - dict: Dictionary containing the consensus result.
        """
        query = inputs["query"]
        self.consensus.query = query
        result = self.consensus.run()
        return {"consensus_result": result}
```

---

## **Key Components**

1. **`__init__` Method**
   - Initializes the chain with a list of agents and additional parameters.
   - Creates an instance of the `LLMConsensus` class to handle consensus-building.
   - Parameters:
     - `agents`: A list of LLM agents contributing to the consensus process.
     - `kwargs`: Optional parameters passed to configure the `LLMConsensus` class.

2. **`input_keys` Property**
   - Specifies the input keys required by the chain.
   - Inputs:
     - `query`: The user query or task to be resolved through consensus.

3. **`output_keys` Property**
   - Specifies the output key returned by the chain.
   - Outputs:
     - `consensus_result`: The final result agreed upon by the agents.

4. **`_call` Method**
   - Core logic for executing the chain.
   - Workflow:
     - Accepts a `query` input.
     - Assigns the `query` to the `LLMConsensus` instance.
     - Calls the `run` method of `LLMConsensus` to compute the consensus result.
     - Returns the consensus result as a dictionary.

---

## **Usage**

1. **Initialization**
   ```python
   from langswarm.swarm.consensus import LLMConsensus
   from mymodule import ConsensusChain

   # Example list of agents (LLM clients)
   agents = [agent1, agent2, agent3]

   # Initialize the ConsensusChain
   chain = ConsensusChain(agents=agents, param1=value1, param2=value2)
   ```

2. **Execution**
   ```python
   # Input data
   inputs = {
       "query": "What is the best programming language for web development?",
   }

   # Get the consensus result
   result = chain(inputs)
   print(result["consensus_result"])
   ```

3. **Integration with LangChain Pipelines**
   - The `ConsensusChain` can be integrated into LangChain workflows as a standalone chain or in combination with other chains and tools.
   ```python
   from langchain.chains import SequentialChain

   # Example pipeline
   pipeline = SequentialChain(chains=[chain, another_chain])
   pipeline.run(inputs)
   ```

---

## **Customization**
- **Adding Custom Parameters**: Pass additional parameters to `LLMConsensus` via the `kwargs` argument when initializing the chain.
- **Extending the Chain**: Subclass `ConsensusChain` to override methods like `_call` or introduce new logic.

---

## **Use Cases**
1. **Validation of LLM Outputs**:
   - Achieve consensus among multiple agents to validate the correctness of answers.
2. **Bias Reduction**:
   - Aggregate diverse perspectives from different agents to mitigate individual biases.
3. **Decision-Making**:
   - Resolve conflicting outputs by finding the most agreed-upon response.

---

## **Comparison with `AggregationChain`**
While both `ConsensusChain` and `AggregationChain` process outputs from multiple agents:
- **AggregationChain**: Merges and synthesizes diverse responses into a single, coherent result.
- **ConsensusChain**: Focuses on finding agreement among agents to determine a unified response.

---

This documentation provides detailed insights into the purpose, structure, and usage of the `ConsensusChain` class. Let me know if you'd like to elaborate further on any aspect!
