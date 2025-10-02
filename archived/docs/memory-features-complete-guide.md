# LangSwarm Memory Features Complete Guide

This comprehensive guide covers all memory features in LangSwarm, from basic setup to advanced session management, based on in-depth analysis of the codebase and practical testing.

## 📚 Table of Contents

1. [Memory Made Simple Overview](#memory-made-simple-overview)
2. [Memory Backends and Adapters](#memory-backends-and-adapters)
3. [Global Memory Configuration](#global-memory-configuration)
4. [Session-Scoped Unified Memory](#session-scoped-unified-memory)
5. [Memory vs Session Configuration Comparison](#memory-vs-session-configuration-comparison)
6. [BigQuery Setup Guide](#bigquery-setup-guide)
7. [Context Management Strategies](#context-management-strategies)
8. [Cost Optimization](#cost-optimization)
9. [Configuration Examples](#configuration-examples)
10. [Best Practices](#best-practices)

## 🎯 Memory Made Simple Overview

LangSwarm implements a **3-tier memory system** that simplifies configuration from basic development to enterprise deployment:

### Tier 1: Development Mode
```yaml
# Simplest possible configuration
memory: true
```
- **Backend**: Auto-selects SQLite (no setup required)
- **Use Case**: Local development, testing, prototyping
- **Storage**: Local file (`./langswarm_memory.db`)
- **Benefits**: Zero configuration, immediate functionality

### Tier 2: Environment-Based
```yaml
# Production-ready with auto-detection
memory: production
```
- **Backend**: Auto-detects based on environment variables
- **Auto-Detection Logic**:
  - `REDIS_URL` present → Redis backend
  - `GOOGLE_CLOUD_PROJECT` + `GOOGLE_APPLICATION_CREDENTIALS` → BigQuery
  - `ELASTICSEARCH_URL` → Elasticsearch
  - Fallback → SQLite
- **Use Case**: Staging, production with environment variables
- **Benefits**: Environment-aware, minimal configuration

### Tier 3: Full Control
```yaml
# Explicit backend configuration
memory:
  backend: "bigquery"
  settings:
    project_id: "my-project"
    dataset_id: "langswarm_data"
    table_id: "agent_conversations"
```
- **Backend**: Explicitly specified with custom settings
- **Use Case**: Enterprise deployments, custom requirements
- **Benefits**: Complete control, advanced features

## 🗄️ Memory Backends and Adapters

LangSwarm supports multiple memory backends through a unified adapter interface:

### Available Backends

| Backend | Module | Use Case | Setup Complexity |
|---------|--------|----------|------------------|
| **SQLite** | `langswarm.memory.adapters._langswarm.sqlite` | Development, small scale | ⭐ None |
| **Redis** | `langswarm.memory.adapters._langswarm.redis` | High-performance, caching | ⭐⭐ Medium |
| **ChromaDB** | `langswarm.memory.adapters._langswarm.chromadb` | Vector search, embeddings | ⭐⭐ Medium |
| **BigQuery** | `langswarm.memory.adapters._langswarm.bigquery` | Analytics, large scale | ⭐⭐⭐ High |
| **Elasticsearch** | `langswarm.memory.adapters._langswarm.elasticsearch` | Full-text search | ⭐⭐⭐ High |
| **Qdrant** | `langswarm.memory.adapters._langswarm.qdrant` | Vector database | ⭐⭐⭐ High |
| **GCS** | `langswarm.memory.adapters._langswarm.gcs` | Cloud storage | ⭐⭐⭐ High |

### Adapter Interface
All adapters implement the `DatabaseAdapter` interface:
```python
class DatabaseAdapter:
    def add_documents(self, documents: List[Document], **kwargs) -> List[str]:
        """Store documents and return IDs"""
        
    def query(self, query: str, k: int = 5, **kwargs) -> List[Document]:
        """Search and retrieve relevant documents"""
        
    def delete(self, document_ids: List[str] = None, **kwargs) -> bool:
        """Delete specific documents or all data"""
```

## 🌐 Global Memory Configuration

Global memory configuration provides **shared storage** for all agents in a workflow without requiring individual agent configuration.

### How It Works
```yaml
# langswarm.yaml
version: "1.0"

# 🎯 GLOBAL MEMORY - All agents inherit this automatically
memory:
  backend: "bigquery"
  settings:
    project_id: "enkl-uat"
    dataset_id: "langswarm_workflows"
    table_id: "all_agent_conversations"

# Your agents DON'T need individual memory config
agents:
  - id: "data_processor"
    model: "gpt-4o"
    behavior: "analytical"
  - id: "response_generator"
    model: "gpt-4o"
    behavior: "creative"

workflows:
  - steps:
      - agent: "data_processor"
        input: "${user_input}"
        output: {to: "analysis"}
      - agent: "response_generator"
        input: |
          Original request: ${user_input}
          Analysis: ${context.step_outputs.analysis}
```

### Key Characteristics
- ✅ **Shared Storage**: All agents write to same memory backend
- ✅ **No Per-Agent Config**: Zero configuration overhead
- ✅ **Workflow Orchestration**: Context passed via step references
- ❌ **Manual Context Assembly**: Requires explicit input templates
- ❌ **Limited Collaboration**: Agents don't automatically share context

### Use Cases
- **Document Processing Pipelines**: Where each step processes previous output
- **Data Transformation**: Clean → validate → process → output
- **Approval Workflows**: Sequential processing with audit trails
- **Batch Processing**: High-volume processing with shared storage

## 🔄 Session-Scoped Unified Memory

Session-Scoped Unified Memory provides **automatic context sharing** between agents within a defined scope, creating seamless collaboration.

### How It Works
```yaml
# langswarm.yaml
version: "1.0"

memory:
  backend: "bigquery"
  settings:
    project_id: "enkl-uat"
    dataset_id: "unified_sessions"
    table_id: "workflow_conversations"

session:
  unified_memory: true              # 🎯 KEY: Enable context sharing
  scope: "workflow"                 # Memory boundary
  sharing_strategy: "all"           # How much context to share
  context_window_management: "auto" # Prevent token overflow

agents:
  - id: "agent1"
    model: "gpt-4o"
  - id: "agent2"
    model: "gpt-4o"

workflows:
  - steps:
      - agent: "agent1"
        input: "${user_input}"
      - agent: "agent2"
        # Automatically receives full conversation context!
        input: "${user_input}"
```

### Key Characteristics
- ✅ **Automatic Context Sharing**: Agents see conversation history
- ✅ **Zero Configuration**: No manual context assembly required
- ✅ **Natural Collaboration**: Agents build on each other's work
- ⚠️ **Context Expansion**: Can lead to exponential token growth
- ⚠️ **Cost Implications**: Higher token usage than global memory

### Session Scoping Options

#### Workflow Scope (`scope: "workflow"`)
```yaml
session:
  scope: "workflow"
```
- **Boundary**: Memory isolated to single workflow execution
- **Privacy**: High - each workflow run is isolated
- **Use Case**: One-time tasks, stateless processing

#### User Scope (`scope: "user"`)
```yaml
session:
  scope: "user"
```
- **Boundary**: Memory shared across all workflows for a user
- **Privacy**: Medium - user-specific memory
- **Use Case**: Personal assistants, customer relationships

#### Global Scope (`scope: "global"`)
```yaml
session:
  scope: "global"
```
- **Boundary**: Memory shared across all users and workflows
- **Privacy**: Low - organizational knowledge base
- **Use Case**: Company knowledge bases, collective intelligence

### Sharing Strategies

#### All Strategy (`sharing_strategy: "all"`)
```yaml
session:
  sharing_strategy: "all"
```
- **Context**: Each agent sees complete session history
- **Token Impact**: Maximum context, maximum tokens
- **Use Case**: Complex collaboration, brainstorming

#### Sequential Strategy (`sharing_strategy: "sequential"`)
```yaml
session:
  sharing_strategy: "sequential"
```
- **Context**: Each agent sees only previous agent's output
- **Token Impact**: Limited context, controlled tokens
- **Cost Savings**: ~58% reduction vs "all" strategy
- **Use Case**: Linear workflows, cost optimization

#### Selective Strategy (`sharing_strategy: "selective"`)
```yaml
session:
  sharing_strategy: "selective"
```
- **Context**: Smart context based on relevance criteria
- **Token Impact**: Optimized context, balanced tokens
- **Use Case**: Large workflows with mixed collaboration needs

## ⚖️ Memory vs Session Configuration Comparison

| Aspect | Global Memory Config | Session-Scoped Unified Memory |
|--------|---------------------|-------------------------------|
| **Context Access** | ✅ Via explicit step references | ✅ Automatic session context |
| **Configuration** | ❌ Manual context assembly | ✅ Automatic context sharing |
| **Agent Autonomy** | ❌ Requires workflow design | ✅ Agents access context naturally |
| **Context Window** | ✅ Controlled, explicit | ⚠️ Can grow large |
| **Maintenance** | ❌ Complex workflow templates | ✅ Simple agent design |
| **Token Costs** | ✅ Predictable, controlled | ⚠️ Can be exponential |
| **Collaboration** | ⭐⭐ Good with proper design | ⭐⭐⭐ Excellent, automatic |
| **Scalability** | ✅ Linear growth | ❌ Exponential growth risk |

### Visual Comparison

#### Global Memory Approach
```
Agent 1: [User Input] → Output A
Agent 2: [User Input + Output A] → Output B  
Agent 3: [User Input + Output B] → Output C
```
**Context Growth**: Linear (User Input + 1 previous output)

#### Session-Scoped Approach
```
Agent 1: [User Input] → Output A
Agent 2: [User Input + Output A] → Output B
Agent 3: [User Input + Output A + Output B] → Output C
```
**Context Growth**: Exponential (Accumulating conversation history)

## 🔧 BigQuery Setup Guide

BigQuery provides enterprise-scale memory storage with powerful analytics capabilities.

### Prerequisites
1. **Google Cloud Project** with BigQuery API enabled
2. **Service Account** with BigQuery permissions
3. **Credentials** configured via environment variables

### Installation
```bash
# Install BigQuery dependency
pip install google-cloud-bigquery

# Or add to requirements.txt
echo "google-cloud-bigquery>=3.0.0" >> requirements.txt
pip install -r requirements.txt
```

### Google Cloud Setup

#### 1. Create Service Account
```bash
# Using gcloud CLI
gcloud iam service-accounts create langswarm-memory \
    --display-name="LangSwarm Memory Service Account"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:langswarm-memory@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor"

# Create and download key
gcloud iam service-accounts keys create ./langswarm-key.json \
    --iam-account=langswarm-memory@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

#### 2. Set Environment Variables
```bash
# Set credentials path
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/langswarm-key.json"

# Set project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### LangSwarm Configuration

#### Automatic Detection (Tier 2)
```yaml
# Auto-detects BigQuery if environment variables are set
memory: production
```

#### Explicit Configuration (Tier 3)
```yaml
memory:
  backend: "bigquery"
  settings:
    project_id: "enkl-uat"
    dataset_id: "langswarm_workflows"
    table_id: "agent_conversations"
    location: "US"  # Optional: BigQuery location
```

### BigQuery Schema
LangSwarm automatically creates tables with this schema:
```sql
CREATE TABLE `project.dataset.table` (
  id STRING NOT NULL,
  content STRING NOT NULL,
  metadata JSON,
  agent_id STRING,
  session_id STRING,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  embedding ARRAY<FLOAT64>  -- For vector search
);
```

### Verification Script
```python
#!/usr/bin/env python3
"""Verify BigQuery setup for LangSwarm"""

def test_bigquery_setup():
    try:
        # Test BigQuery import
        from google.cloud import bigquery
        print("✅ google-cloud-bigquery installed")
        
        # Test client connection
        client = bigquery.Client()
        print(f"✅ BigQuery client connected to project: {client.project}")
        
        # Test LangSwarm memory
        from langswarm.core.config import MemoryConfig
        config = MemoryConfig.setup_memory("production")
        print(f"✅ LangSwarm detected backend: {config.backend}")
        
        return True
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

if __name__ == "__main__":
    test_bigquery_setup()
```

## 🧠 Context Management Strategies

Context window management is critical for preventing token overflow and controlling costs in session-scoped memory.

### Auto Strategy (`context_window_management: "auto"`)
**Description**: LangSwarm automatically manages context based on model limits

**Behavior**:
- Monitor token usage per model (GPT-4: 8K, GPT-4-turbo: 128K, etc.)
- Truncate oldest messages when approaching limits
- Preserve critical context (user input, recent responses)
- Adjust based on model context window capabilities

**Pros**: Zero configuration, Model-aware, Safe defaults  
**Cons**: May lose important context, Generic truncation

**Configuration**:
```yaml
session:
  unified_memory: true
  context_window_management: "auto"
```

### Manual Strategy (`context_window_management: "manual"`)
**Description**: Full manual control over context

**Behavior**:
- No automatic truncation
- Session can grow until model limits
- Requires explicit context management in workflow
- Risk of context overflow errors

**Pros**: Complete control, No unexpected context loss  
**Cons**: Risk of errors, Requires expertise, Manual management

**Configuration**:
```yaml
session:
  unified_memory: true
  context_window_management: "manual"
  # Requires careful workflow design to manage context
```

### Smart Truncate Strategy (`context_window_management: "smart_truncate"`)
**Description**: Intelligent context pruning

**Behavior**:
- Analyze context relevance using semantic analysis
- Remove least important messages based on:
  - Recency (older messages less important)
  - Relevance to current task
  - Agent reasoning chains
- Preserve user intent and recent context

**Pros**: Preserves important context, Intelligent decisions  
**Cons**: More complex, May still lose context, Higher processing overhead

**Configuration**:
```yaml
session:
  unified_memory: true
  context_window_management: "smart_truncate"
  sharing_strategy: "all"  # Works well with full context sharing
```

### Summarize Strategy (`context_window_management: "summarize"`)
**Description**: Compress context through AI summarization

**Behavior**:
- Summarize older conversation segments when approaching limits
- Replace detailed history with AI-generated summaries
- Preserve recent full context (e.g., last 3-5 exchanges)
- Use separate AI calls to create summaries

**Pros**: Preserves information density, Compact representation  
**Cons**: Loss of detail, Additional AI costs for summarization, Potential information loss

**Configuration**:
```yaml
session:
  unified_memory: true
  context_window_management: "summarize"
  sharing_strategy: "sequential"  # Good for document processing
```

### Strategy Selection Guide

| Use Case | Recommended Strategy | Reasoning |
|----------|---------------------|-----------|
| **Development/Testing** | `auto` | Safe defaults, no configuration |
| **Cost-Sensitive** | `smart_truncate` | Intelligent cost control |
| **Document Processing** | `summarize` | Preserve information density |
| **Expert Users** | `manual` | Full control for optimization |
| **Long Sessions** | `smart_truncate` | Prevent gradual context loss |
| **High-Volume** | `auto` | Minimal overhead |

## 💰 Cost Optimization

Understanding and controlling token costs is crucial for production deployments.

### Token Growth Patterns

#### Linear Growth (Global Memory)
```
Agent 1: 100 tokens (user input)
Agent 2: 150 tokens (user input + output 1)
Agent 3: 200 tokens (user input + output 2)
Agent 4: 250 tokens (user input + output 3)
Total: 700 tokens
```

#### Exponential Growth (Session-Scoped "all")
```
Agent 1: 100 tokens (user input)
Agent 2: 350 tokens (user input + output 1)
Agent 3: 650 tokens (user input + outputs 1-2)  
Agent 4: 1000 tokens (user input + outputs 1-3)
Total: 2100 tokens (3x more expensive!)
```

#### Controlled Growth (Session-Scoped "sequential")
```
Agent 1: 100 tokens (user input)
Agent 2: 300 tokens (user input + output 1)
Agent 3: 150 tokens (user input + output 2)
Agent 4: 200 tokens (user input + output 3)
Total: 750 tokens (similar to Global Memory)
```

### Cost Optimization Strategies

#### 1. Choose Appropriate Sharing Strategy
```yaml
# For cost optimization
session:
  sharing_strategy: "sequential"  # 50-60% cost reduction
  
# For maximum collaboration (higher cost)
session:
  sharing_strategy: "all"         # Full context, full cost
```

#### 2. Enable Context Management
```yaml
session:
  context_window_management: "smart_truncate"
  # Prevents runaway token growth
```

#### 3. Monitor with Analytics
```yaml
session:
  enable_analytics: true
  # Track token usage patterns
```

#### 4. Set Reasonable Timeouts
```yaml
session:
  session_timeout: 3600  # 1 hour
  auto_cleanup: true     # Clean up expired sessions
```

#### 5. Use Appropriate Scope
```yaml
session:
  scope: "workflow"      # Isolated sessions (lower cost)
  # vs
  scope: "user"          # Accumulating sessions (higher cost)
```

### Cost Monitoring Query (BigQuery)
```sql
-- Monitor token usage by agent and session
SELECT 
  agent_id,
  session_id,
  COUNT(*) as message_count,
  SUM(JSON_EXTRACT_SCALAR(metadata, '$.token_count')) as total_tokens,
  AVG(JSON_EXTRACT_SCALAR(metadata, '$.token_count')) as avg_tokens_per_message,
  MIN(timestamp) as session_start,
  MAX(timestamp) as session_end
FROM `your_project.langswarm_workflows.agent_conversations`
WHERE DATE(timestamp) = CURRENT_DATE()
GROUP BY agent_id, session_id
ORDER BY total_tokens DESC;
```

## 📋 Configuration Examples

### 1. Development Setup
```yaml
# Simple development configuration
version: "1.0"
memory: true  # Auto-selects SQLite

agents:
  - id: "test_agent"
    model: "gpt-4o"

workflows:
  - steps:
      - agent: "test_agent"
```

### 2. Production with Auto-Detection
```yaml
# Production with environment-based detection
version: "1.0"
memory: production  # Auto-detects BigQuery/Redis/etc

session:
  unified_memory: true
  scope: "workflow"
  sharing_strategy: "sequential"
  enable_analytics: true

agents:
  - id: "processor"
    model: "gpt-4o"
  - id: "responder"
    model: "gpt-4o"
```

### 3. Cost-Optimized Configuration
```yaml
# Optimized for cost control
version: "1.0"

memory:
  backend: "bigquery"
  settings:
    project_id: "my-project"
    dataset_id: "cost_optimized"
    table_id: "workflows"

session:
  unified_memory: true
  scope: "workflow"
  sharing_strategy: "sequential"        # 58% cost reduction
  context_window_management: "smart_truncate"
  session_timeout: 1800                # 30 minutes
  auto_cleanup: true
  enable_analytics: true               # Monitor costs

agents:
  - id: "classifier"
    model: "gpt-4o-mini"               # Use smaller model where possible
  - id: "processor"  
    model: "gpt-4o"
  - id: "responder"
    model: "gpt-4o-mini"
```

### 4. High-Collaboration Configuration
```yaml
# Optimized for agent collaboration
version: "1.0"

memory:
  backend: "bigquery"
  settings:
    project_id: "collaboration-project"
    dataset_id: "team_workflows"
    table_id: "conversations"

session:
  unified_memory: true
  scope: "user"                        # Cross-workflow memory
  sharing_strategy: "all"              # Full collaboration
  context_window_management: "summarize"
  session_timeout: 7200               # 2 hours
  enable_search: true                 # Semantic search
  enable_analytics: true

agents:
  - id: "researcher"
    model: "gpt-4o"
    behavior: "thorough analysis"
  - id: "synthesizer"
    model: "gpt-4o"  
    behavior: "creative synthesis"
  - id: "validator"
    model: "gpt-4o"
    behavior: "critical evaluation"
```

### 5. High-Privacy Configuration
```yaml
# Maximum privacy and minimal persistence
version: "1.0"

memory:
  backend: "sqlite"  # Local only
  settings:
    database_path: "/tmp/secure_memory.db"

session:
  unified_memory: false               # No context sharing
  scope: "workflow"                   # Isolated workflows
  persist_session: false             # No persistence
  auto_cleanup: true                 # Immediate cleanup
  session_timeout: 900               # 15 minutes
  enable_analytics: false            # No analytics tracking

agents:
  - id: "secure_processor"
    model: "gpt-4o"
```

### 6. Document Processing Pipeline
```yaml
# Optimized for document processing
version: "1.0"

memory:
  backend: "bigquery"
  settings:
    project_id: "doc-processing"
    dataset_id: "document_workflows"
    table_id: "processing_history"

session:
  unified_memory: true
  scope: "workflow"
  sharing_strategy: "sequential"      # Perfect for pipelines
  context_window_management: "summarize"
  session_timeout: 14400             # 4 hours for large docs
  enable_analytics: true

agents:
  - id: "extractor"
    model: "gpt-4o"
    behavior: "extract key information"
  - id: "analyzer"
    model: "gpt-4o"
    behavior: "analyze extracted data"
  - id: "summarizer"
    model: "gpt-4o"
    behavior: "create executive summary"
  - id: "formatter"
    model: "gpt-4o-mini"
    behavior: "format final output"

workflows:
  - id: "document_pipeline"
    steps:
      - agent: "extractor"
        input: "${user_input}"
      - agent: "analyzer"
        input: "${user_input}"  # Gets previous context automatically
      - agent: "summarizer"
        input: "${user_input}"
      - agent: "formatter"
        input: "${user_input}"
```

## 🎯 Best Practices

### 1. Memory Backend Selection
- **Development**: Use `memory: true` (SQLite)
- **Staging**: Use `memory: production` (auto-detection)  
- **Production**: Use explicit configuration with BigQuery/Redis
- **High-Scale**: BigQuery for analytics, Redis for performance
- **Privacy-Sensitive**: SQLite with no persistence

### 2. Session Configuration
- **Start with `sharing_strategy: "sequential"`** for cost control
- **Use `scope: "workflow"`** unless you need cross-workflow memory
- **Always enable `enable_analytics: true`** in production
- **Set appropriate `session_timeout`** based on use case
- **Use `context_window_management: "smart_truncate"`** for safety

### 3. Cost Management
- **Monitor token usage** with BigQuery analytics queries
- **Choose smaller models** (gpt-4o-mini) where appropriate
- **Use sequential sharing** for 50-60% cost reduction
- **Set reasonable session timeouts** to prevent runaway costs
- **Implement auto-cleanup** for expired sessions

### 4. Performance Optimization
- **Use Redis** for high-performance memory access
- **Enable search** only when needed (adds overhead)
- **Choose appropriate BigQuery location** for your users
- **Use batch processing** for high-volume workflows
- **Monitor session analytics** for performance bottlenecks

### 5. Security and Privacy
- **Use workflow scope** for maximum isolation
- **Disable persistence** for sensitive data
- **Implement auto-cleanup** for compliance
- **Use environment variables** for credentials
- **Regular audit** of stored conversations

### 6. Development Workflow
- **Start simple** with `memory: true`
- **Test with sequential** sharing before using "all"
- **Enable analytics** to understand usage patterns
- **Gradually increase** session timeouts based on needs
- **Monitor costs** closely when moving to production

### 7. Troubleshooting
- **Check environment variables** for auto-detection issues
- **Verify credentials** for BigQuery/GCS access
- **Monitor session timeouts** for unexpected disconnections
- **Use analytics** to identify token usage spikes
- **Test memory backends** with verification scripts

## 🔍 Common Issues and Solutions

### Issue: "Tool 'filesystem' has no MCP URL configuration"
**Solution**: The middleware was enhanced to automatically default MCP tools to local mode when no explicit URL is configured.

### Issue: BigQuery "Invalid resource name projects/None"
**Solution**: Set the `GOOGLE_CLOUD_PROJECT` environment variable:
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### Issue: Exponential token costs with session memory
**Solution**: Use `sharing_strategy: "sequential"` and `context_window_management: "smart_truncate"`

### Issue: Context loss in long sessions
**Solution**: Use `context_window_management: "summarize"` to preserve information density

### Issue: Memory not persisting between sessions
**Solution**: Ensure `persist_session: true` and proper backend configuration

## 📊 Analytics and Monitoring

### BigQuery Analytics Queries

#### Session Performance
```sql
SELECT 
  DATE(timestamp) as date,
  COUNT(DISTINCT session_id) as unique_sessions,
  COUNT(*) as total_messages,
  AVG(JSON_EXTRACT_SCALAR(metadata, '$.token_count')) as avg_tokens,
  SUM(JSON_EXTRACT_SCALAR(metadata, '$.token_count')) as total_tokens
FROM `project.dataset.conversations`
GROUP BY date
ORDER BY date DESC;
```

#### Agent Collaboration Patterns
```sql
SELECT 
  session_id,
  ARRAY_AGG(agent_id ORDER BY timestamp) as agent_sequence,
  COUNT(DISTINCT agent_id) as unique_agents,
  COUNT(*) as total_exchanges
FROM `project.dataset.conversations`
GROUP BY session_id
HAVING COUNT(DISTINCT agent_id) > 1
ORDER BY total_exchanges DESC;
```

#### Cost Analysis
```sql
SELECT 
  agent_id,
  COUNT(*) as message_count,
  SUM(JSON_EXTRACT_SCALAR(metadata, '$.token_count')) as total_tokens,
  AVG(JSON_EXTRACT_SCALAR(metadata, '$.token_count')) as avg_tokens,
  -- Estimate cost (adjust rate for your model)
  SUM(JSON_EXTRACT_SCALAR(metadata, '$.token_count')) * 0.00001 as estimated_cost_usd
FROM `project.dataset.conversations`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY agent_id
ORDER BY total_tokens DESC;
```

## 🚀 Future Enhancements

The LangSwarm memory system is continuously evolving. Potential future enhancements include:

- **Vector Memory Backends**: Native support for Pinecone, Weaviate
- **Federated Memory**: Cross-organization memory sharing
- **Advanced Context Strategies**: Semantic context selection
- **Real-time Analytics**: Live memory usage dashboards
- **Memory Compression**: Advanced summarization techniques
- **Cross-Modal Memory**: Support for images, audio, documents

---

*This guide represents the complete state of LangSwarm memory features as of the current version. For the latest updates, refer to the official documentation and changelog.*