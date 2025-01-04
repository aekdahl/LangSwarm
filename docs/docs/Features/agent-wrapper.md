---
title: AgentWrapper
sidebar_position: 68
---

# **AgentWrapper**

## **Overview**

The **AgentWrapper** in LangSwarm enables seamless integration of diverse agents (e.g., LangChain, Hugging Face, OpenAI) into LangSwarm workflows. It dynamically adapts agents to make them compatible with LangSwarm’s features such as `LLMConsensus`, `LLMAggregation`, `LLMBranching`, and more.

With the `AgentWrapper`, you can:
- Add LangSwarm functionality to native LangChain or Hugging Face agents.
- Manage conversational context and memory.
- Ensure agents are compatible with LangSwarm’s multi-agent orchestration tools.

---

## **Key Features**

1. **Dynamic Compatibility**: Adapts LangChain, Hugging Face, OpenAI, or custom agents to LangSwarm workflows.
2. **Conversational Context**: Handles history and memory for agents that support conversational queries.
3. **Simplified API**: Provides a unified interface to interact with different types of agents.
4. **Customizable**: Extensible for unsupported agent types or additional features.

---

## **API Reference**

### **Class: `AgentWrapper`**

Wraps an agent to make it compatible with LangSwarm workflows.

#### **Initialization**

```python
AgentWrapper(agent, is_conversational=False, **kwargs)
```

| Parameter          | Type     | Description                                                                 |
|--------------------|----------|-----------------------------------------------------------------------------|
| `agent`            | `object` | The agent to be wrapped (LangChain, Hugging Face, OpenAI, or custom).       |
| `is_conversational`| `bool`   | Specifies if the agent supports conversational context.                     |
| `kwargs`           | `dict`   | Additional parameters for LangSwarm compatibility.                         |

---

### **Methods**

#### **`chat(q, reset=False, erase_query=False, remove_linebreaks=False)`**

Processes a query through the wrapped agent.

| Parameter         | Type     | Description                                                                 |
|-------------------|----------|-----------------------------------------------------------------------------|
| `q`               | `str`    | The query to be processed.                                                  |
| `reset`           | `bool`   | If `True`, resets the memory before processing the query.                   |
| `erase_query`     | `bool`   | If `True`, erases the query after processing.                               |
| `remove_linebreaks`| `bool`  | If `True`, removes line breaks from the query.                              |

**Returns**:  
- `str`: The agent’s response.

---

#### **`__getattr__(name)`**

Delegates attribute access to the wrapped agent.

**Usage**:  
Allows seamless access to the wrapped agent’s native methods and properties.

---

## **Examples**

### **Wrapping a LangChain Agent**

```python
from langchain.llms import OpenAI
from langswarm.wrappers import AgentWrapper

# Create a native LangChain agent
langchain_agent = OpenAI(model="gpt-4", temperature=0)

# Wrap the agent for LangSwarm compatibility
wrapped_agent = AgentWrapper(agent=langchain_agent, is_conversational=True)

# Use the wrapped agent in LangSwarm workflows
response = wrapped_agent.chat("What are the main benefits of AI?")
print("Response:", response)
```

---

### **Wrapping a Hugging Face Model**

```python
from transformers import pipeline
from langswarm.wrappers import AgentWrapper

# Load a Hugging Face QA pipeline
huggingface_agent = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

# Wrap the agent for LangSwarm compatibility
wrapped_agent = AgentWrapper(agent=huggingface_agent, is_conversational=False)

# Use the wrapped agent in LangSwarm workflows
response = wrapped_agent.chat("What is the capital of France?")
print("Response:", response)
```

---

### **Using a Wrapped Agent in a LangSwarm Workflow**

```python
from langswarm.swarm import LLMConsensus
from langswarm.wrappers import AgentWrapper
from langchain.llms import OpenAI

# Create and wrap agents
agent1 = AgentWrapper(agent=OpenAI(model="gpt-4"), is_conversational=True)
agent2 = AgentWrapper(agent=OpenAI(model="gpt-3.5-turbo"), is_conversational=True)

# Use wrapped agents in a LangSwarm consensus workflow
consensus_swarm = LLMConsensus(query="What are the benefits of renewable energy?", clients=[agent1, agent2])
response = consensus_swarm.run()
print("Consensus Response:", response)
```

---

## **Advanced Use Cases**

### **Accessing Native Agent Features**
The `AgentWrapper` allows direct access to the wrapped agent’s native methods.

```python
# Access the wrapped agent's native methods
agent_temperature = wrapped_agent.agent.temperature
print("Temperature Setting:", agent_temperature)
```

### **Managing Conversational Context**
The `AgentWrapper` seamlessly manages conversational history for supported agents.

```python
# Enable conversational context
conversation_agent = AgentWrapper(agent=OpenAI(model="gpt-4"), is_conversational=True)

# Send queries and maintain context
conversation_agent.chat("What is the weather like today?")
conversation_agent.chat("How about tomorrow?")
```

---

## **Best Practices**

1. **Use `is_conversational` Appropriately**:
   - Set `is_conversational=True` for agents with memory or conversational context.
   
2. **Delegate Custom Logic**:
   - Use `__getattr__` to delegate calls to native agent methods when required.

3. **Combine with LangSwarm Tools**:
   - Use `AgentWrapper` to ensure agents are compatible with LangSwarm workflows, such as voting, aggregation, or branching.

---

## **Key Advantages**

- **Seamless Integration**:  
  Enables out-of-the-box compatibility for agents from different platforms.

- **Unified API**:  
  Simplifies agent interaction, regardless of the underlying framework.

- **Flexible and Extensible**:  
  Adapts to custom agents or models with minimal effort.

---

## **Future Enhancements**

1. **Extended Wrapping Support**:  
   - Add pre-built compatibility for additional agent types, like Google Gemini.

2. **Automatic Behavior Detection**:  
   - Dynamically detect agent capabilities (e.g., memory support, conversational context).

3. **Enhanced Memory Management**:  
   - Integrate shared and cross-agent memory for multi-agent workflows.

---

The **AgentWrapper** is a cornerstone of LangSwarm’s ecosystem, enabling seamless multi-agent collaboration. Whether you're using LangChain, Hugging Face, or OpenAI, the `AgentWrapper` ensures your agents are ready to thrive in LangSwarm workflows.
