# BigQuery Vector Search Tool - Built-in Integration

**Status**: ✅ **AVAILABLE** as built-in tool  
**Tool Type**: `mcpbigquery_vector_search`  
**Version**: LangSwarm 0.0.54.dev4+

## 🎯 **Overview**

The BigQuery Vector Search tool is now a **built-in LangSwarm tool** that provides semantic search capabilities over BigQuery datasets with vector embeddings. No manual registration required!

## 🚀 **Quick Start**

### **1. Install Dependencies**

```bash
# Required for BigQuery access
pip install google-cloud-bigquery openai

# Or install LangSwarm with BigQuery extras
pip install langswarm[bigquery]
```

### **2. Environment Setup**

```bash
# Required environment variables
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export OPENAI_API_KEY="your-openai-api-key"  # For embedding generation
```

### **3. Simple Configuration**

```yaml
# langswarm.yaml
version: "1.0"
project_name: "knowledge-search-bot"

agents:
  - id: "knowledge_agent"
    agent_type: "langchain-openai"
    model: "gpt-4o"
    system_prompt: |
      You are a knowledge base assistant. When users ask questions, 
      search the knowledge base using the bigquery_search tool.
      
      Always respond in JSON format:
      {
        "response": "I'll search our knowledge base for that information.",
        "mcp": {
          "tool": "bigquery_search",
          "method": "similarity_search",
          "params": {
            "query": "user's question",
            "limit": 5,
            "similarity_threshold": 0.7
          }
        }
      }
    tools:
      - bigquery_search

tools:
  - id: bigquery_search
    type: mcpbigquery_vector_search  # ← Built-in tool type!
    description: "Search company knowledge base using vector similarity"
    config:
      project_id: "your-gcp-project"
      dataset_id: "vector_search"
      table_name: "embeddings"
      similarity_threshold: 0.7
      max_results: 10

workflows:
  knowledge_chat:
    - id: chat_step
      steps:
        - id: agent_chat
          agent: knowledge_agent
          input: ${context.user_input}
          output:
            to: user
```

### **4. Usage Example**

```python
# app.py
import asyncio
from langswarm.core.config import LangSwarmConfigLoader

async def main():
    # Load configuration - BigQuery tool loads automatically!
    loader = LangSwarmConfigLoader("langswarm.yaml")
    workflows, agents, brokers, tools, tools_metadata = loader.load()
    
    # Get your agent
    agent = agents["knowledge_agent"]
    
    # Test the knowledge search
    response = agent.chat("What is our refund policy?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 **Configuration Options**

### **Required BigQuery Table Schema**

Your BigQuery table must have this schema:

```sql
CREATE TABLE `your_project.vector_search.embeddings` (
  document_id STRING,              -- Unique document identifier
  content STRING,                  -- Document text content
  url STRING,                      -- Source URL
  title STRING,                    -- Document title
  embedding ARRAY<FLOAT64>,        -- Vector embeddings
  metadata STRING,                 -- JSON metadata
  created_at TIMESTAMP             -- Creation timestamp
);
```

### **Tool Configuration Parameters**

| **Parameter** | **Description** | **Default** | **Required** |
|---------------|-----------------|-------------|--------------|
| `project_id` | GCP project ID | `GOOGLE_CLOUD_PROJECT` env var | ✅ |
| `dataset_id` | BigQuery dataset name | `"vector_search"` | ❌ |
| `table_name` | BigQuery table name | `"embeddings"` | ❌ |
| `similarity_threshold` | Minimum similarity score | `0.7` | ❌ |
| `max_results` | Maximum results to return | `50` | ❌ |
| `embedding_model` | OpenAI embedding model | `"text-embedding-3-small"` | ❌ |

### **Full Configuration Example**

```yaml
tools:
  - id: advanced_bigquery_search
    type: mcpbigquery_vector_search
    description: "Advanced BigQuery vector search with custom settings"
    config:
      project_id: "production-project"
      dataset_id: "knowledge_base"
      table_name: "document_embeddings"
      similarity_threshold: 0.8
      max_results: 20
      embedding_model: "text-embedding-3-large"
```

## 🛠️ **Available Methods**

The BigQuery tool provides these methods for agent use:

### **1. similarity_search**
Find semantically similar content:
```json
{
  "tool": "bigquery_search",
  "method": "similarity_search",
  "params": {
    "query": "What is our refund policy?",
    "limit": 5,
    "similarity_threshold": 0.8
  }
}
```

### **2. get_content**
Retrieve document by ID:
```json
{
  "tool": "bigquery_search", 
  "method": "get_content",
  "params": {
    "document_id": "doc_12345"
  }
}
```

### **3. list_datasets**
List available datasets:
```json
{
  "tool": "bigquery_search",
  "method": "list_datasets",
  "params": {
    "pattern": "knowledge"
  }
}
```

### **4. dataset_info**
Get dataset metadata:
```json
{
  "tool": "bigquery_search",
  "method": "dataset_info", 
  "params": {
    "dataset_id": "vector_search",
    "table_name": "embeddings"
  }
}
```

## 🧪 **Testing Your Setup**

Use the provided test script to verify everything works:

```bash
# Run the integration test
python test_bigquery_integration.py
```

Expected output:
```
🧪 Testing BigQuery Vector Search Tool Integration

=== Testing BigQuery Dependencies ===
✅ google-cloud-bigquery is available
✅ openai is available
✅ BigQueryVectorSearchMCPTool imported successfully

=== Testing BigQuery Tool Registration ===
Available tool types: ['mcpfilesystem', 'mcpgithubtool', 'mcpforms', 'mcpbigquery_vector_search', ...]
✅ BigQuery Vector Search tool is registered as built-in tool
✅ Configuration loaded successfully with BigQuery tool
✅ Agent successfully loaded with BigQuery tool

🎉 All tests passed! BigQuery Vector Search tool is working correctly.
```

## 🔍 **Troubleshooting**

### **Common Issues**

1. **"BigQuery Vector Search tool not available"**
   ```bash
   # Solution: Install dependencies
   pip install google-cloud-bigquery openai
   ```

2. **"No module named 'google.cloud'"**
   ```bash
   # Solution: Install Google Cloud SDK
   pip install google-cloud-bigquery
   ```

3. **"project_id is required"**
   ```bash
   # Solution: Set environment variable
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   ```

4. **"Tool not found in agent registry"**
   ```yaml
   # Solution: Check YAML configuration
   agents:
     - id: "agent_name"
       tools: ["bigquery_search"]  # ← Must match tool id
   
   tools:
     - id: "bigquery_search"       # ← Must match agent tools list
       type: mcpbigquery_vector_search
   ```

### **Debug Mode**

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed BigQuery tool loading information
from langswarm.core.config import LangSwarmConfigLoader
loader = LangSwarmConfigLoader("langswarm.yaml")
```

## 🎉 **Migration from Manual Registration**

If you were previously manually registering the BigQuery tool, you can now simplify:

### **Before (Manual Registration)**
```python
# Old approach - no longer needed!
from langswarm.mcp.tools.bigquery_vector_search.main import BigQueryVectorSearchMCPTool
loader.register_tool_class("bigquery_vector_search", BigQueryVectorSearchMCPTool)
```

### **After (Built-in Tool)**
```yaml
# New approach - just use in YAML!
tools:
  - id: bigquery_search
    type: mcpbigquery_vector_search  # ← Built-in type
```

## 📊 **Performance Notes**

- **Embedding Generation**: Uses OpenAI API if `query_embedding` not provided
- **Query Optimization**: Use specific search terms for better results
- **Result Limits**: Keep `limit` reasonable (5-20) for better performance
- **Similarity Threshold**: Start with 0.7, adjust based on result quality

## 🤝 **Support**

The BigQuery Vector Search tool is now a core part of LangSwarm. For issues:

1. **Check dependencies**: `pip list | grep google-cloud-bigquery`
2. **Run test script**: `python test_bigquery_integration.py`
3. **Enable debug logging**: `logging.basicConfig(level=logging.DEBUG)`
4. **Check tool registration**: `print(loader.tool_classes.keys())`

**The tool is production-ready and fully supported as part of LangSwarm's built-in tool ecosystem!** 🚀
