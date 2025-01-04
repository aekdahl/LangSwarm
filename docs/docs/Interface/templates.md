---
title: LangSwarmTemplates
sidebar_position: 800
---

# LangSwarmTemplates

---

## **Overview**
The `LangSwarmTemplates` class provides predefined templates for common workflows within LangSwarm, such as **consensus**, **voting**, **branching**, and **aggregation**. These templates simplify the implementation of workflows by abstracting boilerplate code and offering a high-level interface for interacting with LangSwarm modules.

Each template initializes the appropriate pipeline and processes the input query to produce the desired result, enabling plug-and-play functionality for developers.

---

## **Class Definition**

```python
class LangSwarmTemplates:
    """
    Predefined templates for common LangSwarm workflows.
    """

    @staticmethod
    def consensus_template(agents, query):
        """
        Predefined template for consensus workflow.

        Parameters:
        - agents (list): List of agents.
        - query (str): Query string.

        Returns:
        - str: Consensus result.
        """
        pipeline = LangSwarm.create_pipeline(workflow="consensus", agents=agents)
        return pipeline.run(query)

    @staticmethod
    def voting_template(agents, query):
        """
        Predefined template for voting workflow.

        Parameters:
        - agents (list): List of agents.
        - query (str): Query string.

        Returns:
        - tuple: Voting result, group size, and list of responses.
        """
        pipeline = LangSwarm.create_pipeline(workflow="voting", agents=agents)
        return pipeline.run(query)

    @staticmethod
    def branching_template(agents, query):
        """
        Predefined template for branching workflow.

        Parameters:
        - agents (list): List of agents.
        - query (str): Query string.

        Returns:
        - list: List of responses from the agents.
        """
        pipeline = LangSwarm.create_pipeline(workflow="branching", agents=agents)
        return pipeline.run(query)

    @staticmethod
    def aggregation_template(agents, query):
        """
        Predefined template for aggregation workflow.

        Parameters:
        - agents (list): List of agents.
        - query (str): Query string.

        Returns:
        - str: Aggregated result.
        """
        pipeline = LangSwarm.create_pipeline(workflow="aggregation", agents=agents)
        return pipeline.run(query)
```

---

## **Templates**

### **1. Consensus Template**
The **consensus template** achieves consensus among multiple agents by aggregating their responses into a unified output.

- **Parameters**:
  - `agents (list)`: List of agents contributing to the consensus process.
  - `query (str)`: The query string to be processed.

- **Returns**:
  - `str`: The consensus result.

- **Usage**:
  ```python
  from mymodule import LangSwarmTemplates

  agents = [AgentA(), AgentB(), AgentC()]
  result = LangSwarmTemplates.consensus_template(agents, "What are the benefits of AI?")
  print("Consensus Result:", result)
  ```

---

### **2. Voting Template**
The **voting template** enables decision-making by tallying responses from multiple agents and determining the most popular response.

- **Parameters**:
  - `agents (list)`: List of agents participating in the voting process.
  - `query (str)`: The query string to be processed.

- **Returns**:
  - `tuple`: A tuple containing:
    - `voting_result (str)`: The most popular response.
    - `group_size (int)`: The number of agents involved.
    - `responses (list)`: A list of all responses from the agents.

- **Usage**:
  ```python
  from mymodule import LangSwarmTemplates

  agents = [AgentA(), AgentB(), AgentC()]
  voting_result, group_size, responses = LangSwarmTemplates.voting_template(
      agents, "What is the best renewable energy source?"
  )
  print("Voting Result:", voting_result)
  print("Group Size:", group_size)
  print("Responses:", responses)
  ```

---

### **3. Branching Template**
The **branching template** generates diverse responses from multiple agents for a single query, enabling exploration of varied perspectives or ideas.

- **Parameters**:
  - `agents (list)`: List of agents contributing to the branching process.
  - `query (str)`: The query string to be processed.

- **Returns**:
  - `list`: A list of responses from the agents.

- **Usage**:
  ```python
  from mymodule import LangSwarmTemplates

  agents = [AgentA(), AgentB(), AgentC()]
  branching_results = LangSwarmTemplates.branching_template(
      agents, "Suggest creative business ideas in the tech industry."
  )
  print("Branching Results:", branching_results)
  ```

---

### **4. Aggregation Template**
The **aggregation template** merges responses from multiple agents into a single, cohesive result, synthesizing diverse inputs into a unified output.

- **Parameters**:
  - `agents (list)`: List of agents contributing to the aggregation process.
  - `query (str)`: The query string to be processed.

- **Returns**:
  - `str`: The aggregated result.

- **Usage**:
  ```python
  from mymodule import LangSwarmTemplates

  agents = [AgentA(), AgentB(), AgentC()]
  aggregated_result = LangSwarmTemplates.aggregation_template(
      agents, "Summarize the benefits of renewable energy."
  )
  print("Aggregated Result:", aggregated_result)
  ```

---

## **Benefits of Using Templates**

1. **Simplicity**:
   - Reduces boilerplate code and setup complexity by providing ready-to-use workflows.

2. **Reusability**:
   - Encourages modularity by abstracting common workflows into reusable templates.

3. **Customizability**:
   - Easily extended or modified for specific use cases by adding parameters or altering the workflow logic.

4. **Time-Saving**:
   - Developers can quickly integrate LangSwarm workflows into projects without needing in-depth knowledge of underlying modules.

---

## **Extensibility**
To add a new workflow template:
1. Implement the desired workflow in `LangSwarm.create_pipeline`.
2. Define a new static method in `LangSwarmTemplates` that calls `create_pipeline` with the appropriate parameters.

For example:
```python
@staticmethod
def new_template(agents, query, **kwargs):
    pipeline = LangSwarm.create_pipeline(workflow="new_workflow", agents=agents, **kwargs)
    return pipeline.run(query)
```
