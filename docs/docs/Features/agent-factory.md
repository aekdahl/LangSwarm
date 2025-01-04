---
title: AgentFactory
sidebar_position: 60
---

# AgentFactory

## **Overview**

The **AgentFactory** in LangSwarm simplifies the creation of agents for use in LangSwarm workflows. It provides a unified interface for building agents from popular platforms like LangChain, Hugging Face, OpenAI, and custom implementations. By abstracting the agent creation process, the `AgentFactory` enables developers to focus on orchestrating multi-agent workflows without worrying about agent compatibility.

---

## **Key Features**

1. **Unified Interface**: Supports agent creation from multiple platforms (LangChain, Hugging Face, OpenAI, etc.).
2. **Custom Agent Support**: Allows integration of custom models or agents using LangSwarm’s wrapper classes.
3. **Flexibility**: Automatically adapts agents to LangSwarm workflows, such as voting, consensus, and aggregation.
4. **Dynamic Wrapping**: Wraps agents with required features like memory or conversational context, ensuring compatibility with LangSwarm tools.

---

## **API Reference**

### **`AgentFactory.create_agent`**

Creates an agent based on the provided configuration.

#### **Parameters**

| Parameter         | Type     | Description                                                                 |
|-------------------|----------|-----------------------------------------------------------------------------|
| `agent_type`      | `str`    | The type of agent to create (`"langchain"`, `"huggingface"`, `"openai"`, etc.). |
| `model`           | `str`    | The model identifier (e.g., `"gpt-4"`, `"distilbert-base-uncased"`, etc.).   |
| `api_key`         | `str`    | (Optional) API key for platforms like OpenAI or Google Gemini.              |
| `is_conversational` | `bool` | Indicates whether the agent supports conversational context.               |
| `kwargs`          | `dict`   | Additional parameters passed to the agent during initialization.           |

#### **Returns**

- An instance of the created agent wrapped with `AgentWrapper`.

#### **Example Usage**

```python
from langswarm.factory import AgentFactory

# Create a LangChain agent
langchain_agent = AgentFactory.create_agent(
    agent_type="langchain",
    model="gpt-4",
    api_key="your_openai_api_key",
    is_conversational=True
)

# Create a Hugging Face agent
huggingface_agent = AgentFactory.create_agent(
    agent_type="huggingface",
    model="distilbert-base-uncased",
    is_conversational=False
)

# Create an OpenAI agent
openai_agent = AgentFactory.create_agent(
    agent_type="openai",
    model="gpt-3.5-turbo",
    api_key="your_openai_api_key",
    is_conversational=True
)
```

---

### **`AgentFactory.wrap_agent`**

Wraps an existing agent with additional LangSwarm functionality.

#### **Parameters**

| Parameter         | Type     | Description                                                                 |
|-------------------|----------|-----------------------------------------------------------------------------|
| `agent`           | `object` | The agent to be wrapped.                                                   |
| `is_conversational` | `bool` | Indicates whether the agent supports conversational context.               |
| `kwargs`          | `dict`   | Additional parameters for the wrapper.                                     |

#### **Returns**

- An instance of the wrapped agent.

#### **Example Usage**

```python
from langswarm.factory import AgentFactory
from langchain.llms import OpenAI

# Create a LangChain agent
langchain_native_agent = OpenAI(model="gpt-4", temperature=0)

# Wrap the agent for LangSwarm compatibility
wrapped_agent = AgentFactory.wrap_agent(
    agent=langchain_native_agent,
    is_conversational=True
)
```

---

## **Full Example**

### **Creating Multiple Agents with AgentFactory**

The following example demonstrates how to create multiple agents using the `AgentFactory` and use them in a LangSwarm `LLMConsensus` workflow.

```python
from langswarm.factory import AgentFactory
from langswarm.swarm import LLMConsensus

# Step 1: Create agents
langchain_agent = AgentFactory.create_agent(
    agent_type="langchain",
    model="gpt-4",
    api_key="your_openai_api_key",
    is_conversational=True
)

huggingface_agent = AgentFactory.create_agent(
    agent_type="huggingface",
    model="distilbert-base-uncased",
    is_conversational=False
)

openai_agent = AgentFactory.create_agent(
    agent_type="openai",
    model="gpt-3.5-turbo",
    api_key="your_openai_api_key",
    is_conversational=True
)

# Step 2: Use the agents in a LangSwarm workflow
query = "What are the benefits of AI in healthcare?"
consensus_swarm = LLMConsensus(query=query, clients=[langchain_agent, huggingface_agent, openai_agent])

# Step 3: Run the consensus workflow
response = consensus_swarm.run()
print("Consensus Response:", response)
```

---

## **Best Practices**

1. **Use `AgentFactory` for Consistency**:
   - Always create agents through `AgentFactory` to ensure they are properly wrapped and compatible with LangSwarm workflows.

2. **Specify Conversational Context**:
   - Set `is_conversational=True` for agents that support memory or context, such as LangChain agents with memory.

3. **Custom Agent Wrapping**:
   - For unsupported agents, use `AgentFactory.wrap_agent` to extend functionality and make them LangSwarm-compatible.

---

## **Key Advantages**

- **Streamlined Agent Creation**:
  - One unified interface to manage agents from various platforms.
  
- **Seamless Integration**:
  - Agents created by `AgentFactory` work seamlessly across LangSwarm features like voting, aggregation, and routing.

- **Customizable**:
  - Add custom configurations to agents without worrying about compatibility issues.

---

## **Future Enhancements**

1. **Extend Support**:
   - Add support for additional platforms like Google Gemini or proprietary APIs.
   
2. **Predefined Templates**:
   - Include common agent configurations for popular use cases.

3. **Agent Validation**:
   - Add checks to validate agent functionality (e.g., conversational or non-conversational behavior).

---

The **AgentFactory** is your go-to solution for simplifying multi-agent workflows in LangSwarm. By abstracting agent creation and compatibility, it ensures a hassle-free experience when working with diverse agents in your AI pipelines.
