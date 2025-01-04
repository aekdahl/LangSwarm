---
title: LlamaIndex
---

# LlamaIndex Integration in LangSwarm

LlamaIndex (formerly GPT Index) enables seamless interaction between **Large Language Models (LLMs)** and structured/unstructured data sources. With LangSwarm, you can leverage **LlamaIndex** agents alongside other LLM tools like LangChain, Hugging Face, and OpenAI to orchestrate multi-agent workflows.

---

## **Key Features**

1. **Index-Based Data Retrieval**:
   - Integrate LlamaIndex to query structured or unstructured datasets seamlessly.
2. **Memory Compatibility**:
   - Supports both LangSwarm's internal memory and LangChain memory for managing context.
3. **Unified Logging**:
   - Logs interactions with LlamaIndex agents to LangSmith (if enabled) or Python's logging system.
4. **Interoperability**:
   - Use LlamaIndex agents alongside other LangSwarm agents for consensus, voting, or aggregation workflows.

---

## **Getting Started**

### **1. Installation**

To use LlamaIndex with LangSwarm, ensure the following dependencies are installed:

```bash
pip install langswarm llama-index
```

---

### **2. Creating a LlamaIndex Agent**

#### **Using the AgentFactory (Recommended)**

The `AgentFactory` provides a simple and consistent way to create agents, including LlamaIndex.

```python
from langswarm.factory import AgentFactory

# Create a LlamaIndex agent using the AgentFactory
llama_agent = AgentFactory.create(
    name="LlamaAgent",
    agent_type="llamaindex",
    documents=["LangSwarm is a Python package for orchestrating multiple LLMs."],
)

# Query the agent
response = llama_agent.chat("What is LangSwarm?")
print(response)
# Expected Output: "LangSwarm is a Python package for orchestrating multiple LLMs."
```

#### **Using the AgentWrapper (Advanced Use Case)**

For advanced users who need more control, the `AgentWrapper` can be used directly.

```python
from langswarm.wrappers.agent_wrapper import AgentWrapper

# Advanced: Directly wrap a LlamaIndex agent
llama_agent = AgentWrapper(
    name="LlamaAgent",
    agent="llamaindex",
    documents=["LangSwarm is a Python package for orchestrating multiple LLMs."],
)

# Query the agent
response = llama_agent.chat("What is LangSwarm?")
print(response)
# Expected Output: "LangSwarm is a Python package for orchestrating multiple LLMs."
```

---

### **3. Using Memory with LlamaIndex**

LangSwarm provides flexible memory handling:
- **Agent-Specific Memory**: Automatically uses the memory provided by the agent (if available).
- **Custom Memory**: Pass a memory instance to the `AgentFactory` or `AgentWrapper`.

```python
from langchain.memory import ConversationBufferMemory
from langswarm.factory import AgentFactory

# Create a memory instance
memory = ConversationBufferMemory()

# Create a LlamaIndex agent with memory using the AgentFactory
llama_agent = AgentFactory.create(
    name="LlamaAgent",
    agent_type="llamaindex",
    documents=[
        "LangSwarm is a Python package for orchestrating multiple LLMs.",
        "LlamaIndex is a library for connecting LLMs to data sources.",
    ],
    memory=memory,
)

# Query the agent with memory support
response1 = llama_agent.chat("What is LangSwarm?")
response2 = llama_agent.chat("What is LlamaIndex?")
print(response1)
print(response2)
# Memory ensures both responses have relevant context.
```

---

### **4. Logging LlamaIndex Interactions**

LangSwarm supports unified logging:
- **LangSmith Integration**: Logs queries and responses to LangSmith when configured.
- **Fallback Logging**: Logs to Python's logging system if LangSmith is not available.

```python
# Enable LangSmith logging by providing an API key
llama_agent = AgentFactory.create(
    name="LlamaAgent",
    agent_type="llamaindex",
    documents=["LangSwarm documentation.", "LlamaIndex guides."],
    langsmith_api_key="your-langsmith-api-key",
)

# Query the agent and log the interaction
response = llama_agent.chat("What is LlamaIndex?")
```

---

## **Integration with LangSwarm Features**

### **1. Multi-Agent Collaboration**
LlamaIndex agents can participate in LangSwarm workflows like consensus or aggregation.

#### Example: Consensus Workflow with LlamaIndex and LangChain Agents

```python
from langswarm.tools import LLMConsensus
from langswarm.factory import AgentFactory

# Create agents using the AgentFactory
llama_agent = AgentFactory.create(
    name="LlamaAgent",
    agent_type="llamaindex",
    documents=["LangSwarm is a Python package."],
)
langchain_agent = AgentFactory.create(
    name="LangChainAgent",
    agent_type="langchain",
    model="gpt-3.5-turbo",
)

# Combine agents for consensus
consensus_tool = LLMConsensus(query="What is LangSwarm?", clients=[langchain_agent, llama_agent])
response = consensus_tool.run()
print(response)
# Expected Output: "LangSwarm is a Python package."
```

---

### **2. Using LlamaIndex for Data Aggregation**

```python
from langswarm.tools import LLMAggregation
from langswarm.factory import AgentFactory

# Create a LlamaIndex agent
llama_agent = AgentFactory.create(
    name="LlamaAgent",
    agent_type="llamaindex",
    documents=["LangSwarm supports LlamaIndex."],
)

# Aggregate data from multiple queries
aggregation_tool = LLMAggregation(query="Tell me about LangSwarm.", clients=[llama_agent])
response = aggregation_tool.run()
print(response)
# Expected Output: Aggregated data from LlamaIndex.
```

---

### **3. Shared Memory with LlamaIndex**

Enable shared memory by providing the same memory instance to multiple agents:

```python
from langchain.memory import ConversationBufferMemory
from langswarm.factory import AgentFactory

# Shared memory instance
shared_memory = ConversationBufferMemory()

# Create two agents with shared memory
agent1 = AgentFactory.create(
    name="Agent1",
    agent_type="llamaindex",
    documents=["Document 1"],
    memory=shared_memory,
)
agent2 = AgentFactory.create(
    name="Agent2",
    agent_type="llamaindex",
    documents=["Document 2"],
    memory=shared_memory,
)

# Query both agents with shared context
response1 = agent1.chat("What is Document 1?")
response2 = agent2.chat("What is Document 2?")
print(response1)
print(response2)
```

---

## **FAQs**

### **Q1: Do I need to install LlamaIndex separately?**
Yes. Install it using `pip install llama-index`.

### **Q2: Can LlamaIndex agents use LangChain memory?**
Yes. Provide a `ConversationBufferMemory` or another memory class when wrapping the agent.

### **Q3: Does LlamaIndex support LangSmith logging?**
Yes. If LangSmith is configured, LlamaIndex interactions are logged automatically.

---

Let me know if you'd like further refinements!
