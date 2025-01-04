---
title: Consensus with LangChain
sidebar_label: Consensus with LangChain
sidebar_position: 102
---

# Consensus with LangChain

This tutorial demonstrates how to use **LangSwarm**'s `LLMConsensus` within a LangChain workflow to create a multi-LLM solution. The workflow combines multiple language models to achieve a consensus on a query and integrates this capability seamlessly into LangChain.

---

## **Prerequisites**

Before we begin, ensure you have the following installed:

```bash
pip install langswarm langchain langchain-openai transformers
```

---

## **Overview**

We will:
1. Define multiple agents using LangSwarm.
2. Use `LLMConsensus` to achieve agreement among these agents on a query.
3. Integrate the consensus output into a LangChain `LLMChain` to simulate downstream workflows.

---

```python
"""
LangSwarm + LangChain Tutorial

This script demonstrates how to use LangSwarm's LLMConsensus class to reach consensus
among multiple LLMs and use that consensus in a LangChain workflow.

Key Features:
- Multi-agent collaboration via LangSwarm.
- Consensus-based decision-making with `LLMConsensus`.
- Integration with LangChain for downstream processing.

"""

# Import necessary libraries
from langswarm.swarm import LLMConsensus  # LangSwarm consensus tool
from langswarm.agent import OpenAIAgent   # LangSwarm agent for OpenAI
from langchain.prompts import PromptTemplate  # LangChain prompt templates
from langchain.chains import LLMChain        # LangChain chain framework
from langchain.llms import OpenAI            # Native LangChain OpenAI LLM

# Step 1: Define multiple agents
"""
Here, we define three agents using LangSwarm's OpenAIAgent wrapper.
Each agent represents an independent LLM instance, which we will use for collaboration.
"""
agent1 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-4")
agent2 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-3.5-turbo")
agent3 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-3.5-turbo-instruct")

# Step 2: Create a consensus swarm
"""
The LLMConsensus class takes a query and a list of agents, then uses LangSwarm's
orchestration to determine the best (agreed-upon) response among the agents.
"""
query = "What are the key causes of climate change?"
consensus_swarm = LLMConsensus(query=query, clients=[agent1, agent2, agent3])

# Run the consensus swarm to get a unified response
consensus_response = consensus_swarm.run()

# Print the consensus response
print("Consensus Response:", consensus_response)

# Step 3: Use the consensus response in a LangChain workflow
"""
In this step, we integrate the consensus response into a LangChain `LLMChain`.
The response serves as input for further downstream processing.
"""

# Define a LangChain prompt template
prompt = PromptTemplate(
    input_variables=["consensus_response"],
    template="Based on the following consensus, summarize key solutions:\n\n{consensus_response}"
)

# Create a LangChain LLMChain using OpenAI
"""
We use a LangChain OpenAI LLM here to process the consensus response and generate
a summary of potential solutions for climate change.
"""
chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=prompt)

# Run the LangChain chain with the consensus response
summary = chain.run(consensus_response)

# Print the final output
print("\nSummary of Solutions:")
print(summary)
```

---

## **Code Walkthrough**

### **Step 1: Define Agents**
We define three agents (`agent1`, `agent2`, `agent3`) using LangSwarm's `OpenAIAgent`. Each agent queries a different OpenAI model, simulating a multi-agent collaboration.

```python
agent1 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-4")
agent2 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-3.5-turbo")
agent3 = OpenAIAgent(api_key="your_openai_api_key", model="gpt-3.5-turbo-instruct")
```

---

### **Step 2: Achieve Consensus**
We use `LLMConsensus` to determine a unified response to a query. The `LLMConsensus` class compares the outputs of all agents and selects the most agreed-upon response.

```python
query = "What are the key causes of climate change?"
consensus_swarm = LLMConsensus(query=query, clients=[agent1, agent2, agent3])
consensus_response = consensus_swarm.run()
print("Consensus Response:", consensus_response)
```

---

### **Step 3: Integrate with LangChain**
The consensus response is passed to a LangChain `LLMChain` for further processing. This demonstrates how LangSwarm can be seamlessly integrated into LangChain workflows.

```python
prompt = PromptTemplate(
    input_variables=["consensus_response"],
    template="Based on the following consensus, summarize key solutions:\n\n{consensus_response}"
)

chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=prompt)
summary = chain.run(consensus_response)
print("\nSummary of Solutions:")
print(summary)
```

---

## **Expected Output**

```plaintext
Consensus Response: The key causes of climate change include greenhouse gas emissions from burning fossil fuels, deforestation, and industrial activities.

Summary of Solutions:
To address climate change, key solutions include transitioning to renewable energy sources, promoting reforestation, reducing industrial emissions, and increasing public awareness about sustainable practices.
```

---

## **Why This is Powerful**

1. **Collaboration Across Models:**
   - Use multiple models collaboratively to generate robust and validated outputs.
   
2. **Seamless Integration:**
   - Combine LangSwarm's orchestration tools with LangChain's powerful chains and workflows.

3. **Scalable Multi-Agent Workflows:**
   - Extend this approach to include routing, aggregation, and voting for even more complex workflows.

---

## **Next Steps**
1. Experiment with additional Swarm classes like `LLMAggregation` or `LLMBranching`.
2. Use LangChain's memory systems with LangSwarm agents for enhanced context tracking.
3. Add more agents (e.g., Hugging Face models) to diversify the collaboration.

With LangSwarm and LangChain, you can build scalable, intelligent workflows tailored to your specific needs.
