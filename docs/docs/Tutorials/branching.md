---
title: Branching with a LangChain
sidebar_position: 101
---

# Branching with a LangChain

This tutorial demonstrates how to use **LangSwarm's LLMBranching** with LangChain in a complete pipeline. By leveraging LangSwarm’s LangChain-compatible tools, we can generate diverse outputs from multiple agents and process those outputs with LangChain for further analysis.

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
2. Utilize LangSwarm’s `LLMBranchingChain` to generate diverse responses from multiple agents.
3. Integrate a post-processing step with LangChain to analyze and refine the outputs.
4. Combine all steps into a LangChain `SequentialChain` pipeline for a unified workflow.

---

## **Full Code**

```python
"""
LangSwarm + LangChain Pipeline Tutorial: Branching Swarm

This tutorial demonstrates how to use LangSwarm's LangChain-compatible tools
to include `LLMBranching` directly in a LangChain pipeline with pre- and post-processing steps.

Key Features:
- Use LangSwarm’s built-in LangChain-compatible branching chain.
- Pre-processing and post-processing steps in the pipeline.
- Generate diverse outputs and analyze them in a LangChain workflow.
"""

# Import necessary libraries
from langswarm.chains import LLMBranchingChain  # LangSwarm's LangChain-compatible branching chain
from langchain.prompts import PromptTemplate  # LangChain prompt templates
from langchain.chains import SequentialChain, LLMChain  # LangChain pipeline framework
from langchain.llms import OpenAI  # LangChain OpenAI LLM

# Step 1: Pre-processing Chain
"""
The pre-processing chain ensures the input is clean and formatted before branching.
"""
pre_prompt = PromptTemplate(
    input_variables=["raw_input"],
    template="Clean and standardize the following input for generating ideas:\n\n{raw_input}"
)
pre_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=pre_prompt)

# Step 2: Branching Chain
"""
Use LangSwarm's LangChain-compatible `LLMBranchingChain` to generate diverse responses
from multiple agents.
"""
branching_chain = LLMBranchingChain(
    agents=[
        {"model": "gpt-4", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo-instruct", "api_key": "your_openai_api_key"},
    ]
)

# Step 3: Post-processing Chain
"""
The post-processing chain refines the diverse outputs and generates a final analysis.
"""
post_prompt = PromptTemplate(
    input_variables=["branching_responses"],
    template=(
        "Given the following diverse responses:\n\n"
        "{branching_responses}\n\n"
        "Analyze these ideas and suggest the top three actionable recommendations."
    )
)
post_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=post_prompt)

# Step 4: Build the LangChain Pipeline
"""
Combine the pre-processing, branching, and post-processing steps into a LangChain pipeline.
"""
pipeline = SequentialChain(
    chains=[pre_chain, branching_chain, post_chain],
    input_variables=["raw_input"],
    output_variables=["branching_responses", "recommendations"],
)

# Step 5: Run the Pipeline
"""
Run the pipeline on a query, demonstrating the complete multi-agent workflow.
"""
query = "Propose a marketing strategy for an eco-friendly product."
results = pipeline.run({"raw_input": query})

# Display the results
print("\nBranching Responses:", results["branching_responses"])
print("\nTop Recommendations:", results["recommendations"])
```

---

## **Code Walkthrough**

### **Step 1: Pre-processing Chain**
The pre-processing chain ensures that the input is formatted and cleaned before being sent to the branching swarm. It uses LangChain’s `LLMChain`.

```python
pre_prompt = PromptTemplate(
    input_variables=["raw_input"],
    template="Clean and standardize the following input for generating ideas:\n\n{raw_input}"
)
pre_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=pre_prompt)
```

---

### **Step 2: Branching Chain**
LangSwarm’s `LLMBranchingChain` generates diverse responses by querying multiple agents. Each agent explores the query from a different perspective, creating a set of varied outputs.

```python
branching_chain = LLMBranchingChain(
    agents=[
        {"model": "gpt-4", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo-instruct", "api_key": "your_openai_api_key"},
    ]
)
```

---

### **Step 3: Post-processing Chain**
The post-processing chain refines and analyzes the diverse responses, providing actionable recommendations based on the branching outputs.

```python
post_prompt = PromptTemplate(
    input_variables=["branching_responses"],
    template=(
        "Given the following diverse responses:\n\n"
        "{branching_responses}\n\n"
        "Analyze these ideas and suggest the top three actionable recommendations."
    )
)
post_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=post_prompt)
```

---

### **Step 4: Build and Run the Pipeline**
The `SequentialChain` combines all steps into a single LangChain pipeline. This modular approach makes it easy to extend or modify the workflow as needed.

```python
pipeline = SequentialChain(
    chains=[pre_chain, branching_chain, post_chain],
    input_variables=["raw_input"],
    output_variables=["branching_responses", "recommendations"],
)

query = "Propose a marketing strategy for an eco-friendly product."
results = pipeline.run({"raw_input": query})

print("\nBranching Responses:", results["branching_responses"])
print("\nTop Recommendations:", results["recommendations"])
```

---

## **Expected Output**

```plaintext
Branching Responses:
1. Promote the product via social media influencers who focus on sustainability.
2. Offer discounts for customers who recycle old products.
3. Collaborate with eco-friendly brands to create bundled deals.

Top Recommendations:
1. Create a partnership program with eco-friendly influencers.
2. Launch a rewards program for customers who demonstrate sustainable practices.
3. Host community events to raise awareness about eco-friendly products.
```

---

## **Why This is Powerful**

1. **Exploration of Ideas**:
   - Generates diverse outputs from multiple agents, ensuring a range of perspectives and solutions.

2. **Seamless Integration**:
   - Combines LangSwarm’s branching capabilities with LangChain for advanced analysis.

3. **Modular Design**:
   - Easily extendable pipeline for handling additional pre- or post-processing steps.

With LangSwarm’s `LLMBranchingChain`, you can efficiently generate and refine diverse ideas, making it an excellent tool for brainstorming, problem-solving, and creative workflows.
