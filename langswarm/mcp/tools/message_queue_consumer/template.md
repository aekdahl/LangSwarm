# Message Queue Consumer MCP Tool

A comprehensive MCP tool that enables LangSwarm to act as a worker by polling message queues and processing tasks. Supports Redis, GCP Pub/Sub, and in-memory message brokers with intelligent task processing and monitoring capabilities.

## Methods

### start_consumer
Start a message queue consumer to poll and process tasks from a queue.

**Parameters:**
- `consumer_id` (string, required): Unique identifier for the consumer
- `broker_type` (string, required): Type of message broker - "redis", "gcp_pubsub", or "in_memory"
- `broker_config` (object, required): Broker-specific configuration settings
- `queue_name` (string, required): Name of the queue/topic to consume from
- `max_workers` (integer, optional): Maximum concurrent workers (default: 5)
- `poll_interval` (integer, optional): Polling interval in seconds (default: 1)
- `retry_attempts` (integer, optional): Number of retry attempts for failed tasks (default: 3)
- `task_timeout` (integer, optional): Task execution timeout in seconds (default: 300)

**Returns:**
- `consumer_id` (string): Consumer identifier
- `status` (string): Consumer status
- `message` (string): Status message
- `broker_info` (object): Broker connection information

### stop_consumer
Stop a running message queue consumer.

**Parameters:**
- `consumer_id` (string, required): Consumer identifier to stop
- `graceful` (boolean, optional): Wait for current tasks to complete (default: true)

**Returns:**
- `consumer_id` (string): Consumer identifier
- `status` (string): Final consumer status
- `tasks_completed` (integer): Number of tasks completed during shutdown
- `message` (string): Status message

### list_consumers
List all active message queue consumers.

**Parameters:**
- `include_stats` (boolean, optional): Include consumer statistics (default: true)

**Returns:**
- `consumers` (array): List of active consumers with details
- `total_consumers` (integer): Total number of consumers
- `total_tasks_processed` (integer): Total tasks processed across all consumers

### get_consumer_stats
Get detailed statistics for a specific consumer.

**Parameters:**
- `consumer_id` (string, required): Consumer identifier

**Returns:**
- `consumer_id` (string): Consumer identifier
- `status` (string): Current consumer status
- `tasks_processed` (integer): Total tasks processed
- `tasks_failed` (integer): Total tasks failed
- `average_processing_time` (float): Average task processing time in seconds
- `uptime` (float): Consumer uptime in seconds
- `current_workers` (integer): Current number of active workers
- `queue_info` (object): Queue/topic information

### pause_consumer
Temporarily pause a running consumer.

**Parameters:**
- `consumer_id` (string, required): Consumer identifier to pause

**Returns:**
- `consumer_id` (string): Consumer identifier
- `status` (string): Consumer status after pause
- `message` (string): Status message

### resume_consumer
Resume a paused consumer.

**Parameters:**
- `consumer_id` (string, required): Consumer identifier to resume

**Returns:**
- `consumer_id` (string): Consumer identifier
- `status` (string): Consumer status after resume
- `message` (string): Status message

## Intent-Based Examples

### Start Redis Consumer
```json
{
  "response": "I'll start a Redis consumer to process tasks from the task queue",
  "mcp": {
    "tool": "message_queue_consumer",
    "method": "start_consumer",
    "params": {
      "consumer_id": "redis_worker_1",
      "broker_type": "redis",
      "broker_config": {
        "redis_url": "redis://localhost:6379"
      },
      "queue_name": "task_queue",
      "max_workers": 5,
      "poll_interval": 1
    }
  }
}
```

### Start GCP Pub/Sub Consumer
```json
{
  "response": "I'll start a GCP Pub/Sub consumer for processing enterprise tasks",
  "mcp": {
    "tool": "message_queue_consumer",
    "method": "start_consumer",
    "params": {
      "consumer_id": "pubsub_worker_1",
      "broker_type": "gcp_pubsub",
      "broker_config": {
        "project_id": "my-gcp-project"
      },
      "queue_name": "enterprise-task-subscription",
      "max_workers": 10,
      "task_timeout": 600
    }
  }
}
```

### Monitor Consumer Performance
```json
{
  "response": "I'll check the performance statistics for the specified consumer",
  "mcp": {
    "tool": "message_queue_consumer",
    "method": "get_consumer_stats",
    "params": {
      "consumer_id": "redis_worker_1"
    }
  }
}
```

### List All Active Consumers
```json
{
  "response": "I'll show you all currently active message queue consumers",
  "mcp": {
    "tool": "message_queue_consumer",
    "method": "list_consumers",
    "params": {
      "include_stats": true
    }
  }
}
```

### Pause Consumer for Maintenance
```json
{
  "response": "I'll pause the consumer to allow for maintenance without losing tasks",
  "mcp": {
    "tool": "message_queue_consumer",
    "method": "pause_consumer",
    "params": {
      "consumer_id": "redis_worker_1"
    }
  }
}
```

## Broker Configuration

### Redis Configuration
```json
{
  "broker_type": "redis",
  "broker_config": {
    "redis_url": "redis://username:password@hostname:port/database"
  }
}
```

### GCP Pub/Sub Configuration
```json
{
  "broker_type": "gcp_pubsub",
  "broker_config": {
    "project_id": "your-gcp-project-id"
  }
}
```

### In-Memory Configuration (Development)
```json
{
  "broker_type": "in_memory",
  "broker_config": {}
}
```

## Supported Task Types

### Workflow Execution Tasks
```json
{
  "type": "workflow_execution",
  "workflow": "data_analysis",
  "data": {
    "input_file": "/data/dataset.csv",
    "output_format": "json"
  }
}
```

### Data Processing Tasks
```json
{
  "type": "data_processing",
  "data": [1, 2, 3, 4, 5],
  "operation": "sum"
}
```

### File Processing Tasks
```json
{
  "type": "file_processing",
  "file_path": "/documents/report.pdf",
  "operation": "analyze"
}
```

### API Call Tasks
```json
{
  "type": "api_call",
  "url": "https://api.example.com/data",
  "method": "GET"
}
```

## Consumer States

### Running States
- **stopped**: Consumer is not active
- **starting**: Consumer is initializing
- **running**: Consumer is actively polling and processing tasks
- **paused**: Consumer is temporarily halted but can be resumed
- **error**: Consumer encountered an error and needs attention

### Task States
- **received**: Task has been consumed from queue
- **processing**: Task is currently being processed
- **completed**: Task completed successfully
- **failed**: Task failed and may be retried
- **retrying**: Task is being retried after failure

## Performance Optimization

### Worker Configuration
- **Low-latency tasks**: max_workers=2-5, poll_interval=1
- **CPU-intensive tasks**: max_workers=1-3, task_timeout=600+
- **High-throughput tasks**: max_workers=10-20, poll_interval=1-2

### Broker Selection
- **Redis**: Fast, simple, good for general use cases
- **GCP Pub/Sub**: Enterprise-grade, guaranteed delivery, auto-scaling
- **In-Memory**: Development and testing only

### Monitoring Metrics
- **Success Rate**: tasks_processed / (tasks_processed + tasks_failed)
- **Throughput**: tasks_processed / uptime
- **Resource Utilization**: current_workers / max_workers
- **Average Processing Time**: Performance indicator

## Error Handling

### Automatic Retry Logic
- Failed tasks are automatically retried up to `retry_attempts`
- Exponential backoff between retry attempts
- Tasks that exceed retry limit are marked as permanently failed

### Timeout Handling
- Tasks that exceed `task_timeout` are automatically terminated
- Timed-out tasks are marked as failed and may be retried
- Adjust timeout based on expected task complexity

### Broker Connection Issues
- Automatic reconnection attempts for broker disconnections
- Graceful handling of temporary network issues
- Consumer status reflects connection health

## Security Considerations

### Redis Security
- Use authentication (username/password or AUTH command)
- Configure Redis in protected mode
- Use TLS encryption for network communications

### GCP Pub/Sub Security
- Ensure proper IAM permissions for service account
- Use application default credentials or service account keys
- Configure subscription-level access controls

### Task Data Security
- Avoid sensitive data in task payloads
- Use encryption for sensitive task data
- Implement audit logging for task processing

## Limitations

### Broker-Specific Limitations
- **Redis**: No guaranteed delivery, limited to available memory
- **GCP Pub/Sub**: Requires GCP account and proper authentication
- **In-Memory**: Limited to single process, data lost on restart

### Processing Limitations
- Task processing is limited by available system resources
- Large tasks may impact overall consumer performance
- Concurrent workers share the same process memory

### Scalability Considerations
- Single consumer instance has finite processing capacity
- For high-scale deployments, use multiple consumer instances
- Consider message broker capacity and performance limits