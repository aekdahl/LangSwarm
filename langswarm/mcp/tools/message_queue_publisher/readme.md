# Message Queue Publisher MCP Tool

A comprehensive message queue publisher built on the MCP (Model-Compatible Protocol) framework with local mode support for LangSwarm workflows. Enables asynchronous communication between agents and external systems through multiple message broker backends.

## Features

- ✅ **Multi-Broker Support**: Redis, Google Cloud Pub/Sub, and in-memory queues
- 📱 **Local Mode Support**: Zero-latency local execution  
- 🔍 **Auto-Detection**: Automatically detects and uses available message brokers
- 📨 **Message Enrichment**: Automatic timestamps, metadata, and broker information
- 🤖 **Intent-Based Interface**: Natural language message publishing
- 🔧 **Direct API Calls**: Structured method invocation
- 🛡️ **Error Handling**: Comprehensive validation and error recovery
- 🔄 **Fallback Mechanisms**: Graceful degradation to in-memory broker
- 📊 **Monitoring**: Broker statistics and channel management

## Quick Start

### Using with LangSwarm

**Basic Configuration (Auto-Detection)**:
```yaml
tools:
  - id: message_queue
    type: mcpmessage_queue_publisher
    description: "Message queue publisher with auto-detected broker"
    local_mode: true
    pattern: "intent"
    main_workflow: "use_message_queue_tool"
    permission: anonymous
```

**With Specific Broker Configuration**:
```yaml
# Environment variables for broker detection
# Redis: REDIS_URL=redis://localhost:6379
# GCP: GOOGLE_CLOUD_PROJECT=your-project-id

tools:
  - id: message_queue
    type: mcpmessage_queue_publisher
    description: "Enterprise message queue with Redis/GCP Pub/Sub"
    local_mode: true
    pattern: "intent"
    main_workflow: "use_message_queue_tool"
    permission: anonymous
```

### Example Usage

**Natural Language (Intent-Based)**:
```
"Send a task completion notification to the workers queue"
"Publish an error alert: Database connection failed"
"Forward these results to the analysis-agent channel"
"Show me available message channels"
```

**Direct API Calls**:
```python
# Publish a task notification
tool.run({
    "method": "publish_message",
    "params": {
        "channel": "task_notifications",
        "message": {
            "type": "task_completion",
            "task_id": "task-123",
            "status": "completed",
            "result": "Data processing finished"
        },
        "metadata": {
            "priority": "high",
            "source": "data_processor"
        }
    }
})

# List available channels
tool.run({
    "method": "list_channels",
    "params": {}
})

# Get broker statistics
tool.run({
    "method": "get_broker_stats", 
    "params": {}
})
```

## Message Broker Support

### Auto-Detection Logic

The tool automatically selects the best available broker:

1. **Redis** (if `REDIS_URL` environment variable is set)
2. **GCP Pub/Sub** (if `GOOGLE_CLOUD_PROJECT` environment variable is set)  
3. **In-Memory** (fallback for development and testing)

### Broker Configuration

#### **Redis Setup**
```bash
# Set Redis connection
export REDIS_URL="redis://localhost:6379"

# Or with authentication
export REDIS_URL="redis://:password@localhost:6379/0"
```

#### **GCP Pub/Sub Setup**
```bash
# Set project and credentials
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

#### **In-Memory (Development)**
```bash
# No configuration needed - automatic fallback
# Perfect for development and testing
```

## API Reference

### Methods

#### `publish_message`
Publish a message to a specific channel/queue.

**Parameters**:
- `channel` (str, required): Target channel or queue name
- `message` (dict, required): Message payload to publish  
- `metadata` (dict, optional): Additional metadata for routing/filtering

**Response**:
```json
{
  "success": true,
  "channel": "task_notifications",
  "message_id": "msg_1234567890.123",
  "timestamp": "2025-08-12T08:46:03.546581Z",
  "broker_type": "RedisBroker"
}
```

#### `list_channels`
List available channels/queues (for in-memory broker).

**Parameters**: None

**Response**:
```json
{
  "channels": ["tasks", "alerts", "notifications"],
  "broker_type": "InMemoryBroker", 
  "total_count": 3
}
```

#### `get_broker_stats`
Get statistics and status of the message broker.

**Parameters**: None

**Response**:
```json
{
  "broker_type": "RedisBroker",
  "available": true,
  "stats": {
    "type": "RedisBroker",
    "available": true
  }
}
```

## Message Types and Patterns

### Standard Message Structures

#### **Task Messages**
```json
{
  "type": "task",
  "action": "process|complete|failed|queued",
  "task_id": "task-123",
  "data": {...},
  "priority": 1,
  "timestamp": "2025-08-12T08:46:03.546581Z"
}
```

#### **Event Messages**
```json
{
  "type": "event", 
  "event_name": "user_registration",
  "payload": {
    "user_id": "user-456",
    "email": "user@example.com"
  },
  "source": "auth_service",
  "timestamp": "2025-08-12T08:46:03.546581Z"
}
```

#### **Alert Messages**
```json
{
  "type": "alert",
  "level": "error",
  "message": "Database connection failed",
  "details": {
    "error_code": "CONN_TIMEOUT",
    "retry_count": 3
  },
  "component": "database_service",
  "timestamp": "2025-08-12T08:46:03.546581Z"
}
```

### Channel Naming Conventions

- **Task Channels**: `task_notifications`, `work_queue`, `processing_tasks`
- **Event Channels**: `user_events`, `system_events`, `workflow_triggers`  
- **Alert Channels**: `system_alerts`, `error_notifications`, `monitoring_alerts`
- **Agent Channels**: `agent_communications`, `data_processor_queue`, `analysis_input`

## Integration Patterns

### Event-Driven Architecture
```yaml
workflows:
  event_driven_flow:
    - steps:
      - agent: data_processor
        input: "${user_data}"
        output:
          to: message_queue
      
      - tool: message_queue
        input: |
          {
            "method": "publish_message",
            "params": {
              "channel": "processing_complete",
              "message": {
                "type": "event",
                "event_name": "data_processed",
                "payload": "${previous_output}"
              }
            }
          }
```

### Task Distribution
```yaml
workflows:
  task_distribution:
    - steps:
      - tool: message_queue
        input: |
          {
            "method": "publish_message", 
            "params": {
              "channel": "worker_tasks",
              "message": {
                "type": "task",
                "action": "process",
                "data": "${task_data}",
                "priority": 1
              }
            }
          }
```

### System Monitoring
```yaml
workflows:
  error_monitoring:
    - steps:
      - tool: message_queue
        input: |
          {
            "method": "publish_message",
            "params": {
              "channel": "system_alerts",
              "message": {
                "type": "alert", 
                "level": "error",
                "message": "${error_message}",
                "component": "${component_name}"
              }
            }
          }
```

## Environment Setup

### Development Environment
```bash
# No additional setup needed
# Tool automatically uses in-memory broker
```

### Redis Environment
```bash
# Install Redis
brew install redis  # macOS
# OR
sudo apt-get install redis-server  # Ubuntu

# Start Redis
redis-server

# Set environment
export REDIS_URL="redis://localhost:6379"
```

### GCP Pub/Sub Environment
```bash
# Install Google Cloud SDK
# Create service account with Pub/Sub permissions
# Download service account key

export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Install Python dependencies
pip install google-cloud-pubsub
```

## Advanced Usage

### Custom Message Routing
```python
# Publish with routing metadata
tool.run({
    "method": "publish_message",
    "params": {
        "channel": "smart_routing",
        "message": {...},
        "metadata": {
            "priority": "high",
            "routing_key": "urgent_tasks",
            "target_agents": ["processor_1", "processor_2"],
            "retry_policy": "exponential_backoff"
        }
    }
})
```

### Batch Message Publishing
```python
# Use batch workflow for multiple messages
workflow_input = {
    "messages": [
        {"channel": "tasks", "message": {...}},
        {"channel": "alerts", "message": {...}}, 
        {"channel": "events", "message": {...}}
    ]
}
```

### Error Handling and Monitoring
```python
# Check broker status before publishing
stats = tool.run({
    "method": "get_broker_stats",
    "params": {}
})

if stats["available"]:
    # Proceed with message publishing
    pass
else:
    # Handle broker unavailability
    pass
```

## Performance Considerations

### Broker Performance Comparison

| Broker | Throughput | Latency | Persistence | Best For |
|--------|------------|---------|-------------|----------|
| **Redis** | Very High | Very Low | Optional | Real-time, high-frequency |
| **GCP Pub/Sub** | High | Low | Guaranteed | Enterprise, cross-system |
| **In-Memory** | Extremely High | Minimal | None | Development, testing |

### Optimization Tips

1. **Channel Design**: Use specific channels rather than broadcasting
2. **Message Size**: Keep messages reasonably sized for better performance
3. **Metadata**: Use metadata for routing instead of large message payloads
4. **Batch Operations**: Use batch workflows for multiple related messages
5. **Error Handling**: Implement proper error handling and retry logic

## Troubleshooting

### Common Issues

**Messages not being published?**
```bash
# Check broker status
python3 -c "
from langswarm.mcp.tools.message_queue_publisher.main import MessageQueuePublisherMCPTool
tool = MessageQueuePublisherMCPTool('test')
print(tool.run({'method': 'get_broker_stats', 'params': {}}))
"
```

**Redis connection issues?**
```bash
# Verify Redis is running
redis-cli ping

# Check connection string
echo $REDIS_URL
```

**GCP Pub/Sub authentication issues?**
```bash
# Verify credentials
gcloud auth application-default print-access-token

# Check project
echo $GOOGLE_CLOUD_PROJECT
```

### Performance Issues

**High latency?**
- Switch to Redis for lower latency
- Use direct workflows instead of complex processing
- Optimize message size and structure

**Message loss?**
- Ensure broker persistence is configured
- Implement message acknowledgment patterns
- Add retry logic for critical messages

## Migration from Synapse Tool

This MCP tool is a direct replacement for the legacy `langswarm.synapse.tools.message_queue_publisher` with enhanced features:

- ✅ **Local mode support** (new)
- ✅ **MCP protocol compliance** (new)
- ✅ **Auto-broker detection** (new)
- ✅ **Message enrichment** (new)
- ✅ **Enhanced error handling** (improved)
- ✅ **Multiple broker support** (enhanced)
- ✅ **Intent-based interface** (enhanced)
- ✅ **Message publishing** (same core functionality)

### Migration Steps
1. Replace tool configuration in `tools.yaml`:
   ```yaml
   # Old synapse tool
   - id: message_queue
     type: message_queue_publisher
   
   # New MCP tool
   - id: message_queue
     type: mcpmessage_queue_publisher
     local_mode: true
   ```
2. Update workflow references from synapse to MCP
3. Test functionality with existing message patterns
4. Verify broker auto-detection works with your environment
5. Remove legacy tool dependencies

## License

Part of the LangSwarm framework. See main project license.