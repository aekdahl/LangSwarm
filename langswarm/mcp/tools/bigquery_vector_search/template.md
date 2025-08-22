# BigQuery Vector Search MCP Tool

## Description
Provides vector similarity search capabilities over BigQuery datasets with embeddings. This tool enables semantic search through stored document embeddings using cosine similarity.

## Capabilities
- **Similarity Search**: Find semantically similar content using vector embeddings
- **Dataset Management**: List and inspect available vector datasets
- **Content Retrieval**: Get full document content by ID
- **Dataset Information**: Get detailed metadata about datasets and tables

## Configuration
Required environment variables:
- `GOOGLE_CLOUD_PROJECT`: GCP project ID containing BigQuery datasets
- `OPENAI_API_KEY`: OpenAI API key for embedding generation (if needed)

Optional configuration:
- Default dataset: `vector_search`
- Default table: `embeddings`
- Default similarity threshold: `0.7`

## Usage Examples

### Similarity Search
Find content similar to a query:
```json
{
  "task": "similarity_search",
  "query": "What is our refund policy?",
  "limit": 5,
  "similarity_threshold": 0.8
}
```

### List Available Datasets
Get all vector datasets:
```json
{
  "task": "list_datasets",
  "pattern": "vector"
}
```

### Get Document Content
Retrieve full content by ID:
```json
{
  "task": "get_content",
  "document_id": "doc_12345"
}
```

## Schema Requirements
The BigQuery table must have the following schema:
- `document_id` (STRING): Unique document identifier
- `content` (STRING): Document content
- `url` (STRING): Source URL
- `title` (STRING): Document title
- `embedding` (REPEATED FLOAT): Vector embedding
- `metadata` (STRING): JSON metadata
- `created_at` (TIMESTAMP): Creation timestamp

## Integration
This tool integrates with LangSwarm agents to provide semantic search capabilities over company knowledge bases stored in BigQuery.
