---
title: Voting with a LangChain
sidebar_position: 104
---

# Voting with a LangChain

This tutorial demonstrates how to use **LangSwarm's LLMVoting** within a LangChain pipeline. By leveraging LangSwarm’s voting capabilities, we can select the best response from multiple agents and process the selected response in LangChain for further refinement.

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
2. Utilize LangSwarm’s `LLMVotingChain` to vote on responses from multiple agents.
3. Integrate a post-processing step with LangChain to refine the selected response.
4. Combine all steps into a LangChain `SequentialChain` pipeline for a unified workflow.

---

## **Full Code**

```python
"""
LangSwarm + LangChain Pipeline Tutorial: Voting Swarm

This tutorial demonstrates how to use LangSwarm's LangChain-compatible tools
to include `LLMVoting` directly in a LangChain pipeline with pre- and post-processing steps.

Key Features:
- Use LangSwarm’s built-in LangChain-compatible voting chain.
- Pre-processing and post-processing steps in the pipeline.
- Select the best response from multiple agents using a voting mechanism.
"""

# Import necessary libraries
from langswarm.chains import LLMVotingChain  # LangSwarm's LangChain-compatible voting chain
from langchain.prompts import PromptTemplate  # LangChain prompt templates
from langchain.chains import SequentialChain, LLMChain  # LangChain pipeline framework
from langchain.llms import OpenAI  # LangChain OpenAI LLM

# Step 1: Pre-processing Chain
"""
The pre-processing chain ensures the input is clean and formatted before voting.
"""
pre_prompt = PromptTemplate(
    input_variables=["raw_input"],
    template="Clean and standardize the following input for analysis:\n\n{raw_input}"
)
pre_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=pre_prompt)

# Step 2: Voting Chain
"""
Use LangSwarm's LangChain-compatible `LLMVotingChain` to select the best response
from multiple agents.
"""
voting_chain = LLMVotingChain(
    agents=[
        {"model": "gpt-4", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo-instruct", "api_key": "your_openai_api_key"},
    ]
)

# Step 3: Post-processing Chain
"""
The post-processing chain refines the voted response and generates actionable insights.
"""
post_prompt = PromptTemplate(
    input_variables=["voted_response"],
    template=(
        "Based on the selected response:\n\n"
        "{voted_response}\n\n"
        "Provide three actionable recommendations to address the topic."
    )
)
post_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=post_prompt)

# Step 4: Build the LangChain Pipeline
"""
Combine the pre-processing, voting, and post-processing steps into a LangChain pipeline.
"""
pipeline = SequentialChain(
    chains=[pre_chain, voting_chain, post_chain],
    input_variables=["raw_input"],
    output_variables=["voted_response", "recommendations"],
)

# Step 5: Run the Pipeline
"""
Run the pipeline on a query, demonstrating the complete multi-agent workflow.
"""
query = "What are the key benefits of remote work?"
results = pipeline.run({"raw_input": query})

# Display the results
print("\nVoted Response:", results["voted_response"])
print("\nRecommendations:", results["recommendations"])
```

---

## **Code Walkthrough**

### **Step 1: Pre-processing Chain**
The pre-processing chain formats the input query to ensure it is standardized before being passed to the voting swarm. This step uses LangChain’s `LLMChain`.

```python
pre_prompt = PromptTemplate(
    input_variables=["raw_input"],
    template="Clean and standardize the following input for analysis:\n\n{raw_input}"
)
pre_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=pre_prompt)
```

---

### **Step 2: Voting Chain**
LangSwarm’s `LLMVotingChain` queries multiple agents and selects the best response using a voting mechanism. This ensures that the output reflects the majority's decision or the highest-quality response.

```python
voting_chain = LLMVotingChain(
    agents=[
        {"model": "gpt-4", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo", "api_key": "your_openai_api_key"},
        {"model": "gpt-3.5-turbo-instruct", "api_key": "your_openai_api_key"},
    ]
)
```

---

### **Step 3: Post-processing Chain**
The post-processing chain refines the selected response and generates actionable recommendations based on the voted output.

```python
post_prompt = PromptTemplate(
    input_variables=["voted_response"],
    template=(
        "Based on the selected response:\n\n"
        "{voted_response}\n\n"
        "Provide three actionable recommendations to address the topic."
    )
)
post_chain = LLMChain(llm=OpenAI(model="gpt-3.5-turbo"), prompt=post_prompt)
```

---

### **Step 4: Build and Run the Pipeline**
The pipeline combines all steps—pre-processing, voting, and post-processing—into a unified LangChain workflow. The query is processed, the best response is selected via voting, and actionable recommendations are generated.

```python
pipeline = SequentialChain(
    chains=[pre_chain, voting_chain, post_chain],
    input_variables=["raw_input"],
    output_variables=["voted_response", "recommendations"],
)

query = "What are the key benefits of remote work?"
results = pipeline.run({"raw_input": query})

print("\nVoted Response:", results["voted_response"])
print("\nRecommendations:", results["recommendations"])
```

---

## **Expected Output**

```plaintext
Voted Response:
Remote work increases productivity, enhances work-life balance, and reduces commuting-related stress.

Recommendations:
1. Implement flexible scheduling policies to maximize productivity.
2. Provide remote work resources, such as ergonomic equipment and IT support.
3. Encourage regular team check-ins to maintain collaboration and morale.
```

---

## **Why This is Powerful**

1. **Democratic Decision-Making**:
   - Selects the best response using a robust voting mechanism among multiple agents.

2. **Seamless Integration**:
   - Combines LangSwarm’s voting capabilities with LangChain for post-processing.

3. **Scalability**:
   - Easily add more agents or refine the pipeline for specific use cases.

With LangSwarm’s `LLMVotingChain`, you can confidently select the best outputs from multiple agents and refine them in LangChain workflows for actionable results.
