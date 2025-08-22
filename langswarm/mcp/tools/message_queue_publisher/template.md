# Message Queue Publisher MCP Tool Template

## Description

Message queue publisher tool for asynchronous communication between agents and external systems. Supports Redis, Google Cloud Pub/Sub, and in-memory message brokers for event dispatching, task queuing, and system integration. Auto-detects available message brokers and provides fallback mechanisms for reliable message delivery.

## Instructions

**Tool Type**: Direct method calls AND intent-based calls
**Tool ID**: message_queue_publisher

### Available Methods:

#### 1. `publish_message`
**Purpose**: Publish a message to a specific channel/queue
**Parameters**:
- `channel` (str, required): Target channel or queue name
- `message` (dict, required): Message payload to publish
- `metadata` (dict, optional): Additional metadata for routing/filtering

**Example Direct Call**:
```json
{
  "method": "publish_message",
  "params": {
    "channel": "task_notifications",
    "message": {
      "type": "task_completion",
      "task_id": "task-123",
      "status": "completed",
      "result": "Successfully processed user data"
    },
    "metadata": {
      "priority": "high",
      "source": "data_processor_agent"
    }
  }
}
```

#### 2. `list_channels`
**Purpose**: List available channels/queues (for in-memory broker)
**Parameters**: None

**Example Direct Call**:
```json
{
  "method": "list_channels",
  "params": {}
}
```

#### 3. `get_broker_stats`
**Purpose**: Get statistics and status of the message broker
**Parameters**: None

**Example Direct Call**:
```json
{
  "method": "get_broker_stats", 
  "params": {}
}
```

### Intent-Based Usage Examples:

**Task Notification**:
- "Send a task completion notification to the workers queue"
- "Notify the monitoring system that data processing is done"
- "Queue a task for the analysis agent with high priority"

**System Alerts**:
- "Publish an error alert: Database connection failed"
- "Send a warning to the admin channel about high CPU usage"
- "Alert the security team about failed login attempts"

**Agent Communication**:
- "Forward these results to the analysis-agent channel"
- "Send workflow output to the reporting queue"
- "Communicate with downstream agents about status change"

**Information Queries**:
- "Show me available message channels"
- "What's the status of the message broker?"
- "List all active queues"

### Message Types and Structures:

#### Task Messages:
```json
{
  "type": "task",
  "action": "process|complete|failed|queued",
  "task_id": "unique_task_identifier", 
  "data": {...},
  "priority": 1-5,
  "timestamp": "ISO_timestamp"
}
```

#### Event Messages:
```json
{
  "type": "event",
  "event_name": "user_action|system_event|workflow_trigger",
  "payload": {...},
  "source": "originating_agent",
  "timestamp": "ISO_timestamp"
}
```

#### Alert Messages:
```json
{
  "type": "alert",
  "level": "info|warning|error|critical",
  "message": "human_readable_message",
  "details": {...},
  "component": "system_component",
  "timestamp": "ISO_timestamp"
}
```

#### Agent Communication:
```json
{
  "type": "agent_message",
  "from": "source_agent_id",
  "to": "target_agent_id|channel",
  "content": {...},
  "message_id": "unique_identifier",
  "timestamp": "ISO_timestamp"
}
```

### Broker Auto-Detection:

The tool automatically detects and uses the best available message broker:

1. **Redis**: If `REDIS_URL` environment variable is set
2. **GCP Pub/Sub**: If `GOOGLE_CLOUD_PROJECT` environment variable is set
3. **In-Memory**: Fallback for development and testing

### Channel Naming Conventions:

- Use lowercase with underscores: `task_notifications`
- Include purpose: `system_alerts`, `user_events`, `agent_communications`
- Environment prefix: `prod_alerts`, `dev_tasks`, `staging_events`
- Agent-specific: `data_processor_queue`, `analysis_agent_input`

### Metadata Usage:

**Routing Metadata**:
- `priority`: Message priority (1=highest, 5=lowest)
- `source`: Originating agent or system
- `target`: Intended recipient or processor
- `routing_key`: Custom routing identifier

**Processing Metadata**:
- `retry_count`: Number of retry attempts
- `timeout`: Processing timeout in seconds
- `batch_id`: Batch operation identifier
- `correlation_id`: Request correlation tracking

### Error Handling:

The tool provides comprehensive error handling for:
- **Connection Errors**: Broker unavailable, network issues
- **Authentication Errors**: Invalid credentials, permissions
- **Validation Errors**: Invalid channel names, malformed messages
- **Capacity Errors**: Queue full, rate limits exceeded

### Performance Considerations:

- **Redis**: Best for high-frequency operations and real-time communication
- **GCP Pub/Sub**: Ideal for enterprise-scale and cross-system integration
- **In-Memory**: Perfect for development, testing, and simple workflows

### Security and Access:

- Messages are automatically enriched with timestamps and broker metadata
- Channel names are validated for security (alphanumeric, underscore, hyphen only)
- Supports broker-specific authentication mechanisms
- No sensitive data is logged in error messages

### Integration Patterns:

**Event-Driven Architecture**:
```
Agent A → publish_message → Queue → Agent B (subscriber)
```

**Task Distribution**:
```
Controller → publish_message → Work Queue → Worker Agents
```

**System Monitoring**:
```
All Agents → publish_message → Alert Channel → Monitoring System
```

### Limitations:

- **Channel Management**: Limited channel management capabilities (mainly for in-memory broker)
- **Message Persistence**: Persistence depends on broker type and configuration
- **Subscriber Management**: Tool focuses on publishing; subscription management is broker-specific
- **Message Ordering**: Message ordering guarantees depend on broker implementation
- **Size Limits**: Message size limits vary by broker type