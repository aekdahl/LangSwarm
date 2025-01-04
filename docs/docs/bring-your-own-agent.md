---
title: Bring Your Own Agent
sidebar_position: 1
---

# Bring Your Own Agent

LangSwarm empowers users to seamlessly integrate their own agents or models into LangSwarm’s ecosystem, leveraging its powerful orchestration features such as consensus, aggregation, and voting. After using LangSwarm, you can continue processing results in your platform of choice, such as LangChain, Hugging Face, or OpenAI.

This guide explains how to bring your own agents into LangSwarm, use our features, and seamlessly integrate back into your workflow.

---

## **Why Bring Your Own Agent?**

- **Flexibility**: Use your custom models or agents built on LangChain, Hugging Face, OpenAI, or other frameworks.
- **Powerful Orchestration**: Leverage LangSwarm’s multi-agent collaboration tools like `LLMConsensus`, `LLMAggregation`, and more.
- **Seamless Integration**: Output results in a format that can be passed back to your native platform or extended workflows.

---

## **Steps to Bring Your Own Agent**

1. Wrap your agent using LangSwarm’s `AgentWrapper`.
2. Use LangSwarm’s features (e.g., swarms like `LLMConsensus` or `LLMAggregation`).
3. Process the output in your platform (e.g., LangChain).

---

### **Step 1: Wrap Your Agent**

LangSwarm provides the `AgentWrapper` to make any agent compatible with its features. Wrap your agent with this class, specifying its behavior (e.g., conversational or not).

#### **Example: Wrapping a LangChain Agent**
```python
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from langswarm.wrappers import AgentWrapper

# Create a LangChain agent
memory = ConversationBufferMemory()
langchain_agent = OpenAI(model="gpt-4", memory=memory)

# Wrap the agent for LangSwarm compatibility
wrapped_agent = AgentWrapper(agent=langchain_agent, is_conversational=True)
```

#### **Example: Wrapping a Hugging Face Model**
```python
from transformers import pipeline
from langswarm.wrappers import AgentWrapper

# Load a Hugging Face QA pipeline
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

# Wrap the pipeline for LangSwarm compatibility
wrapped_agent = AgentWrapper(agent=qa_pipeline, is_conversational=False)
```

---

### **Step 2: Use LangSwarm Features**

Now that your agents are wrapped, you can use LangSwarm’s orchestration tools to process queries collaboratively.

#### **Example: Aggregation with Custom Agents**
```python
from langswarm.swarm import LLMAggregation

# Define a query
query = "What are the main causes of climate change?"

# Use LangSwarm aggregation to combine outputs
aggregation_swarm = LLMAggregation(query=query, clients=[wrapped_agent])
aggregated_response = aggregation_swarm.run()

# Print the aggregated response
print("Aggregated Response:", aggregated_response)
```

---

### **Step 3: Seamlessly Continue in Your Platform**

LangSwarm outputs results in standard formats (e.g., strings or JSON), making it easy to continue processing in your native platform.

#### **Example: Using Aggregated Response in LangChain**
```python
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Define a LangChain prompt template
prompt = PromptTemplate(
    input_variables=["aggregated_response"],
    template=(
        "Based on the following aggregated data:\n\n"
        "{aggregated_response}\n\n"
        "Propose three solutions to mitigate climate change."
    )
)

# Create a LangChain chain
chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=prompt)

# Use the aggregated response as input
solutions = chain.run({"aggregated_response": aggregated_response})

# Print the solutions
print("\nProposed Solutions:")
print(solutions)
```

---

## **Full Workflow Example**

Here’s a complete workflow showcasing how to bring your own agent, use LangSwarm features, and continue in LangChain.

```python
"""
Complete Workflow: Bring Your Own Agent with LangSwarm and LangChain

1. Wrap your agent for LangSwarm compatibility.
2. Use LangSwarm’s orchestration tools (e.g., LLMAggregation).
3. Continue processing results in LangChain.
"""

# Import necessary libraries
from langswarm.wrappers import AgentWrapper
from langswarm.swarm import LLMAggregation
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from transformers import pipeline

# Step 1: Wrap your agent
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
wrapped_agent = AgentWrapper(agent=qa_pipeline, is_conversational=False)

# Step 2: Use LangSwarm features
query = "What are the main causes of deforestation?"
aggregation_swarm = LLMAggregation(query=query, clients=[wrapped_agent])
aggregated_response = aggregation_swarm.run()
print("Aggregated Response:", aggregated_response)

# Step 3: Process the results in LangChain
prompt = PromptTemplate(
    input_variables=["aggregated_response"],
    template=(
        "Based on the following aggregated data:\n\n"
        "{aggregated_response}\n\n"
        "Suggest three ways to prevent deforestation."
    )
)
chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=prompt)
solutions = chain.run({"aggregated_response": aggregated_response})
print("\nProposed Solutions:", solutions)
```

---

## **Advanced Use Cases**

1. **Cross-Agent Memory Sharing**
   - Use LangSwarm’s shared memory system to enable memory sharing between wrapped agents.

2. **Dynamic Routing**
   - Combine multiple agents with LangSwarm’s routing capabilities to dynamically choose the best agent for a query.

3. **Integration with Custom Pipelines**
   - Integrate LangSwarm features into your custom LangChain pipelines with pre- and post-processing steps.

---

## **Best Practices**

- **Select the Right Wrapper**: Ensure your agent is wrapped using `AgentWrapper` to make it compatible with LangSwarm features.
- **Optimize Query Structure**: For best results, standardize your queries during pre-processing.
- **Leverage LangSwarm Features**: Use LangSwarm's orchestration tools to aggregate, validate, or route outputs before feeding them into your native workflows.

---

LangSwarm’s `Bring Your Own Agent` capability gives you the flexibility to use custom models or agents while leveraging its orchestration power. Combine the best of LangSwarm and LangChain to build intelligent, multi-agent workflows tailored to your needs!
