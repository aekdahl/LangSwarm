---
title: Multi-Agent Voting
sidebar_position: 5
---

# Multi-Agent Voting

## **Overview**

The **LLMVoting** class in LangSwarm enables decision-making by evaluating outputs from multiple agents and selecting the most popular or agreed-upon response through a voting mechanism. It is ideal for scenarios requiring collaborative validation, such as content moderation, consensus-building, or opinion polling.

---

## **Key Features**

1. **Collaborative Decision-Making**:  
   Aggregates outputs from multiple agents and determines the best response based on a voting mechanism.

2. **Flexible Voting Logic**:  
   Supports customization of voting thresholds and scoring criteria.

3. **Multi-Agent Support**:  
   Works seamlessly with agents from LangChain, Hugging Face, OpenAI, or custom implementations via the `AgentWrapper`.

4. **LangChain-Compatible**:  
   Can be integrated into LangChain workflows for pre- and post-processing.

---

## **API Reference**

### **Class: `LLMVoting`**

Facilitates voting-based decision-making among multiple agents.

#### **Initialization**

```python
LLMVoting(query, clients, threshold=0.75, verbose=False)
```

| Parameter  | Type    | Description                                                                |
|------------|---------|----------------------------------------------------------------------------|
| `query`    | `str`   | The input query to be processed by the agents.                             |
| `clients`  | `list`  | A list of agents participating in the voting process.                      |
| `threshold`| `float` | The similarity threshold for determining agreement. Default is `0.75`.      |
| `verbose`  | `bool`  | If `True`, enables detailed logging. Default is `False`.                   |

---

### **Methods**

#### **`run()`**

Executes the voting workflow, querying all agents, evaluating their outputs, and selecting the most agreed-upon response.

**Returns**:  
- `tuple`: The winning response, its agreement score, and the total number of votes received.

---

## **Examples**

### **Basic Example**

```python
from langswarm.swarm import LLMVoting
from langswarm.wrappers import AgentWrapper
from langchain.llms import OpenAI

# Step 1: Create and wrap agents
agent1 = AgentWrapper(agent=OpenAI(model="gpt-4"), is_conversational=True)
agent2 = AgentWrapper(agent=OpenAI(model="gpt-3.5-turbo"), is_conversational=True)
agent3 = AgentWrapper(agent=OpenAI(model="gpt-3.5-turbo-instruct"), is_conversational=True)

# Step 2: Initialize LLMVoting with the agents
query = "What are the benefits of renewable energy?"
voting_swarm = LLMVoting(query=query, clients=[agent1, agent2, agent3])

# Step 3: Run the voting workflow
winning_response, agreement_score, votes = voting_swarm.run()

# Display the results
print("Winning Response:", winning_response)
print("Agreement Score:", agreement_score)
print("Total Votes:", votes)
```

---

### **Advanced Example: Custom Thresholds**

```python
from langswarm.swarm import LLMVoting
from langswarm.wrappers import AgentWrapper
from transformers import pipeline

# Step 1: Create and wrap agents
huggingface_agent = AgentWrapper(agent=pipeline("text-generation", model="gpt2"), is_conversational=False)

openai_agent = AgentWrapper(agent="openai_gpt3", is_conversational=True)  # Assuming an OpenAI agent wrapper

# Step 2: Initialize LLMVoting with a custom threshold
query = "What are the challenges of remote work?"
voting_swarm = LLMVoting(query=query, clients=[huggingface_agent, openai_agent], threshold=0.8, verbose=True)

# Step 3: Run the voting workflow
winning_response, agreement_score, votes = voting_swarm.run()

# Display the results
print("Winning Response:", winning_response)
print("Agreement Score:", agreement_score)
print("Total Votes:", votes)
```

---

## **How It Works**

1. **Querying Agents**:  
   All agents in the `clients` list are queried with the provided input.

2. **Evaluating Responses**:  
   Responses are compared to calculate agreement scores based on cosine similarity or other metrics.

3. **Selecting the Winner**:  
   The response with the highest votes or agreement score is selected as the winning output.

4. **Returning Results**:  
   The winning response, its agreement score, and the total number of votes are returned.

---

## **Best Practices**

1. **Diverse Agents**:  
   Use a mix of agents to ensure a range of perspectives during the voting process.

2. **Adjust Thresholds**:  
   Tailor the similarity threshold to balance strictness and flexibility for agreement.

3. **Enable Verbose Mode**:  
   Use `verbose=True` during development to understand the voting process in detail.

---

## **Use Cases**

1. **Content Moderation**:  
   Validate and approve content collaboratively using multiple AI models.

2. **Consensus Building**:  
   Aggregate responses to select the most agreed-upon output for decision-making.

3. **Opinion Polling**:  
   Use multiple agents to simulate polling or collect opinions on specific topics.

---

## **Key Advantages**

- **Democratic Decision-Making**:  
  Uses a voting mechanism to ensure the most agreed-upon response is selected.

- **Multi-Agent Collaboration**:  
  Leverages the strengths of multiple agents for balanced decision-making.

- **Flexible and Configurable**:  
  Supports customization of voting thresholds and evaluation metrics.

---

## **Future Enhancements**

1. **Weighted Voting**:  
   Assign different weights to agents based on reliability or relevance.

2. **Dynamic Threshold Adjustment**:  
   Automatically adjust thresholds based on query type or agent performance.

3. **Enhanced Metrics**:  
   Incorporate additional evaluation metrics such as diversity or sentiment scoring.

---

The **LLMVoting** class is a robust tool for decision-making in multi-agent workflows. By leveraging collaborative voting mechanisms, LangSwarm ensures the selection of high-quality, consensus-driven outputs.
