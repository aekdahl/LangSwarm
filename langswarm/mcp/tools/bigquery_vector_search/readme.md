# BigQuery Vector Search MCP Tool

## Overview

The BigQuery Vector Search MCP Tool provides intelligent knowledge base search capabilities using vector embeddings stored in BigQuery. It supports both direct API calls and natural language queries through LangSwarm workflows and agents.

## Features

### 🔍 **Intelligent Search Workflows**
- **Natural Language Processing**: Understands conversational queries and converts them to structured searches
- **Intent Classification**: Automatically determines what type of search operation is needed
- **Query Enhancement**: Improves search queries by adding synonyms and related terms
- **Context-Aware Responses**: Provides comprehensive answers based on search results

### 🛠️ **Direct Tool Operations**
- **Similarity Search**: Vector-based semantic search with configurable thresholds
- **Dataset Management**: List and inspect available datasets and tables
- **Document Retrieval**: Get full content by document ID
- **Dataset Information**: Detailed metadata about datasets and schemas

## Usage Examples

### Natural Language Queries

**Ask Questions:**
```
"What is our refund policy?"
"How do I integrate with the API?"
"Tell me about pricing plans"
```

**Browse Content:**
```
"What datasets are available?"
"Show me what's in the knowledge base"
"List all the indexed content"
```

**Get Specific Information:**
```
"Show me details about the customer_docs dataset"
"Get document doc_12345"
"What's the structure of the vector_search table?"
```

### Direct API Calls

**Similarity Search:**
```json
{
  "query": "API authentication methods",
  "limit": 10,
  "similarity_threshold": 0.8,
  "dataset_id": "docs",
  "table_name": "api_documentation"
}
```

**List Datasets:**
```json
{
  "pattern": "customer"
}
```

**Get Document:**
```json
{
  "document_id": "doc_12345",
  "dataset_id": "support_docs",
  "table_name": "faq_embeddings"
}
```

## Workflow Architecture

### Main Workflows

1. **`intelligent_search_workflow`**: Complete NLP processing pipeline
   - Input normalization
   - Intent classification
   - Parameter extraction
   - Query enhancement
   - Search execution
   - Response formatting

2. **`quick_search_workflow`**: Fast similarity search for simple questions
   - Query enhancement
   - Direct similarity search
   - Formatted response

3. **`browse_knowledge_workflow`**: Explore available content
   - List all datasets
   - Format overview

4. **`document_retrieval_workflow`**: Get specific documents
   - Extract document ID
   - Retrieve content
   - Format response

5. **`dataset_inspection_workflow`**: Inspect dataset metadata
   - Extract dataset parameters
   - Get detailed information
   - Format technical details

### Agents

- **`input_normalizer`**: Handles multiple input formats
- **`search_intent_classifier`**: Determines operation type
- **`query_extractor`**: Extracts search parameters
- **`context_enhancer`**: Improves search queries
- **`parameter_builder`**: Constructs API calls
- **`search_response_formatter`**: Creates user-friendly responses
- **`error_handler`**: Provides helpful error guidance

## Configuration

### Environment Variables
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
OPENAI_API_KEY=your-openai-key
```

### BigQuery Schema Requirements
Tables must include:
- `document_id` (STRING): Unique identifier
- `content` (STRING): Document content
- `url` (STRING): Source URL
- `title` (STRING): Document title
- `embedding` (REPEATED FLOAT): Vector embeddings
- `metadata` (STRING): JSON metadata
- `created_at` (TIMESTAMP): Creation date

## Integration with LangSwarm

### In Agent Configuration
```yaml
tools:
  - name: "knowledge_search"
    type: "local_mcp"
    description: "Search company knowledge base"
    mcp_server: "bigquery_vector_search"
    enabled: true
```

### Workflow Usage
```python
# Use in workflow executor
executor.run_workflow("intelligent_search_workflow", 
                     user_input="What are our API rate limits?")

# Quick search
executor.run_workflow("quick_search_workflow", 
                     user_input="pricing information")

# Browse available content
executor.run_workflow("browse_knowledge_workflow")
```

## Advanced Features

### Query Enhancement
Automatically expands queries with related terms:
- "API docs" → "API documentation endpoints developer guide reference"
- "refund policy" → "refund return policy money back guarantee cancellation"

### Smart Error Handling
Provides contextual help when searches fail:
- Suggests alternative keywords
- Explains availability of datasets
- Guides users to successful searches

### Multiple Input Formats
Supports both structured JSON and natural language:
- Direct API calls with JSON parameters
- Conversational queries in plain English
- Mixed input with `user_input` and `user_query`

## Performance Optimization

- **Similarity Threshold**: Adjustable relevance filtering (0.1-1.0)
- **Result Limiting**: Configurable result counts
- **Dataset Targeting**: Search specific datasets for faster results
- **Query Caching**: Leverages BigQuery's caching for repeated searches

## Error Handling

The tool provides comprehensive error handling:
- **Connection Issues**: Graceful degradation with retry suggestions
- **No Results**: Alternative search strategies
- **Invalid Parameters**: Clear validation messages
- **Dataset Errors**: Helpful navigation guidance

## Development and Testing

### Local Development
```bash
# Run in local mode (for LangSwarm integration)
python langswarm/mcp/tools/bigquery_vector_search/main.py

# Run as HTTP server (for external testing)
uvicorn langswarm.mcp.tools.bigquery_vector_search.main:app --port 4021
```

### Testing Workflows
```python
from langswarm.workflows import WorkflowExecutor

executor = WorkflowExecutor()
result = executor.run_workflow("quick_search_workflow", 
                              user_input="test query")
print(result)
```

This BigQuery Vector Search MCP Tool bridges the gap between natural language queries and structured vector search, making knowledge base interactions intuitive and powerful for both users and agents.
