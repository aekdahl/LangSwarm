---
title: Aggregation with LangChain
sidebar_label: Aggregation with LangChain
sidebar_position: 100
---

# Aggregation with LangChain

This tutorial demonstrates how to use **LangSwarm's LLMAggregation** with LangChain in a complete pipeline. By leveraging LangSwarm’s LangChain-compatible tools, we can integrate pre- and post-processing steps seamlessly into LangChain’s infrastructure while aggregating outputs from multiple agents.

---

## **Prerequisites**

Ensure you have the necessary libraries installed:

```bash
pip install langswarm langchain langchain-openai transformers
```

---

## **Overview**

We will:
1. Use LangChain’s `LLMChain` for pre-processing input.
2. Utilize LangSwarm’s `LLMAggregationChain` to aggregate responses from multiple agents.
3. Integrate a post-processing step with LangChain to refine the aggregated output.
4. Combine all steps into a LangChain `SequentialChain` pipeline for a unified workflow.

---

## **Full Code**

```python
"""
LangSwarm + LangChain Pipeline Tutorial: Aggregation Swarm

This tutorial demonstrates how to use LangSwarm's LangChain-compatible tools
to include `LLMAggregation` directly in a LangChain pipeline with pre- and post-processing steps.

Key Features:
- Use LangSwarm’s built-in LangChain-compatible aggregation chain.
- Pre-processing and post-processing steps in the pipeline.
"""

# Import necessary libraries
from langswarm.chains import LLMAggregationChain  # LangSwarm's LangChain-compatible aggregation chain
from langchain.prompts import PromptTemplate  # LangChain prompt templates
from langchain.chains import SequentialChain, LLMChain  # LangChain pipeline framework
from langchain.llms import OpenAI  # LangChain OpenAI LLM

# Step 1: Pre-processing Chain
"""
The pre-processing chain ensures the input is clean and formatted before aggregation.
"""
pre_prompt = PromptTemplate(
    input_variables=["raw_input"],
    template="Clean and standardize the following input for analysis:\n\n{raw_input}"
)
pre_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=pre_prompt)

# Step 2: Aggregation Chain
"""
Use LangSwarm's LangChain-compatible `LLMAggregationChain` to aggregate outputs
from multiple agents.
"""
aggregation_chain = LLMAggregationChain(
    agents=[
        {"model": "gpt-4", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo-instruct", "api_key": "your_openai_api_key"},
    ]
)

# Step 3: Post-processing Chain
"""
The post-processing chain refines the aggregated output and generates actionable insights.
"""
post_prompt = PromptTemplate(
    input_variables=["aggregated_response"],
    template=(
        "Based on the following aggregated data:\n\n"
        "{aggregated_response}\n\n"
        "Provide three actionable insights."
    )
)
post_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=post_prompt)

# Step 4: Build the LangChain Pipeline
"""
Combine the pre-processing, aggregation, and post-processing steps into a LangChain pipeline.
"""
pipeline = SequentialChain(
    chains=[pre_chain, aggregation_chain, post_chain],
    input_variables=["raw_input"],
    output_variables=["aggregated_response", "insights"],
)

# Step 5: Run the Pipeline
"""
Run the pipeline on a query, demonstrating the complete multi-agent workflow.
"""
query = "What are the main causes and solutions for climate change?"
results = pipeline.run({"raw_input": query})

# Display the results
print("\nAggregated Response:", results["aggregated_response"])
print("\nActionable Insights:", results["insights"])
```

---

## **Code Walkthrough**

### **Step 1: Pre-processing Chain**
The pre-processing chain ensures the input is clean and formatted before aggregation. This step uses LangChain’s `LLMChain` to process the raw query.

```python
pre_prompt = PromptTemplate(
    input_variables=["raw_input"],
    template="Clean and standardize the following input for analysis:\n\n{raw_input}"
)
pre_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=pre_prompt)
```

---

### **Step 2: Aggregation Chain**
LangSwarm’s `LLMAggregationChain` aggregates responses from multiple agents. The chain is built-in and LangChain-compatible, simplifying the integration process.

```python
aggregation_chain = LLMAggregationChain(
    agents=[
        {"model": "gpt-4", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo-instruct", "api_key": "your_openai_api_key"},
    ]
)
```

---

### **Step 3: Post-processing Chain**
The post-processing chain refines the aggregated output. Here, actionable insights are generated from the aggregated response using LangChain’s `LLMChain`.

```python
post_prompt = PromptTemplate(
    input_variables=["aggregated_response"],
    template=(
        "Based on the following aggregated data:\n\n"
        "{aggregated_response}\n\n"
        "Provide three actionable insights."
    )
)
post_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=post_prompt)
```

---

### **Step 4: Build the LangChain Pipeline**
The `SequentialChain` combines all steps—pre-processing, aggregation, and post-processing—into a unified pipeline.

```python
pipeline = SequentialChain(
    chains=[pre_chain, aggregation_chain, post_chain],
    input_variables=["raw_input"],
    output_variables=["aggregated_response", "insights"],
)
```

---

### **Step 5: Run the Pipeline**
The pipeline is executed with a query. The pre-processing step cleans the query, the aggregation step combines responses from agents, and the post-processing step refines the output.

```python
query = "What are the main causes and solutions for climate change?"
results = pipeline.run({"raw_input": query})

# Display the results
print("\nAggregated Response:", results["aggregated_response"])
print("\nActionable Insights:", results["insights"])
```

---

## **Expected Output**

```plaintext
Aggregated Response:
Climate change is caused by greenhouse gas emissions, deforestation, and industrial pollution. It leads to global warming, rising sea levels, and extreme weather events.

Actionable Insights:
1. Transition to renewable energy sources.
2. Implement reforestation programs and protect natural habitats.
3. Enforce stricter regulations on industrial emissions.
```

---

## **Why This is Powerful**

1. **Seamless Integration**:
   - LangSwarm integrates naturally into LangChain pipelines without requiring custom wrappers.

2. **Collaborative AI**:
   - Aggregates diverse outputs from multiple agents for a comprehensive response.

3. **Scalability**:
   - Easily extend the pipeline by adding more agents or additional steps.

With LangSwarm’s LangChain-compatible chains, you can effortlessly integrate multi-agent collaboration into your existing LangChain workflows. This tutorial demonstrates how to create advanced pipelines for powerful and scalable AI solutions.
