---
title: Collaborative Decision-Making
sidebar_position: 3
---

# Collaborative Decision-Making

## **Overview**

The **LLMConsensus** class in LangSwarm enables multiple agents to collaboratively generate and evaluate responses, selecting the most consistent or highest-quality output through consensus. It is ideal for use cases where multiple perspectives are required, and the best answer needs to be determined from a pool of responses.

---

## **Key Features**

1. **Collaborative Decision-Making**:  
   Aggregates outputs from multiple agents and determines the best response using similarity-based consensus mechanisms.

2. **Diverse Agent Support**:  
   Compatible with LangChain, Hugging Face, OpenAI, and custom agents via the `AgentWrapper`.

3. **Dynamic Similarity Calculation**:  
   Uses cosine similarity and paraphrase detection to evaluate and compare responses.

4. **Configurable Consensus Mechanisms**:  
   Supports customization of thresholds and other parameters to tailor consensus behavior.

---

## **API Reference**

### **Class: `LLMConsensus`**

Performs consensus-building among multiple agents.

#### **Initialization**

```python
LLMConsensus(query, clients, threshold=0.75, verbose=False)
```

| Parameter      | Type        | Description                                                                 |
|----------------|-------------|-----------------------------------------------------------------------------|
| `query`        | `str`       | The input query to be processed by the agents.                              |
| `clients`      | `list`      | A list of agents participating in the consensus process.                    |
| `threshold`    | `float`     | The similarity threshold for determining consensus. Default is `0.75`.      |
| `verbose`      | `bool`      | If `True`, enables detailed logging. Default is `False`.                    |

---

### **Methods**

#### **`run()`**

Executes the consensus workflow, querying all agents, comparing their outputs, and selecting the best response.

**Returns**:  
- `tuple`: The selected response, its similarity score, and the group size supporting it.

---

## **Examples**

### **Basic Example**

```python
from langswarm.swarm import LLMConsensus
from langswarm.wrappers import AgentWrapper
from langchain.llms import OpenAI

# Step 1: Create and wrap agents
agent1 = AgentWrapper(agent=OpenAI(model="gpt-4"), is_conversational=True)
agent2 = AgentWrapper(agent=OpenAI(model="gpt-3.5-turbo"), is_conversational=True)

# Step 2: Initialize LLMConsensus with the agents
query = "What are the key benefits of using solar energy?"
consensus_swarm = LLMConsensus(query=query, clients=[agent1, agent2])

# Step 3: Run the consensus workflow
response, similarity, group_size = consensus_swarm.run()

# Display the results
print("Consensus Response:", response)
print("Similarity Score:", similarity)
print("Group Size Supporting Consensus:", group_size)
```

---

### **Advanced Example: Custom Thresholds**

```python
from langswarm.swarm import LLMConsensus
from langswarm.wrappers import AgentWrapper
from transformers import pipeline

# Step 1: Create and wrap agents
huggingface_agent = AgentWrapper(agent=pipeline("text-generation", model="gpt2"), is_conversational=False)

openai_agent = AgentWrapper(agent="openai_gpt3", is_conversational=True)  # Assuming an OpenAI agent wrapper

# Step 2: Initialize LLMConsensus with a custom threshold
query = "What are the challenges of remote work?"
consensus_swarm = LLMConsensus(query=query, clients=[huggingface_agent, openai_agent], threshold=0.8, verbose=True)

# Step 3: Run the consensus workflow
response, similarity, group_size = consensus_swarm.run()

# Display the results
print("Consensus Response:", response)
print("Similarity Score:", similarity)
print("Group Size Supporting Consensus:", group_size)
```

---

## **How It Works**

1. **Querying Agents**:  
   All agents in the `clients` list are queried with the provided input.

2. **Calculating Similarities**:  
   The outputs are compared using cosine similarity and paraphrase detection.

3. **Selecting the Best Response**:  
   The response with the highest similarity score that meets the threshold is selected as the consensus.

4. **Returning Results**:  
   The consensus response, its similarity score, and the group size are returned.

---

## **Best Practices**

1. **Use Multiple Agents**:  
   The effectiveness of consensus improves with diverse agents providing different perspectives.

2. **Adjust Thresholds**:  
   Tailor the similarity threshold to balance strictness and flexibility for consensus selection.

3. **Enable Verbose Mode**:  
   Use `verbose=True` during testing or debugging to understand the consensus process in detail.

---

## **Use Cases**

1. **Research and Summarization**:  
   Combine multiple agents to generate high-quality summaries of research papers or articles.

2. **Content Moderation**:  
   Validate and approve content collaboratively using multiple AI models.

3. **Decision Support Systems**:  
   Aggregate diverse perspectives for decision-making tasks.

---

## **Key Advantages**

- **Collaborative Intelligence**:  
  Harness the strengths of multiple agents to generate superior responses.

- **Flexibility**:  
  Works with diverse agents and platforms, making it adaptable to various use cases.

- **Robust Decision-Making**:  
  Ensures the selected response meets quality and consistency criteria.

---

## **Future Enhancements**

1. **Dynamic Threshold Adjustment**:  
   Automatically adjust thresholds based on the nature of the query and agent responses.

2. **Expanded Metrics**:  
   Incorporate additional metrics, such as sentiment analysis or diversity scoring, for consensus selection.

3. **Cross-Agent Memory**:  
   Enable shared memory to improve context understanding across multiple agents.

---

The **LLMConsensus** class is a powerful tool for scenarios requiring collaborative decision-making. By leveraging multiple agents and advanced similarity techniques, LangSwarm ensures the best responses are consistently selected.
