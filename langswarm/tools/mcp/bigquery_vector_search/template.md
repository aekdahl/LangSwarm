# BigQuery Vector Search Tool

## Description

Advanced semantic search tool for exploring knowledge bases using AI-powered vector similarity. Searches through company documentation, policies, and content stored in BigQuery.

## Instructions

This tool provides semantic search capabilities for your knowledge base with two calling approaches:

### Direct Method Calling (Precise Control)

Use **`bigquery_vector_search.similarity_search`** when you have specific search terms:

**Parameters:**
- `query` (required): The search terms or question
- `limit` (optional): Number of results to return (default: 10)
- `similarity_threshold` (optional): Minimum relevance score 0-1 (default: 0.3)

**When to use:**
- User asks with clear keywords: "Find refund policy"
- Specific document lookups: "Show pricing documentation"
- Direct factual queries: "What are our API rate limits?"

**Examples:**
- "Find documents about employee benefits" → query="employee benefits", limit=5
- "Show me refund policies" → query="refund policy", limit=10

### Intent-Based Calling (Smart Interpretation)

Use **`bigquery_vector_search`** with natural language intent when the user's question is vague or exploratory:

**Parameters:**
- `query`: General search terms
- `intent`: What the user is trying to find or understand
- `context`: The domain or topic area

**When to use:**
- Vague questions: "What does Jacy'z offer?"
- Exploratory queries: "Tell me about our company policies"
- Contextual searches: "How do we handle customer complaints?"

**Examples:**
- "What's our stance on data privacy?" → intent="understand company data privacy policy", context="compliance, customer data"
- "Tell me about Jacy'z" → intent="get general company information", context="company overview"

### Other Available Methods

**`bigquery_vector_search.get_content`** - Retrieve specific document by ID
- Use when: You know the exact document ID from a previous search

**`bigquery_vector_search.list_datasets`** - Show available knowledge base datasets
- Use when: User asks "what can you search?" or "what information do you have?"

**`bigquery_vector_search.get_embedding`** - Get vector embedding for text
- Use when: Technical operations requiring embeddings (rare in normal use)

### Decision Guide

Choose your approach based on the user's question:

**Direct calling** = User knows what they want  
**Intent-based** = User is exploring or asking vaguely

When in doubt, start with intent-based calling for better user experience.

## Brief

Semantic search with intelligent intent processing for knowledge base exploration.
