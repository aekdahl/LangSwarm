# Message Queue Consumer Tool

The **Message Queue Consumer** tool transforms LangSwarm into a distributed task processing worker. It enables your agents to poll message queues (Redis, GCP Pub/Sub, or In-Memory), pull tasks, and execute them as LangSwarm workflows.

## 🚀 Overview

- **Role**: Distributed Worker Node
- **Supported Brokers**: Redis, Google Cloud Pub/Sub, In-Memory
- **Capabilities**:
    - Poll queues for tasks
    - Execute workflows based on task content
    - Robust retry logic with exponential backoff
    - Real-time monitoring and statistics

## ⚙️ Configuration

The consumer is configured via the `message_queue_consumer` tool. You can define specialized agents to manage these consumers.

### 1. Redis Consumer (Production Standard)

Best for general-purpose high-throughput task queues.

```json
{
  "method": "start_consumer",
  "params": {
    "consumer_id": "redis_worker_01",
    "broker_type": "redis",
    "broker_config": {
      "redis_url": "redis://localhost:6379"  # Or your Redis URL
    },
    "queue_name": "tasks",
    "max_workers": 5,
    "poll_interval": 1
  }
}
```

### 2. GCP Pub/Sub Consumer (Enterprise)

Best for reliable, at-least-once delivery and auto-scaling cloud architectures.

```json
{
  "method": "start_consumer",
  "params": {
    "consumer_id": "pubsub_worker_01",
    "broker_type": "gcp_pubsub",
    "broker_config": {
      "project_id": "my-gcp-project"
    },
    "queue_name": "task-subscription-id",
    "max_workers": 10
  }
}
```

### 3. In-Memory Consumer (Development)

Best for local testing and debugging without external dependencies.

```json
{
  "method": "start_consumer",
  "params": {
    "consumer_id": "dev_worker",
    "broker_type": "in_memory",
    "broker_config": {},
    "queue_name": "test_queue"
  }
}
```

---

## 🛠️ Usage Patterns

### Manager Agent

You can create a "Queue Manager" agent responsible for these operations.

```yaml
# agents.yaml
agents:
  - id: queue_manager
    agent_type: openai
    model: gpt-4o
    system_prompt: |
      You are responsible for managing the Message Queue Consumers.
      Use 'message_queue_consumer' to start, stop, pause, and monitor consumers.
    tools:
      - message_queue_consumer
```

### Task Structure

When you publish a message to the queue, it should ideally follow this structure so the consumer knows how to handle it:

**Workflow Task:**
```json
{
  "type": "workflow_execution",
  "workflow": "document_analysis",
  "data": {
    "file_path": "/docs/contract.pdf",
    "priority": "high"
  }
}
```

**Generic Task:**
```json
{
  "type": "data_processing",
  "operation": "summarize",
  "data": "Text content to summarize..."
}
```

---

## 📊 Monitoring & Management

The tool provides real-time control over your consumers.

### Check Status
```json
{
  "method": "get_consumer_stats",
  "params": { "consumer_id": "redis_worker_01" }
}
```
*Returns: Tasks processed, failures, average processing time, and uptime.*

### Lifecycle Control
- **Pause**: `{"method": "pause_consumer", "params": {"consumer_id": "..."}}`
- **Resume**: `{"method": "resume_consumer", "params": {"consumer_id": "..."}}`
- **Stop**: `{"method": "stop_consumer", "params": {"consumer_id": "...", "graceful": true}}` (Waits for current tasks to finish)

## 🏗️ Architecture Notes

- **Async Core**: Built on Python's `asyncio` for non-blocking I/O.
- **Worker Pool**: Maintains a set of concurrent workers (configurable via `max_workers`) to process multiple tasks in parallel.
- **Error Handling**: Failed tasks are automatically retried (if configured) or moved to a dead-letter state depending on the broker's logic.
