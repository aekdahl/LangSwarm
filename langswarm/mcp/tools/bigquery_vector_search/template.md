# BigQuery Vector Search MCP Tool

## Description

Advanced semantic search tool that finds relevant documents using AI embeddings. Instead of exact keyword matching, this tool understands the meaning and context of your search to find the most relevant information in the knowledge base.

**Key Capabilities:**
- Semantic search (understands context, not just keywords)
- Document retrieval by ID
- Dataset exploration and discovery
- Embedding generation for text analysis

## Instructions

**Tool Type**: Supports BOTH direct method calls AND intent-based calls  
**Tool ID**: `bigquery_vector_search`

### When to Use This Tool

✅ **Perfect for:**
- Finding company policies, procedures, or documentation
- Answering questions about products, services, or support
- Searching knowledge bases with natural language queries
- Exploring what information is available in datasets
- Retrieving specific documents when you have their ID

❌ **Not for:**
- Real-time data queries (use current date/time APIs instead)
- Creating or modifying documents (read-only tool)
- Mathematical calculations (use calculation tools instead)

### Available Methods

#### 1. **similarity_search** - Main Search Function
**Purpose**: Find documents similar to your search query using AI understanding
**Required Parameters:**
- `query` (string) - Your search question or keywords in natural language

**Optional Parameters:**
- `limit` (integer) - How many results to return (default: configured value)
- `similarity_threshold` (float) - Minimum relevance score 0-1 (default: configured value)

**Best Practices:**
- Use natural language: "refund policy for cancelled orders" vs "refund cancel"
- Be specific: "enterprise pricing plans" vs "pricing"
- Include context: "mobile app login issues" vs "login"

#### 2. **list_datasets** - Explore Available Data
**Purpose**: See what datasets and information are available
**Parameters**: None required (always works with empty params)

#### 3. **get_content** - Retrieve Specific Document
**Purpose**: Get the full content of a specific document when you have its ID
**Required Parameters:**
- `document_id` (string) - The unique identifier from search results

#### 4. **get_embedding** - Generate AI Embeddings
**Purpose**: Convert text into AI embeddings for analysis
**Required Parameters:**
- `text` (string) - The text to convert to embeddings

### Response Format Requirements

**CRITICAL**: You MUST always include both `response` and `mcp` fields:


{
  "response": "Human-readable explanation of what you're doing and why",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "method_name",
    "params": { "your": "parameters" }
  }
}


**Alternative - Intent-Based Format:**

{
  "response": "Human-readable explanation of what you're doing",
  "mcp": {
    "tool": "bigquery_vector_search", 
    "intent": "Natural language description of the search goal",
    "context": "Additional keywords or context"
  }
}


## Usage Examples

### Example 1: Customer Support Query
**User**: "How do I return a damaged product?"
**Your Response**:

{
  "response": "I'll search our knowledge base for information about returning damaged products.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search",
    "params": {
      "query": "return damaged product refund policy",
      "limit": 5
    }
  }
}


### Example 2: Exploring Available Information
**User**: "What kind of information do you have access to?"
**Your Response**:

{
  "response": "Let me show you what datasets and information are available in our knowledge base.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "list_datasets",
    "params": {}
  }
}


### Example 3: Following Up on Search Results
**User**: "Can you get me the full details from that first document?"
**Your Response** (assuming you have document_id from previous search):

{
  "response": "I'll retrieve the complete content of that document for you.",
  "mcp": {
    "tool": "bigquery_vector_search", 
    "method": "get_content",
    "params": {
      "document_id": "d7de6e72afb2d9c169bd95d0f416d210_12"
    }
  }
}


### Example 4: Intent-Based Search
**User**: "Find pricing information for business customers"
**Your Response**:

{
  "response": "I'll search for business pricing information in our knowledge base.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "intent": "Find business and enterprise pricing information",
    "context": "business customers, enterprise plans, pricing tiers, cost"
  }
}


## Parameter Requirements

### similarity_search Parameters
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `query` | string | ✅ **Required** | Your search question or keywords | "refund policy for cancelled orders" |
| `limit` | integer | ❌ Optional | Number of results (1-50) | 10 |
| `similarity_threshold` | float | ❌ Optional | Minimum relevance (0.0-1.0) | 0.7 |

### get_content Parameters
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `document_id` | string | ✅ **Required** | Document ID from search results | "abc123_0" |

### get_embedding Parameters
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `text` | string | ✅ **Required** | Text to convert to embeddings | "customer support policy" |

### list_datasets Parameters
No parameters required - always use empty params: `{}`

## ⚠️ Critical Rules - Follow These Exactly

1. **ALWAYS use "query" parameter** - Never use "search", "keyword", "text", or "search_term"
2. **ALWAYS include "response" field** - Explain what you're doing in human language
3. **NEVER nest MCP calls** - No MCP structures inside params
4. **Use exact tool name** - Must be "bigquery_vector_search" 
5. **Choose direct OR intent** - Don't mix method and intent in same call
6. **Natural language queries work best** - "how to cancel subscription" vs "cancel"

## Common Mistakes to Avoid

### ❌ WRONG - Missing response field:

{
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search",
    "params": {"query": "refunds"}
  }
}


### ✅ CORRECT - Always include response:

{
  "response": "I'll search for refund information in our knowledge base.",
  "mcp": {
    "tool": "bigquery_vector_search", 
    "method": "similarity_search",
    "params": {"query": "refunds"}
  }
}


### ❌ WRONG - Using incorrect parameter name:

{
  "response": "Searching...",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search", 
    "params": {"search_term": "refunds"}  // Should be "query"
  }
}


### ❌ WRONG - Nested MCP structure:

{
  "response": "Searching...",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search",
    "params": {
      "mcp": {  // Never put MCP inside params
        "method": "similarity_search",
        "params": {"query": "refunds"}
      }
    }
  }
}


## Expected Output Types

### similarity_search Results
Returns a ranked list of relevant documents with:
- **Document content** - The actual text content
- **Similarity score** - How relevant it is (0.0-1.0)
- **Document ID** - For retrieving full content later
- **Metadata** - URL, title, creation date, source information
- **Total results** - How many documents were found

### list_datasets Results  
Returns information about available datasets:
- **Dataset names** - What datasets exist
- **Table information** - What tables are available
- **Record counts** - How much data is available
- **Schema details** - What fields are available

### get_content Results
Returns complete document information:
- **Full text content** - The entire document
- **All metadata** - Complete information about the document
- **Source information** - Where it came from, when it was created

### get_embedding Results
Returns AI vector embeddings:
- **Embedding vector** - Array of numbers representing the text
- **Dimensions** - Size of the embedding vector
- **Model information** - Which AI model was used

## Error Handling

When you encounter parameter validation errors, help the user by suggesting corrections:

### Method Not Found
If user tries unknown methods, suggest correct ones:
- "search" → use "similarity_search"
- "find" → use "similarity_search"
- "document" → use "get_content"
- "datasets" → use "list_datasets"
- "embed" → use "get_embedding"

### Missing Required Parameters
Guide users to include required parameters:
- **similarity_search**: Must include "query"
- **get_content**: Must include "document_id"  
- **get_embedding**: Must include "text"

### Example Error Recovery
If a user provides wrong parameters, respond like this:

{
  "response": "I encountered an issue with the search parameters. The parameter should be 'query' not 'search_term'. Let me fix that and search for information about refunds.",
  "mcp": {
    "tool": "bigquery_vector_search",
    "method": "similarity_search", 
    "params": {"query": "refund policy information", "limit": 5}
  }
}


## Brief

Advanced semantic search tool using AI embeddings to find relevant documents in BigQuery datasets. Understands context and meaning, not just keywords, for intelligent knowledge base querying.