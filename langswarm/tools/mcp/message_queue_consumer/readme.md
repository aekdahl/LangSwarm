# Message Queue Consumer MCP Tool

🔄 **Transform LangSwarm into a powerful distributed worker by consuming tasks from message queues. Support Redis, GCP Pub/Sub, and in-memory brokers with intelligent task processing, monitoring, and workflow integration.**

## 🎯 **What This Tool Does**

The Message Queue Consumer MCP Tool enables LangSwarm to:

### 🔄 **Act as a Distributed Worker**
- **Poll Message Queues**: Continuously monitor queues for new tasks
- **Process Tasks Intelligently**: Execute various task types using LangSwarm workflows
- **Handle Multiple Brokers**: Support Redis, GCP Pub/Sub, and in-memory queues
- **Scale Horizontally**: Run multiple consumers across different instances

### 📊 **Enterprise-Grade Processing**
- **Concurrent Workers**: Process multiple tasks simultaneously
- **Retry Logic**: Automatic retry with exponential backoff
- **Timeout Handling**: Graceful handling of long-running tasks
- **Performance Monitoring**: Real-time statistics and health monitoring

### 🔧 **Production-Ready Features**
- **Graceful Shutdown**: Complete current tasks before stopping
- **Pause/Resume**: Temporarily halt processing for maintenance
- **Error Recovery**: Robust error handling and recovery mechanisms
- **Resource Management**: Intelligent worker allocation and management

## 🌟 **Key Features**

### 🚀 **Multi-Broker Support**

#### **Redis Broker**
```python
# Fast, simple, excellent for general use cases
{
  "broker_type": "redis",
  "broker_config": {
    "redis_url": "redis://localhost:6379"
  }
}
```

#### **GCP Pub/Sub Broker**
```python
# Enterprise-grade with guaranteed delivery
{
  "broker_type": "gcp_pubsub", 
  "broker_config": {
    "project_id": "your-gcp-project"
  }
}
```

#### **In-Memory Broker**
```python
# Perfect for development and testing
{
  "broker_type": "in_memory",
  "broker_config": {}
}
```

### 🎯 **Intelligent Task Processing**

#### **Workflow Integration**
```json
{
  "type": "workflow_execution",
  "workflow": "data_analysis",
  "data": {
    "dataset": "/data/sales_2024.csv",
    "analysis_type": "trend_analysis"
  }
}
```

#### **Data Processing**
```json
{
  "type": "data_processing",
  "data": [1, 2, 3, 4, 5],
  "operation": "statistical_analysis"
}
```

#### **File Operations**
```json
{
  "type": "file_processing",
  "file_path": "/documents/report.pdf",
  "operation": "extract_text"
}
```

#### **API Integration**
```json
{
  "type": "api_call",
  "url": "https://api.external-service.com/process",
  "method": "POST",
  "data": {"key": "value"}
}
```

## 🏗️ **Architecture**

### 📋 **Consumer Lifecycle**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   STOPPED   │───▶│  STARTING   │───▶│   RUNNING   │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                                      │
       │                ┌─────────────┐      │
       └────────────────│   PAUSED    │◀─────┘
                        └─────────────┘
```

### 🔄 **Task Processing Flow**
```
Queue → Consume → Process → Complete → Acknowledge
  ▲                 │
  └─────── Retry ◀──┘ (on failure)
```

### 🏭 **Multi-Consumer Architecture**
```
┌─────────────────┐    ┌─────────────────┐
│ Message Queue   │    │ LangSwarm       │
│ (Redis/Pub/Sub) │    │ Consumer Pool   │
│                 │    │ ┌─────┐ ┌─────┐ │
│ ┌─────────────┐ │    │ │Con1 │ │Con2 │ │
│ │ Task Queue  │◀┼────┤ └─────┘ └─────┘ │
│ │ - Task A    │ │    │ ┌─────┐ ┌─────┐ │
│ │ - Task B    │ │    │ │Con3 │ │Con4 │ │
│ │ - Task C    │ │    │ └─────┘ └─────┘ │
│ └─────────────┘ │    └─────────────────┘
└─────────────────┘
```

## 🚀 **Usage Examples**

### 🔴 **Start a Redis Consumer**

```python
# Start consuming from Redis queue
{
  "method": "start_consumer",
  "params": {
    "consumer_id": "redis_worker_1",
    "broker_type": "redis",
    "broker_config": {
      "redis_url": "redis://localhost:6379"
    },
    "queue_name": "langswarm_tasks",
    "max_workers": 5,
    "poll_interval": 1,
    "task_timeout": 300
  }
}
```

### 🟢 **Start a GCP Pub/Sub Consumer**

```python
# Enterprise-grade consumer with GCP Pub/Sub
{
  "method": "start_consumer",
  "params": {
    "consumer_id": "enterprise_worker",
    "broker_type": "gcp_pubsub",
    "broker_config": {
      "project_id": "my-enterprise-project"
    },
    "queue_name": "enterprise-task-subscription",
    "max_workers": 10,
    "retry_attempts": 5,
    "task_timeout": 600
  }
}
```

### 📊 **Monitor Consumer Performance**

```python
# Get detailed consumer statistics
{
  "method": "get_consumer_stats",
  "params": {
    "consumer_id": "redis_worker_1"
  }
}

# Response:
{
  "consumer_id": "redis_worker_1",
  "status": "running",
  "tasks_processed": 1247,
  "tasks_failed": 23,
  "average_processing_time": 4.2,
  "uptime": 3600.0,
  "current_workers": 3,
  "queue_info": {
    "queue_name": "langswarm_tasks",
    "message_count": 15
  }
}
```

### 🔧 **Management Operations**

```python
# List all active consumers
{
  "method": "list_consumers",
  "params": {"include_stats": true}
}

# Pause consumer for maintenance
{
  "method": "pause_consumer", 
  "params": {"consumer_id": "redis_worker_1"}
}

# Resume after maintenance
{
  "method": "resume_consumer",
  "params": {"consumer_id": "redis_worker_1"}
}

# Graceful shutdown
{
  "method": "stop_consumer",
  "params": {
    "consumer_id": "redis_worker_1",
    "graceful": true
  }
}
```

## ⚙️ **Configuration**

### 🏠 **Local Development Setup**

```yaml
# langswarm.yaml
tools:
  - id: task_consumer
    type: mcpmessage_queue_consumer
    description: "Message queue consumer for task processing"

agents:
  - id: task_processor
    agent_type: openai
    model: gpt-4o
    system_prompt: |
      You process tasks from message queues using the task_consumer tool.
      Start consumers, monitor performance, and handle task processing.
    tools:
      - task_consumer

workflows:
  process_queue_tasks:
    steps:
      - agent: task_processor
        input: "${user_input}"
        output: {to: user}
```

### 🌐 **Distributed Production Setup**

```yaml
# Production configuration with multiple consumers
tools:
  - id: redis_consumer
    type: mcpmessage_queue_consumer
    description: "Redis-based task consumer"
    
  - id: pubsub_consumer  
    type: mcpmessage_queue_consumer
    description: "GCP Pub/Sub consumer for enterprise tasks"

agents:
  - id: redis_task_manager
    system_prompt: |
      You manage Redis-based task consumption for high-speed processing.
      Configure consumers for optimal Redis performance.
    tools: [redis_consumer]
    
  - id: enterprise_task_manager
    system_prompt: |
      You manage enterprise task processing using GCP Pub/Sub.
      Ensure reliable, scalable task processing with proper monitoring.
    tools: [pubsub_consumer]

workflows:
  distributed_task_processing:
    steps:
      - agent: redis_task_manager
        input: "Handle Redis tasks: ${user_input}"
      - agent: enterprise_task_manager  
        input: "Handle enterprise tasks: ${user_input}"
        output: {to: user}
```

## 🔄 **Integration Patterns**

### 🔗 **With Workflow Executor**

```python
# Producer publishes workflow execution task
{
  "type": "workflow_execution",
  "workflow": "document_analysis",
  "data": {
    "document_path": "/uploads/contract.pdf",
    "analysis_type": "legal_review"
  }
}

# Consumer processes using workflow executor
# Automatically integrates with LangSwarm workflow system
```

### 📊 **With Data Processing Pipelines**

```python
# ETL Pipeline Tasks
{
  "type": "data_processing",
  "operation": "transform",
  "data": {
    "source": "database",
    "query": "SELECT * FROM orders WHERE date > '2024-01-01'",
    "transformations": ["normalize", "aggregate", "export"]
  }
}
```

### 🔄 **Event-Driven Architecture**

```
External System → Queue → LangSwarm Consumer → Process → Results → Callback
      │                                                           │
      └─────────────────── Async Notification ◀─────────────────┘
```

## 📊 **Performance & Monitoring**

### 🎯 **Key Performance Metrics**

#### **Throughput Metrics**
- **Tasks/Second**: `tasks_processed / uptime`
- **Success Rate**: `tasks_processed / (tasks_processed + tasks_failed)`
- **Worker Efficiency**: `current_workers / max_workers`

#### **Latency Metrics**
- **Average Processing Time**: Time per task
- **Queue Depth**: Pending tasks in queue
- **End-to-End Latency**: Queue → Complete

#### **Resource Metrics**
- **Memory Usage**: Per worker memory consumption
- **CPU Utilization**: Processing efficiency
- **Connection Health**: Broker connection status

### 📈 **Performance Optimization**

#### **Redis Optimization**
```python
{
  "max_workers": 5,        # Balance with Redis performance
  "poll_interval": 1,      # Fast polling for low latency
  "task_timeout": 300      # Based on task complexity
}
```

#### **GCP Pub/Sub Optimization**
```python
{
  "max_workers": 15,       # Higher concurrency supported
  "poll_interval": 5,      # Efficient long polling
  "task_timeout": 600      # Enterprise task complexity
}
```

#### **Resource-Based Tuning**
```python
# CPU-intensive tasks
{"max_workers": 2, "task_timeout": 900}

# I/O-intensive tasks  
{"max_workers": 10, "task_timeout": 300}

# Mixed workload
{"max_workers": 5, "task_timeout": 450}
```

## 🛠️ **Production Deployment**

### 🐳 **Docker Deployment**

```dockerfile
FROM python:3.9-slim

# Install LangSwarm with message queue consumer
COPY . /app/langswarm/
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Configure consumer
ENV REDIS_URL=redis://redis:6379
ENV GCP_PROJECT_ID=my-project

# Start consumer service
CMD ["python", "-m", "langswarm.mcp.tools.message_queue_consumer.main"]
```

### ☸️ **Kubernetes Deployment**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langswarm-consumer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: langswarm-consumer
  template:
    metadata:
      labels:
        app: langswarm-consumer
    spec:
      containers:
      - name: consumer
        image: langswarm/consumer:latest
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi" 
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: langswarm-consumer-service
spec:
  selector:
    app: langswarm-consumer
  ports:
  - port: 4021
    targetPort: 4021
```

### 🔄 **Auto-Scaling Configuration**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: langswarm-consumer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: langswarm-consumer
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🔒 **Security & Best Practices**

### 🔐 **Authentication & Authorization**

#### **Redis Security**
```python
{
  "broker_config": {
    "redis_url": "rediss://user:password@redis.example.com:6380/0",
    "ssl_cert_reqs": "required",
    "ssl_ca_certs": "/path/to/ca.pem"
  }
}
```

#### **GCP Pub/Sub Security**
```python
{
  "broker_config": {
    "project_id": "secure-project",
    "credentials_path": "/path/to/service-account.json",
    "subscription_settings": {
      "ack_deadline": 600,
      "message_retention_duration": 7200
    }
  }
}
```

### 🛡️ **Data Protection**

#### **Task Data Encryption**
- Encrypt sensitive data before queuing
- Use environment variables for secrets
- Implement audit logging for compliance

#### **Network Security**
- Use TLS for all broker connections
- Configure VPC/network isolation
- Implement IP allowlisting where possible

### 📋 **Operational Best Practices**

#### **Monitoring & Alerting**
- Monitor consumer health and performance
- Set up alerts for high failure rates
- Track queue depth and processing lag

#### **Backup & Recovery**
- Implement graceful shutdown procedures
- Use persistent storage for critical state
- Plan for broker failover scenarios

#### **Capacity Planning**
- Monitor resource utilization trends
- Plan scaling based on workload patterns
- Test recovery procedures regularly

## 🚀 **Advanced Use Cases**

### 🔄 **Event-Driven Microservices**

```python
# Order Processing Pipeline
{
  "type": "workflow_execution",
  "workflow": "order_processing",
  "data": {
    "order_id": "ORD-12345",
    "customer_id": "CUST-67890",
    "items": [{"sku": "ITEM-001", "quantity": 2}],
    "priority": "high"
  }
}
```

### 📊 **Real-Time Analytics**

```python
# Analytics Processing Task
{
  "type": "data_processing", 
  "operation": "analytics",
  "data": {
    "event_stream": "user_interactions",
    "time_window": "1h",
    "metrics": ["conversion_rate", "engagement_score"]
  }
}
```

### 🔧 **Batch Processing**

```python
# Large Dataset Processing
{
  "type": "file_processing",
  "operation": "batch_transform",
  "data": {
    "input_path": "/data/batch/2024-01-15/",
    "output_path": "/processed/2024-01-15/",
    "transformation": "ml_feature_extraction"
  }
}
```

### 🌐 **API Integration Hub**

```python
# External API Integration
{
  "type": "api_call",
  "url": "https://external-service.com/api/v1/process",
  "method": "POST",
  "headers": {"Authorization": "Bearer token"},
  "data": {"payload": "to_process"},
  "callback_url": "https://my-service.com/callback"
}
```

## 🏆 **Benefits**

### 🎯 **For Organizations**
- **Distributed Processing**: Scale task processing across multiple instances
- **Cost Efficiency**: Pay only for processing time used
- **Reliability**: Enterprise-grade message brokers with guaranteed delivery
- **Flexibility**: Support multiple broker types and deployment patterns

### 🚀 **For Developers**
- **Easy Integration**: Simple API for complex distributed processing
- **Multiple Brokers**: Choose the right broker for your use case
- **Built-in Monitoring**: Real-time visibility into task processing
- **Production Ready**: Robust error handling and recovery mechanisms

### 🧠 **For AI Agents**
- **Task Intelligence**: Process various task types with context awareness
- **Workflow Integration**: Seamlessly integrate with LangSwarm workflows
- **Resource Management**: Intelligent worker allocation and scaling
- **Error Recovery**: Automatic retry and failure handling

## 🔮 **Future Enhancements**

### **Planned Features**
- Visual task processing dashboard
- Advanced load balancing algorithms
- Integration with more message brokers (RabbitMQ, Apache Kafka)
- Machine learning-based performance optimization

### **Integration Roadmap**
- Kubernetes operator for automated scaling
- Prometheus metrics integration
- Dead letter queue handling
- Task priority and scheduling

---

## 🎯 **Quick Start**

### **1. Basic Setup (5 minutes)**
```python
# Start a simple Redis consumer
{
  "method": "start_consumer",
  "params": {
    "consumer_id": "my_worker",
    "broker_type": "redis", 
    "broker_config": {"redis_url": "redis://localhost:6379"},
    "queue_name": "tasks"
  }
}
```

### **2. Monitor Processing**
```python
# Check consumer status
{"method": "get_consumer_stats", "params": {"consumer_id": "my_worker"}}
```

### **3. Scale Up**
```python
# Start additional consumers for higher throughput
{"method": "start_consumer", "params": {"consumer_id": "worker_2", ...}}
{"method": "start_consumer", "params": {"consumer_id": "worker_3", ...}}
```

**Transform LangSwarm into a distributed task processing powerhouse with the Message Queue Consumer MCP Tool!** 🚀

---

**Ready to build distributed, scalable task processing systems? Start with Redis for simplicity or GCP Pub/Sub for enterprise scale!**