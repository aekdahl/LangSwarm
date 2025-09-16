# BigQuery Vector Search MCP Tool

## Description

Provides vector similarity search capabilities over BigQuery datasets with embeddings. This tool enables semantic search through stored document embeddings using cosine similarity.

## Instructions

**Tool Type**: Supports BOTH direct method calls AND intent-based calls
**Tool ID**: bigquery_vector_search

### Available Methods:
- **similarity_search**: Perform semantic vector similarity search using embeddings
  - Required: `query` (string) - The search text
  - Optional: `limit` (integer) - Maximum results to return (uses your configured value)
  - Optional: `similarity_threshold` (float) - Minimum similarity score (uses your configured value)
- **list_datasets**: List available BigQuery datasets with vector data
  - No parameters required
- **get_content**: Retrieve full document content by ID
  - Required: `document_id` (string) - The unique document identifier
- **get_embedding**: Generate embeddings for text
  - Required: `text` (string) - Text to generate embeddings for

### Response Format

You MUST respond using this exact format:

{
  "response": "Your human-readable explanation of what you're doing",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "method_name",
    "params": { }
  }
}

OR for intent-based calls:

{
  "response": "Your human-readable explanation of what you're doing", 
  "mcp": {
    "tool": "bigquery_vector_search",
    "intent": "Natural language description of what to do",
    "context": "Additional context if needed"
  }
}

## Usage Examples

### 1. Direct Method Calls

#### Similarity Search
**User**: "Search for information about refund policies"
**Your Response**:
{
  "response": "I'll search for information about refund policies in the knowledge base.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search",
    "params": {
      "query": "refund policies",
      "limit": 10,
      "similarity_threshold": 0.01
    }
  }
}

#### List Datasets
**User**: "What datasets are available?"
**Your Response**:
{
  "response": "I'll list the available datasets in BigQuery.",
  "mcp": {
    "tool": "bigquery_vector_search", 
    "method": "list_datasets",
    "params": {}
  }
}

#### Get Content
**User**: "Get me the full content of document doc_12345"
**Your Response**:
{
  "response": "I'll retrieve the full content for document doc_12345.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "get_content", 
    "params": {
      "document_id": "doc_12345"
    }
  }
}

### 2. Intent-Based Calls

#### Search Intent
**User**: "Find information about enterprise pricing"
**Your Response**:
{
  "response": "I'll search for information about enterprise pricing for you.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "intent": "Search for enterprise pricing information",
    "context": "pricing, enterprise plans, costs"
  }
}

#### Dataset Exploration Intent  
**User**: "Show me what's in the knowledge base"
**Your Response**:
{
  "response": "I'll show you what datasets are available in the knowledge base.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "intent": "Show available datasets and their contents", 
    "context": "knowledge base exploration"
  }
}

## Parameter Requirements

### similarity_search
- **query** (required): The search text - use this exact field name
- **limit** (optional): Number of results (default: 10)
- **similarity_threshold** (optional): Minimum similarity score (default: 0.01)

### list_datasets  
- **pattern** (optional): Filter pattern for dataset names

### get_content
- **document_id** (required): Unique document identifier

### get_embedding
- **text** (required): Text to generate embeddings for
- **model** (optional): Embedding model to use

## ⚠️ Critical Rules

1. **ALWAYS use "query" parameter** - NOT "keyword", "search", "text", or "search_term"
2. **ALWAYS include the "response" field** with human-readable explanation
3. **NEVER nest MCP structures** inside params
4. **Use exact tool name**: "bigquery_vector_search" 
5. **Choose direct OR intent** - don't mix both in same call

## Common Mistake Examples

❌ **WRONG** - Missing response field:
{
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search", 
    "params": {"query": "refunds"}
  }
}

❌ **WRONG** - Wrong parameter name:
{
  "response": "Searching...",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search",
    "params": {"search_term": "refunds"}  // Should be "query"
  }
}

❌ **WRONG** - Nested MCP structure:
{
  "response": "Searching...",
  "mcp": {
    "tool": "bigquery_vector_search", 
    "method": "similarity_search",
    "params": {
      "mcp": {
        "method": "similarity_search",
        "params": {"query": "refunds"}
      }
    }
  }
}

## Usage Context

- Use when searching company knowledge bases stored in BigQuery
- Use for semantic search that understands context and meaning  
- Use when exploring available datasets and their contents
- Use for retrieving specific documents by ID
- Perfect for question-answering about company policies, documentation, or procedures

## Expected Output

- **similarity_search**: Ranked list of similar documents with content, URLs, titles, and similarity scores
- **list_datasets**: Available datasets and their metadata
- **get_content**: Full document content with metadata  
- **get_embedding**: Vector embeddings for the provided text

## Error Handling

If you encounter errors, provide helpful guidance to the user:

### Method Not Found
If a method doesn't exist, suggest the correct method:
- "search" → use "similarity_search"
- "find" → use "similarity_search" 
- "document" → use "get_content"
- "datasets" → use "list_datasets"
- "embed" → use "get_embedding"

### Missing Parameters
If parameters are missing, show the correct format:
- For similarity_search: `{"query": "your search text"}` (limit and similarity_threshold will use your configured defaults)
- For get_content: `{"document_id": "your_document_id"}`
- For get_embedding: `{"text": "your text to embed"}`

### Example Error Response
When an error occurs, respond like this:
{
  "response": "I encountered an error with the BigQuery search. The method 'search' is not available. Did you mean 'similarity_search'? Here's the correct format: {\"query\": \"your search text\", \"limit\": 5}",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search",
    "params": {"query": "corrected search query", "limit": 5}
  }
}

## Brief

BigQuery vector search for semantic knowledge retrieval using embeddings and cosine similarity.