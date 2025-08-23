# MemoryPro API Documentation

## Overview

MemoryPro provides advanced memory management features for LangSwarm agents with two operation modes:

1. **Internal Mode**: Uses LangSwarmPro's built-in memory management with advanced features
2. **External Mode**: Integrates with external MemoryPro service for enterprise-grade capabilities

**Configuration**: Set `MEMORYPRO_ENABLED=true` and provide MemoryPro API credentials to enable external mode  
**Authentication**: API Key required (`Authorization: Bearer lsp_your_api_key`)  
**Subscription**: Pro subscription required for all endpoints

---

## Operation Modes

### Internal Mode (Default)
- Uses LangSwarmPro's built-in memory service
- Provides priority management, fading, and analytics
- Suitable for development and small-scale deployments

### External Mode (Enterprise)
- Integrates with external MemoryPro service
- Provides AI-powered insights, evolution tracking, and real-time webhooks
- Requires MemoryPro API credentials and subscription
- Includes automatic action discovery and lifecycle management

**Environment Variables for External Mode:**
```bash
MEMORYPRO_ENABLED=true
MEMORYPRO_API_URL=https://api.memorypro.com
MEMORYPRO_API_KEY=your_api_key
MEMORYPRO_API_SECRET=your_api_secret
MEMORYPRO_WEBHOOK_URL=https://your-app.com/memorypro/webhook
MEMORYPRO_WEBHOOK_SECRET=your_webhook_secret
```

---

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

**Response (Internal Mode):**
```json
{
  "memory": {
    "id": "mem_123",
    "user_id": "user_456",
    "content": "Important information about project requirements",
    "priority": "HIGH",
    "priority_score": 0.87,
    "importance_score": 0.92,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Response (External Mode):**
```json
{
  "status": "success",
  "memory_id": "mem_789xyz",
  "analysis": {
    "priority_score": 0.75,
    "relevance_score": 0.85,
    "themes": ["project management", "deadlines"],
    "extracted_actions": [
      {
        "type": "task",
        "title": "Review project timeline",
        "priority": "high"
      }
    ]
  }
}
```

### 2. Memory Recall with AI Analysis

Enhanced memory retrieval with semantic search and AI-powered insights.

**Endpoint:** `POST /memory/search`

**Request Body (Internal Mode):**
```json
{
  "query": "project requirements",
  "limit": 5,
  "threshold": 0.8,
  "priority_boost": true
}
```

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

**Response (External Mode):**
```json
{
  "status": "success",
  "memories": [
    {
      "memory_id": "mem_789xyz",
      "content": "We discussed that the project deadline is Friday...",
      "relevance_score": 0.95,
      "priority_score": 0.80,
      "themes": ["deadlines", "project management"]
    }
  ],
  "analysis": {
    "total_memories_searched": 1247,
    "patterns_discovered": ["frequent deadline discussions"],
    "evolution_insights": "User shows pattern of deadline anxiety"
  },
  "discovered_actions": [
    {
      "type": "reminder",
      "title": "Set up project timeline review",
      "priority": "high"
    }
  ]
}
```

### 3. Memory Insights and Analytics

Get comprehensive memory insights, patterns, and recommendations.

**Endpoint:** `GET /memory/insights`

**Response (Internal Mode):**
```json
{
  "status": "success",
  "user_id": "user_456",
  "insights": {
    "memory_health_score": 0.85,
    "total_memories": 156,
    "high_priority_count": 23,
    "patterns": [
      {
        "pattern_type": "recurring_topics",
        "description": "Based on memory analysis",
        "frequency": 5,
        "trend": "stable"
      }
    ]
  }
}
```

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
    ],
    "evolution_updates": [
      {
        "insight": "User prefers morning deadlines",
        "confidence": 0.92,
        "recommendation": "Schedule reminders for 9 AM"
      }
    ]
  }
}
```

### 4. Pattern Analysis

Get detailed pattern analysis and evolution insights.

**Endpoint:** `GET /memory/patterns`

**Response:**
```json
{
  "status": "success",
  "user_id": "user_456",
  "analysis": {
    "patterns": [
      {
        "pattern_type": "recurring_topics",
        "description": "User frequently discusses: project, deadline, meeting",
        "frequency": 8,
        "trend": "stable"
      },
      {
        "pattern_type": "time_preference",
        "description": "Most active during hours: 9, 14, 16",
        "frequency": 45,
        "trend": "consistent"
      }
    ],
    "evolution_insights": [
      {
        "insight": "User tends to create high-priority memories frequently",
        "confidence": 0.85,
        "recommendation": "Consider priority-based filtering"
      }
    ],
    "user_preferences": {
      "preferred_time": "morning",
      "content_style": "detailed",
      "default_priority": "medium"
    },
    "recommendations": [
      {
        "type": "automation",
        "title": "Create topic-based auto-tags",
        "priority": "medium"
      }
    ]
  }
}
```

### 5. Trigger Analysis

Force refresh of insights and pattern analysis.

**Endpoint:** `POST /memory/insights/trigger`

**Response:**
```json
{
  "status": "success",
  "message": "Memory analysis and insights generation triggered",
  "triggered_at": "2024-01-15T16:00:00Z",
  "insights_available": true
}
```

---

## Webhook Integration (External Mode Only)

### Webhook Registration

**Endpoint:** `POST /memorypro/webhook/register`

**Request Body:**
```json
{
  "user_id": "user_456",
  "webhook_url": "https://your-app.com/webhook"
}
```

### Webhook Events

MemoryPro sends real-time notifications for:

1. **Memory Insights** (`memory_insights`)
2. **Lifecycle Recommendations** (`lifecycle_recommendations`) 
3. **Evolution Updates** (`evolution_updates`)
4. **Action Discoveries** (`action_discoveries`)

**Webhook Payload Example:**
```json
{
  "event_type": "memory_insights",
  "user_id": "user_456",
  "timestamp": "2025-01-08T10:30:00Z",
  "data": {
    "insights": {
      "memory_health_score": 0.85,
      "new_patterns": [...],
      "lifecycle_recommendations": [...],
      "evolution_updates": [...]
    }
  }
}
```

### Webhook Verification

Webhooks include signature verification via `X-MemoryPro-Signature` header using HMAC-SHA256.

---

## Action Queue Integration

External mode automatically discovers and queues actions from memory analysis:

- **Memory Lifecycle**: Archive, prioritize, delete recommendations
- **Evolution Insights**: User preference updates  
- **Action Discovery**: Tasks, reminders, follow-ups extracted from memory content

Actions are queued via Google Cloud Pub/Sub and can be consumed via:
- Pull-based polling (`/action-queue/poll`)
- Push-based webhooks

---

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

### Update Fading Settings

**Endpoint:** `PUT /memory/fading/config`

---

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "message": "Memory content exceeds maximum length",
    "code": "INVALID_MEMORY_CONTENT",
    "details": {
      "content_length": 75000,
      "max_allowed": 50000
    }
  },
  "timestamp": "2025-01-08T10:30:00Z"
}
```

### Common Error Codes

- `AUTHENTICATION_ERROR`: Invalid API credentials
- `VALIDATION_ERROR`: Invalid request data
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded
- `MEMORYPRO_UNAVAILABLE`: External MemoryPro service unavailable
- `WEBHOOK_VERIFICATION_FAILED`: Invalid webhook signature

---

## Rate Limits

- **Internal Mode**: 100 requests per hour per user
- **External Mode**: Based on MemoryPro subscription tier
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

---

## Best Practices

### Memory Management
- Use descriptive content for better AI analysis
- Set appropriate priorities for effective filtering
- Include relevant metadata for enhanced insights

### External Mode
- Configure webhooks for real-time updates
- Monitor action queue for discovered tasks
- Review lifecycle recommendations regularly

### Performance
- Use semantic search for better relevance
- Enable priority boosting for important queries
- Set appropriate recall limits to control response size

---

## Migration Guide

### From Internal to External Mode

1. **Obtain MemoryPro credentials**
2. **Configure environment variables**
3. **Test webhook integration**
4. **Update application code** to handle enhanced response formats
5. **Monitor action queue** for discovered actions

### Backward Compatibility

The memory adapter automatically detects the mode and maintains backward compatibility with existing LangSwarm integrations. 