---
title: "MemoryPro API"
description: "Advanced memory management system."
---

# MemoryPro API

MemoryPro provides advanced memory management features for LangSwarm agents with two operation modes:

1. **Internal Mode**: Uses LangSwarmPro's built-in memory management with advanced features.
2. **External Mode**: Integrates with external MemoryPro service for enterprise-grade capabilities.

## Operation Modes

### Internal Mode (Default)
- Uses LangSwarmPro's built-in memory service.
- Provides priority management, fading, and analytics.
- Suitable for development and small-scale deployments.

### External Mode (Enterprise)
- Integrates with external MemoryPro service.
- Provides AI-powered insights, evolution tracking, and real-time webhooks.
- Requires MemoryPro API credentials and subscription.
- Includes automatic action discovery and lifecycle management.

## API Endpoints

### 1. Create Memory

Create a new memory with automatic priority calculation and enhanced analysis.

**Endpoint:** `POST /memory/`

**Request Body:**
```json
{
  "content": "Important information about project requirements",
  "agent_id": "agent_123",
  "session_id": "session_456", 
  "memory_type": "CONVERSATION",
  "priority": "HIGH",
  "tags": ["project", "requirements"],
  "metadata": {
    "source": "user_input",
    "confidence": 0.95
  }
}
```

### 2. Memory Recall with AI Analysis

Enhanced memory retrieval with semantic search and AI-powered insights.

**Endpoint:** `POST /memory/search`

**Request Body (External Mode):**
```json
{
  "query": "What did we discuss about project deadlines?",
  "user_id": "user_456",
  "session_id": "session_abc123",
  "recall_count": 5,
  "options": {
    "weight_recent": true,
    "weight_responsibilities": true,
    "auto_queue_actions": true,
    "include_analysis": true,
    "evolution_enabled": true
  }
}
```

### 3. Memory Insights and Analytics

Get comprehensive memory insights, patterns, and recommendations.

**Endpoint:** `GET /memory/insights`

**Response (External Mode):**
```json
{
  "status": "success",
  "user_id": "user_456",
  "insights": {
    "memory_health_score": 0.85,
    "total_memories": 1247,
    "patterns": [
      {
        "pattern_type": "recurring_topics",
        "description": "Frequent discussions about project deadlines",
        "frequency": 15,
        "trend": "increasing"
      }
    ],
    "lifecycle_recommendations": [
      {
        "action": "archive",
        "memory_ids": ["mem_old_1", "mem_old_2"],
        "reason": "Low relevance, older than 6 months"
      }
    ]
  }
}
```

## Configuration Management

### Fading Configuration

 **Endpoint:** `GET /memory/fading/config`

 ```json
 {
   "enabled": true,
   "base_fading_factor": 0.95,
   "priority_boost": {
     "HIGH": 1.0,
     "MEDIUM": 0.8,
     "LOW": 0.6
   },
   "minimum_retention_days": 7,
   "maximum_retention_days": 365
 }
 ```

## Framework Interoperability (Polyglot Memory)

MemoryPro's `HybridMemoryManager` can adapt itself to other popular AI frameworks, allowing you to use LangSwarm's advanced memory logic within LangChain or LlamaIndex workflows.

### LangChain Integration

Exports the manager as a LangChain `VectorStore`.

```python
from langswarm_pro.core.memory.hybrid import HybridMemoryManager

# Initialize your hybrid manager
manager = HybridMemoryManager(adapters=[...])

# Convert to LangChain VectorStore
vectorstore = manager.to_framework("langchain")

# Use in LangChain chains
from langchain.chains import RetrievalQA
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever())
```

### LlamaIndex Integration

Exports the manager as a LlamaIndex `QueryEngine`.

```python
# Convert to LlamaIndex QueryEngine
query_engine = manager.to_framework("llamaindex")

# Query directly
response = query_engine.query("What did we discuss about deployment?")
```
