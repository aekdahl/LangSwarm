---
title: Routing with a LangChain
sidebar_position: 103
---

# Routing with a LangChain

This tutorial demonstrates how to use **LangSwarm's LLMRouting** within a LangChain pipeline. LangSwarm's routing capabilities allow dynamic selection of workflows (e.g., branching, voting, consensus) based on the query or other conditions, enabling flexible and scalable AI solutions.

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
2. Utilize LangSwarm’s `LLMRouting` to dynamically select a workflow (e.g., voting, branching).
3. Integrate a post-processing step with LangChain to refine the selected response.
4. Combine all steps into a LangChain `SequentialChain` pipeline for a unified workflow.

---

## **Full Code**

```python
"""
LangSwarm + LangChain Pipeline Tutorial: Routing Swarm

This tutorial demonstrates how to use LangSwarm's LangChain-compatible tools
to include `LLMRouting` directly in a LangChain pipeline with pre- and post-processing steps.

Key Features:
- Use LangSwarm’s dynamic routing capabilities.
- Route queries to different workflows (e.g., voting, branching, consensus).
- Pre-processing and post-processing steps in the pipeline.
"""

# Import necessary libraries
from langswarm.swarm import LLMRouting  # LangSwarm's dynamic routing tool
from langchain.prompts import PromptTemplate  # LangChain prompt templates
from langchain.chains import SequentialChain, LLMChain  # LangChain pipeline framework
from langchain.llms import OpenAI  # LangChain OpenAI LLM

# Step 1: Pre-processing Chain
"""
The pre-processing chain ensures the input is clean and formatted before routing.
"""
pre_prompt = PromptTemplate(
    input_variables=["raw_input"],
    template="Clean and standardize the following input for processing:\n\n{raw_input}"
)
pre_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=pre_prompt)

# Step 2: Routing Swarm
"""
Use LangSwarm's LLMRouting to dynamically select a workflow based on the query.
"""
class RoutingChain:
    """
    A LangChain-compatible wrapper for LangSwarm's LLMRouting.
    """

    def __init__(self, query, route, agents):
        self.routing_swarm = LLMRouting(route=route, bots=agents, main_bot=agents[0], query=query)

    def run(self, query):
        return self.routing_swarm.run()

# Define agents for routing
agents = [
    {"model": "gpt-4", "api_key": "your_openai_api_key"},
    {"model": "gpt-3.5-turbo", "api_key": "your_openai_api_key"},
    {"model": "gpt-3.5-turbo-instruct", "api_key": "your_openai_api_key"},
]

# Example: Route 1 (Branching) and Route 2 (Voting)
routing_chain = RoutingChain(query="What are the benefits of AI in education?", route=1, agents=agents)

# Step 3: Post-processing Chain
"""
The post-processing chain refines the routed response and generates actionable insights.
"""
post_prompt = PromptTemplate(
    input_variables=["routed_response"],
    template=(
        "Based on the routed response:\n\n"
        "{routed_response}\n\n"
        "Provide three actionable recommendations."
    )
)
post_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=post_prompt)

# Step 4: Build the LangChain Pipeline
"""
Combine the pre-processing, routing, and post-processing steps into a LangChain pipeline.
"""
pipeline = SequentialChain(
    chains=[pre_chain, routing_chain, post_chain],
    input_variables=["raw_input"],
    output_variables=["routed_response", "recommendations"],
)

# Step 5: Run the Pipeline
"""
Run the pipeline on a query, demonstrating the complete multi-agent workflow.
"""
query = "What are the benefits of AI in education?"
results = pipeline.run({"raw_input": query})

# Display the results
print("\nRouted Response:", results["routed_response"])
print("\nRecommendations:", results["recommendations"])
```

---

## **Code Walkthrough**

### **Step 1: Pre-processing Chain**
The pre-processing chain formats the input query to ensure it is standardized before being routed to the appropriate workflow.

```python
pre_prompt = PromptTemplate(
    input_variables=["raw_input"],
    template="Clean and standardize the following input for processing:\n\n{raw_input}"
)
pre_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=pre_prompt)
```

---

### **Step 2: Routing Swarm**
LangSwarm’s `LLMRouting` dynamically selects the workflow (e.g., branching or voting) based on the query and the specified route.

```python
class RoutingChain:
    """
    A LangChain-compatible wrapper for LangSwarm's LLMRouting.
    """

    def __init__(self, query, route, agents):
        self.routing_swarm = LLMRouting(route=route, bots=agents, main_bot=agents[0], query=query)

    def run(self, query):
        return self.routing_swarm.run()

# Define agents for routing
agents = [
    {"model": "gpt-4", "api_key": "your_openai_api_key"},
    {"model": "gpt-3.5-turbo", "api_key": "your_openai_api_key"},
    {"model": "gpt-3.5-turbo-instruct", "api_key": "your_openai_api_key"},
]
```

---

### **Step 3: Post-processing Chain**
The post-processing chain refines the routed response and provides actionable insights based on the output.

```python
post_prompt = PromptTemplate(
    input_variables=["routed_response"],
    template=(
        "Based on the routed response:\n\n"
        "{routed_response}\n\n"
        "Provide three actionable recommendations."
    )
)
post_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=post_prompt)
```

---

### **Step 4: Build and Run the Pipeline**
The `SequentialChain` combines all steps into a single LangChain pipeline, enabling a complete workflow that integrates routing and post-processing.

```python
pipeline = SequentialChain(
    chains=[pre_chain, routing_chain, post_chain],
    input_variables=["raw_input"],
    output_variables=["routed_response", "recommendations"],
)

query = "What are the benefits of AI in education?"
results = pipeline.run({"raw_input": query})

print("\nRouted Response:", results["routed_response"])
print("\nRecommendations:", results["recommendations"])
```

---

## **Expected Output**

```plaintext
Routed Response:
AI in education improves personalized learning, enhances accessibility, and provides data-driven insights for educators.

Recommendations:
1. Implement AI-powered personalized learning platforms.
2. Use AI to create accessible educational resources for diverse learners.
3. Leverage AI analytics to support data-driven decision-making in schools.
```

---

## **Why This is Powerful**

1. **Dynamic Workflow Selection**:
   - Routes queries to appropriate workflows, ensuring optimal processing for different use cases.

2. **Seamless Integration**:
   - Combines LangSwarm’s routing capabilities with LangChain for downstream workflows.

3. **Scalability**:
   - Easily extend routing logic to include additional workflows (e.g., consensus, aggregation).

With LangSwarm’s `LLMRouting`, you can build dynamic pipelines that adapt to diverse AI workflows, combining the best of LangSwarm and LangChain. 
