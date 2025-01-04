---
title: Dynamic Routing
sidebar_position: 4
---

# Dynamic Routing

## **Overview**

The **LLMRouting** class in LangSwarm dynamically routes queries to specific workflows or agents based on predefined routes. It allows users to select different strategies, such as branching, voting, or consensus, for handling a query. This flexibility makes it an excellent tool for managing complex multi-agent workflows and adapting workflows based on the nature of the input.

---

## **Key Features**

1. **Dynamic Routing**:  
   Routes queries to specific workflows (e.g., branching, voting, consensus) based on predefined routes.

2. **Workflow Flexibility**:  
   Supports different processing strategies tailored to various use cases.

3. **Multi-Agent Support**:  
   Works with LangChain, Hugging Face, OpenAI, or custom agents via the `AgentWrapper`.

4. **LangChain-Compatible**:  
   Easily integrates into LangChain pipelines for seamless workflows.

---

## **API Reference**

### **Class: `LLMRouting`**

Routes queries to predefined workflows dynamically.

#### **Initialization**

```python
LLMRouting(route, bots, main_bot, query, remove_chat=False, verbose=False)
```

| Parameter      | Type    | Description                                                                 |
|----------------|---------|-----------------------------------------------------------------------------|
| `route`        | `int`   | The route to be executed (e.g., `0` for regular processing, `1` for branching). |
| `bots`         | `list`  | A list of agents participating in the workflow.                            |
| `main_bot`     | `object`| The primary agent for fallback or certain workflows.                       |
| `query`        | `str`   | The input query to be routed.                                              |
| `remove_chat`  | `bool`  | If `True`, removes queries from memory after processing. Default is `False`.|
| `verbose`      | `bool`  | If `True`, enables detailed logging. Default is `False`.                   |

---

### **Methods**

#### **`run()`**

Executes the specified route, processing the query and returning the output.

**Returns**:  
- `str`: The response from the selected workflow or agent.

---

## **Routing Options**

| Route | Description                                                                 |
|-------|-----------------------------------------------------------------------------|
| `0`   | Regular processing by the `main_bot`.                                       |
| `1`   | Branching: Uses multiple agents to generate diverse outputs.                |
| `2`   | Voting: Selects the best response based on votes from multiple agents.      |
| `3`   | Prompt Reformulation: Reformulates the query before processing it.          |
| `4`   | Inline Prompting: Converts remarks into inline prompts before processing.   |

---

## **Examples**

### **Basic Example**

```python
from langswarm.swarm import LLMRouting
from langswarm.wrappers import AgentWrapper
from langchain.llms import OpenAI

# Step 1: Create and wrap agents
agent1 = AgentWrapper(agent=OpenAI(model="gpt-4"), is_conversational=True)
agent2 = AgentWrapper(agent=OpenAI(model="gpt-3.5-turbo"), is_conversational=True)

# Step 2: Initialize LLMRouting with the agents
query = "How can AI improve healthcare?"
routing_swarm = LLMRouting(route=2, bots=[agent1, agent2], main_bot=agent1, query=query, verbose=True)

# Step 3: Run the routing workflow
response = routing_swarm.run()

# Display the results
print("Routed Response:", response)
```

---

### **Advanced Example: Dynamic Routing with Prompt Reformulation**

```python
from langswarm.swarm import LLMRouting
from langswarm.wrappers import AgentWrapper
from transformers import pipeline

# Step 1: Create and wrap agents
huggingface_agent = AgentWrapper(agent=pipeline("text-generation", model="gpt2"), is_conversational=False)
openai_agent = AgentWrapper(agent="openai_gpt3", is_conversational=True)  # Assuming an OpenAI agent wrapper

# Step 2: Initialize LLMRouting with reformulation route
query = "Explain how blockchain technology works."
routing_swarm = LLMRouting(route=3, bots=[huggingface_agent, openai_agent], main_bot=openai_agent, query=query)

# Step 3: Run the routing workflow
response = routing_swarm.run()

# Display the results
print("Reformulated Response:", response)
```

---

## **How It Works**

1. **Select Route**:  
   Based on the `route` parameter, LLMRouting determines which workflow to execute.

2. **Process Query**:  
   The query is processed using the selected workflow or agent(s).

3. **Return Response**:  
   The result of the selected workflow is returned to the user.

---

## **Best Practices**

1. **Choose Routes Strategically**:  
   Select appropriate routes based on the nature of the query and desired output.

2. **Enable Verbose Mode**:  
   Use `verbose=True` during development to understand how queries are routed and processed.

3. **Combine with Other Tools**:  
   Use LLMRouting in conjunction with tools like `LLMConsensus` or `LLMAggregation` for advanced workflows.

---

## **Use Cases**

1. **Dynamic Query Handling**:  
   Route queries to different workflows based on input type or requirements.

2. **Adaptive Workflows**:  
   Adjust workflows dynamically for complex use cases like brainstorming or decision-making.

3. **Query Reformulation**:  
   Improve query clarity and precision with reformulation and inline prompting.

---

## **Key Advantages**

- **Dynamic and Flexible**:  
  Adapts workflows to suit diverse query requirements.

- **Workflow Integration**:  
  Seamlessly integrates with other LangSwarm tools and LangChain pipelines.

- **Simplified Multi-Agent Management**:  
  Provides a unified interface for handling multiple workflows.

---

## **Future Enhancements**

1. **Route Recommendations**:  
   Automatically recommend optimal routes based on query analysis.

2. **Custom Route Logic**:  
   Allow users to define custom routes and workflows.

3. **Advanced Analytics**:  
   Provide detailed analytics on routing decisions and outcomes.

---

The **LLMRouting** class is a versatile tool for managing dynamic workflows in multi-agent systems. By enabling flexible routing of queries, LangSwarm ensures adaptability and efficiency in handling diverse AI tasks.
