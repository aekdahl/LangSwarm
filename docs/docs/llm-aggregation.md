---
title: Multi-Agent Aggregation
sidebar_position: 1
---

# Multi-Agent Aggregation

## **Overview**

The **LLMAggregation** class in LangSwarm is designed to combine and aggregate responses from multiple agents into a unified output. It is ideal for scenarios where insights from multiple agents need to be merged or summarized, such as brainstorming, research synthesis, or collaborative content creation.

---

## **Key Features**

1. **Multi-Agent Aggregation**:  
   Collects and combines responses from multiple agents into a single, coherent output.

2. **Flexible Integration**:  
   Works seamlessly with agents from LangChain, Hugging Face, OpenAI, and custom implementations via the `AgentWrapper`.

3. **Customizable Merging**:  
   Allows for tailored aggregation logic to suit specific workflows or output requirements.

4. **LangChain-Compatible**:  
   Easily integrates into LangChain pipelines for pre- and post-processing.

---

## **API Reference**

### **Class: `LLMAggregation`**

Performs aggregation of responses from multiple agents.

#### **Initialization**

```python
LLMAggregation(query, clients, verbose=False)
```

| Parameter  | Type    | Description                                                                |
|------------|---------|----------------------------------------------------------------------------|
| `query`    | `str`   | The input query to be processed by the agents.                             |
| `clients`  | `list`  | A list of agents participating in the aggregation process.                 |
| `verbose`  | `bool`  | If `True`, enables detailed logging. Default is `False`.                   |

---

### **Methods**

#### **`run(hb=None)`**

Executes the aggregation workflow, querying all agents and combining their responses.

| Parameter  | Type    | Description                                                                |
|------------|---------|----------------------------------------------------------------------------|
| `hb`       | `object`| (Optional) Helper bot for advanced aggregation logic.                      |

**Returns**:  
- `str`: The aggregated response.

---

## **Examples**

### **Basic Example**

```python
from langswarm.swarm import LLMAggregation
from langswarm.wrappers import AgentWrapper
from langchain.llms import OpenAI

# Step 1: Create and wrap agents
agent1 = AgentWrapper(agent=OpenAI(model="gpt-4"), is_conversational=True)
agent2 = AgentWrapper(agent=OpenAI(model="gpt-3.5-turbo"), is_conversational=True)

# Step 2: Initialize LLMAggregation with the agents
query = "List the main causes of climate change."
aggregation_swarm = LLMAggregation(query=query, clients=[agent1, agent2])

# Step 3: Run the aggregation workflow
aggregated_response = aggregation_swarm.run()

# Display the results
print("Aggregated Response:", aggregated_response)
```

---

### **Advanced Example: Custom Helper Bot**

```python
from langswarm.swarm import LLMAggregation
from langswarm.wrappers import AgentWrapper
from transformers import pipeline

# Step 1: Create and wrap agents
huggingface_agent = AgentWrapper(agent=pipeline("text-generation", model="gpt2"), is_conversational=False)

openai_agent = AgentWrapper(agent="openai_gpt3", is_conversational=True)  # Assuming an OpenAI agent wrapper

# Step 2: Initialize LLMAggregation with a helper bot
query = "What are the benefits of renewable energy?"
aggregation_swarm = LLMAggregation(query=query, clients=[huggingface_agent, openai_agent])

# Optional: Use a helper bot for advanced aggregation
class HelperBot:
    def chat(self, q, reset=True, erase_query=True):
        # Custom aggregation logic
        return "Merged and aggregated data from all responses."

helper_bot = HelperBot()

# Step 3: Run the aggregation workflow with the helper bot
aggregated_response = aggregation_swarm.run(hb=helper_bot)

# Display the results
print("Aggregated Response:", aggregated_response)
```

---

## **How It Works**

1. **Querying Agents**:  
   All agents in the `clients` list are queried with the provided input.

2. **Combining Responses**:  
   The responses are merged or aggregated based on the aggregation logic (default or custom via helper bot).

3. **Returning Results**:  
   The aggregated response is returned as a unified output.

---

## **Best Practices**

1. **Diverse Agents**:  
   Use a mix of agents to ensure a variety of perspectives and insights in the aggregated output.

2. **Helper Bot**:  
   Leverage a helper bot for advanced or custom aggregation logic tailored to your use case.

3. **Enable Verbose Mode**:  
   Use `verbose=True` during development to understand how responses are aggregated.

---

## **Use Cases**

1. **Research Synthesis**:  
   Combine insights from multiple agents to create comprehensive summaries of research topics.

2. **Brainstorming**:  
   Aggregate diverse ideas for creative tasks or problem-solving.

3. **Collaborative Content Creation**:  
   Merge contributions from different agents into a unified piece of content.

---

## **Key Advantages**

- **Collaboration at Scale**:  
  Aggregate responses from multiple agents for well-rounded outputs.

- **Flexible Integration**:  
  Compatible with various platforms, including LangChain and Hugging Face.

- **Custom Aggregation**:  
  Tailor aggregation logic to suit specific needs using helper bots.

---

## **Future Enhancements**

1. **Dynamic Aggregation Logic**:  
   Implement intelligent merging algorithms based on content type or query intent.

2. **Improved Summarization**:  
   Enhance the aggregation process with advanced summarization techniques.

3. **Real-Time Collaboration**:  
   Enable real-time aggregation for live inputs from multiple agents.

---

The **LLMAggregation** class is a versatile tool for combining insights from multiple agents. Whether you're brainstorming, synthesizing research, or creating collaborative content, LangSwarm’s aggregation capabilities simplify the process while ensuring high-quality outputs.
