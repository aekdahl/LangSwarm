---
id: getting-started
title: Getting Started with LangSwarm
slug: /
sidebar_label: Getting Started
sidebar_position: 0
---

### **Getting Started with LangSwarm**

Welcome to **LangSwarm**, a Python package for orchestrating and enhancing collaboration among multiple AI agents, including **LangChain**, **Hugging Face**, **OpenAI**, and more. LangSwarm enables seamless integration and provides tools for consensus-building, memory management, multi-agent orchestration, and more.

This guide will help you quickly get started by walking you through installation, creating agents, and using LangSwarm's powerful orchestration tools.

---

### **Installation**

LangSwarm requires Python 3.8+ and can be installed from PyPI. Use the following command:

```bash
pip install langswarm
```

#### **Additional Dependencies**

Depending on the agents you plan to use, you may need to install additional dependencies:

- **LangChain**: Required for LangChain agents and memory management.
  ```bash
  pip install langchain
  ```

- **LangChain-OpenAI**: Needed for direct integration with OpenAI models via LangChain.
  ```bash
  pip install langchain-openai
  ```

- **Transformers**: Required for Hugging Face models.
  ```bash
  pip install transformers
  ```

- **Optional Dependencies**: Other libraries (e.g., Redis) may be required if you use specific memory backends.

---

### **Key Features**

1. **Multi-Agent Orchestration:**
   - Manage multiple agents for collaboration, routing, and decision-making.
2. **Native OpenAI Support:**
   - Directly use OpenAI agents without additional wrappers or dependencies.
3. **Agent Creation:**
   - Use LangSwarm to create and manage agents from LangChain, Hugging Face, and OpenAI seamlessly.
4. **Memory Management:**
   - Support for shared memory across agents or standalone memory for individual agents.
5. **Advanced Consensus and Aggregation Tools:**
   - Validate, combine, and summarize outputs from multiple agents.
6. **Integration with Native Platforms:**
   - Wrap LangChain, Hugging Face, or OpenAI agents and extend their functionality while retaining native platform features.

---

### **Basic Concepts**

#### **Agents**
LangSwarm supports three main categories of agents:
1. **LangChain agents**: Leverage LangChain's powerful tools, chains, and memory.
2. **Hugging Face models**: Use transformers for conversational AI, question answering, or custom tasks.
3. **Native OpenAI agents**: Integrate directly with OpenAI's GPT models without wrappers.

#### **Swarm Classes**
LangSwarm provides powerful orchestration tools to manage and extend multi-agent workflows:
- **Consensus**: Achieve agreement among multiple agents.
- **Aggregation**: Combine outputs into meaningful summaries.
- **Branching**: Generate diverse outputs for further analysis.
- **Voting**: Use democratic methods to select the best outputs.

#### **Agent Creation**
LangSwarm allows you to create agents for LangChain, Hugging Face, and OpenAI directly. These agents work seamlessly with LangSwarm's features and tools.

---

### **Step 1: Creating Agents in LangSwarm**

You can create agents directly using LangSwarm. These agents are fully compatible with LangSwarm's features and tools.

#### **Creating a LangChain Agent**
```python
from langswarm.agent import LangChainAgent
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory

# Create a LangChain agent with memory
memory = ConversationBufferMemory()
langchain_agent = LangChainAgent(llm=OpenAI(), memory=memory)

# Interact with the agent
response = langchain_agent.chat("What is the capital of France?")
print(response)
```

#### **Creating a Hugging Face Agent**
```python
from langswarm.agent import HuggingFaceAgent
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load a Hugging Face conversational model
model_name = "microsoft/DialoGPT-medium"
huggingface_agent = HuggingFaceAgent(model_name=model_name)

# Interact with the agent
response = huggingface_agent.chat("Tell me about Paris.")
print(response)
```

#### **Creating a Native OpenAI Agent**
```python
from langswarm.agent import OpenAIAgent

# Create an OpenAI agent
openai_agent = OpenAIAgent(api_key="your_openai_api_key", model="gpt-4")

# Interact with the agent
response = openai_agent.chat("What is quantum entanglement?")
print(response)
```

---

### **Step 2: Wrapping External Agents**

If you're using LangChain, Hugging Face, or OpenAI agents not created in LangSwarm, you can use the `AgentWrapper` to extend their functionality. This allows you to integrate these agents into LangSwarm workflows while retaining native platform features.

#### **LangChain Example: Including in a Chain**
```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langswarm.wrappers import AgentWrapper
from langchain.llms import OpenAI

# Create a LangChain agent
prompt = PromptTemplate(input_variables=["question"], template="Answer this: {question}")
chain = LLMChain(llm=OpenAI(), prompt=prompt)

# Wrap the agent
wrapped_agent = AgentWrapper(agent=chain)

# Use the wrapped agent
response = wrapped_agent.chat("What is the capital of Germany?")
print(response)
```

#### **Hugging Face Example: Custom Pipeline Integration**
```python
from transformers import pipeline
from langswarm.wrappers import AgentWrapper

# Load a QA pipeline from Hugging Face
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

# Wrap the pipeline
wrapped_agent = AgentWrapper(agent=qa_pipeline)

# Use the wrapped agent
response = wrapped_agent.chat("What is the capital of France?")
print(response)
```

---

### **Step 3: Using Swarm Classes**

#### **Consensus Swarm**
Achieve consensus among multiple agents.

```python
from langswarm.swarm import LLMConsensus
from langswarm.agent import OpenAIAgent

# Define agents
agent1 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-4")
agent2 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-3.5")

# Create a consensus swarm
consensus_swarm = LLMConsensus(query="What is the capital of France?", clients=[agent1, agent2])
response = consensus_swarm.run()
print("Consensus Response:", response)
```

#### **Aggregation Swarm**
Combine outputs from multiple agents.

```python
from langswarm.swarm import LLMAggregation
from langswarm.agent import HuggingFaceAgent

# Define agents
agent1 = HuggingFaceAgent(model_name="facebook/blenderbot-400M-distill")
agent2 = HuggingFaceAgent(model_name="microsoft/DialoGPT-medium")

# Create an aggregation swarm
aggregation_swarm = LLMAggregation(query="Summarize the causes of World War II.", clients=[agent1, agent2])
response = aggregation_swarm.run()
print("Aggregated Response:", response)
```

---

### **Documentation & Support**

Explore more features and detailed examples in the [LangSwarm GitHub Repository](https://github.com/your-repo/langswarm). If you encounter issues, join the [Discussions](https://github.com/your-repo/langswarm/discussions) or file an [Issue](https://github.com/your-repo/langswarm/issues).

LangSwarm makes orchestrating intelligent workflows across AI agents simple, flexible, and scalable. Dive in and start building smarter AI systems today!
