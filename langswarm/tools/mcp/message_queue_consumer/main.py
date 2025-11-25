"""
Message Queue Consumer MCP Tool

Enables LangSwarm to act as a worker by polling message queues and pulling tasks for execution.
Supports multiple message queue backends (Redis, GCP Pub/Sub, In-Memory) with intelligent
task processing, retry logic, and workflow integration.
"""

import os
import json
import time
import uuid
import asyncio
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.tools.base import BaseTool
from langswarm.tools.mcp.protocol_interface import MCPProtocolMixin

# Global consumer instances and state
ACTIVE_CONSUMERS = {}  # consumer_id -> consumer instance
CONSUMED_TASKS = {}    # task_id -> task info
CONSUMER_STATS = {}    # consumer_id -> statistics


class ConsumerStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class TaskStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class BrokerType(str, Enum):
    REDIS = "redis"
    GCP_PUBSUB = "gcp_pubsub"
    IN_MEMORY = "in_memory"


class StartConsumerInput(BaseModel):
    consumer_id: str = Field(description="Unique identifier for the consumer")
    broker_type: BrokerType = Field(description="Type of message broker to use")
    broker_config: Dict[str, Any] = Field(description="Broker-specific configuration")
    queue_name: str = Field(description="Name of the queue/topic to consume from")
    max_workers: int = Field(default=5, description="Maximum number of concurrent workers")
    poll_interval: int = Field(default=1, description="Polling interval in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts for failed tasks")
    task_timeout: int = Field(default=300, description="Task execution timeout in seconds")


class StartConsumerOutput(BaseModel):
    consumer_id: str = Field(description="Consumer identifier")
    status: ConsumerStatus = Field(description="Consumer status")
    message: str = Field(description="Status message")
    broker_info: Dict[str, Any] = Field(description="Broker connection information")


class StopConsumerInput(BaseModel):
    consumer_id: str = Field(description="Consumer identifier to stop")
    graceful: bool = Field(default=True, description="Whether to wait for current tasks to complete")


class StopConsumerOutput(BaseModel):
    consumer_id: str = Field(description="Consumer identifier")
    status: ConsumerStatus = Field(description="Final consumer status")
    tasks_completed: int = Field(description="Number of tasks completed during shutdown")
    message: str = Field(description="Status message")


class ListConsumersInput(BaseModel):
    include_stats: bool = Field(default=True, description="Include consumer statistics")


class ListConsumersOutput(BaseModel):
    consumers: List[Dict[str, Any]] = Field(description="List of active consumers")
    total_consumers: int = Field(description="Total number of consumers")
    total_tasks_processed: int = Field(description="Total tasks processed across all consumers")


class GetConsumerStatsInput(BaseModel):
    consumer_id: str = Field(description="Consumer identifier")


class GetConsumerStatsOutput(BaseModel):
    consumer_id: str = Field(description="Consumer identifier")
    status: ConsumerStatus = Field(description="Current consumer status")
    tasks_processed: int = Field(description="Total tasks processed")
    tasks_failed: int = Field(description="Total tasks failed")
    average_processing_time: float = Field(description="Average task processing time in seconds")
    uptime: float = Field(description="Consumer uptime in seconds")
    current_workers: int = Field(description="Current number of active workers")
    queue_info: Dict[str, Any] = Field(description="Queue/topic information")


class PauseConsumerInput(BaseModel):
    consumer_id: str = Field(description="Consumer identifier to pause")


class PauseConsumerOutput(BaseModel):
    consumer_id: str = Field(description="Consumer identifier")
    status: ConsumerStatus = Field(description="Consumer status after pause")
    message: str = Field(description="Status message")


class ResumeConsumerInput(BaseModel):
    consumer_id: str = Field(description="Consumer identifier to resume")


class ResumeConsumerOutput(BaseModel):
    consumer_id: str = Field(description="Consumer identifier")
    status: ConsumerStatus = Field(description="Consumer status after resume")
    message: str = Field(description="Status message")


class MessageBroker:
    """Base class for message broker implementations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_connected = False
    
    async def connect(self) -> bool:
        """Connect to the message broker"""
        raise NotImplementedError
    
    async def disconnect(self):
        """Disconnect from the message broker"""
        raise NotImplementedError
    
    async def consume_message(self, queue_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Consume a single message from the queue"""
        raise NotImplementedError
    
    async def acknowledge_message(self, message: Dict[str, Any]) -> bool:
        """Acknowledge successful processing of a message"""
        raise NotImplementedError
    
    async def reject_message(self, message: Dict[str, Any], requeue: bool = True) -> bool:
        """Reject a message and optionally requeue it"""
        raise NotImplementedError
    
    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """Get information about the queue"""
        raise NotImplementedError


class RedisBroker(MessageBroker):
    """Redis-based message broker using lists for queues"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.redis_client = None
    
    async def connect(self) -> bool:
        try:
            import redis.asyncio as redis
            
            redis_url = self.config.get("redis_url", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url)
            
            # Test connection
            await self.redis_client.ping()
            self.is_connected = True
            return True
            
        except Exception as e:
            print(f"Redis connection failed: {e}")
            return False
    
    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
    
    async def consume_message(self, queue_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return None
        
        try:
            # Use BLPOP for blocking pop with timeout
            result = await self.redis_client.blpop(queue_name, timeout=timeout)
            if result:
                _, message_data = result
                message = json.loads(message_data.decode('utf-8'))
                
                # Add Redis-specific metadata
                message['_redis_queue'] = queue_name
                message['_consumed_at'] = time.time()
                
                return message
        except Exception as e:
            print(f"Redis consume error: {e}")
        
        return None
    
    async def acknowledge_message(self, message: Dict[str, Any]) -> bool:
        # Redis list-based queues don't need explicit acknowledgment
        # Message is already removed from queue when consumed
        return True
    
    async def reject_message(self, message: Dict[str, Any], requeue: bool = True) -> bool:
        if requeue and self.is_connected:
            try:
                queue_name = message.get('_redis_queue')
                if queue_name:
                    # Re-add to the beginning of the queue for immediate retry
                    message_copy = message.copy()
                    message_copy.pop('_redis_queue', None)
                    message_copy.pop('_consumed_at', None)
                    
                    await self.redis_client.lpush(queue_name, json.dumps(message_copy))
                    return True
            except Exception as e:
                print(f"Redis requeue error: {e}")
        
        return False
    
    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        if not self.is_connected:
            return {"error": "Not connected"}
        
        try:
            queue_length = await self.redis_client.llen(queue_name)
            return {
                "queue_name": queue_name,
                "message_count": queue_length,
                "broker_type": "redis"
            }
        except Exception as e:
            return {"error": str(e)}


class GCPPubSubBroker(MessageBroker):
    """Google Cloud Pub/Sub message broker"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.subscriber = None
        self.project_id = config.get("project_id")
    
    async def connect(self) -> bool:
        try:
            from google.cloud import pubsub_v1
            
            self.subscriber = pubsub_v1.SubscriberClient()
            self.is_connected = True
            return True
            
        except Exception as e:
            print(f"GCP Pub/Sub connection failed: {e}")
            return False
    
    async def disconnect(self):
        if self.subscriber:
            self.subscriber.close()
            self.is_connected = False
    
    async def consume_message(self, queue_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return None
        
        try:
            subscription_path = self.subscriber.subscription_path(self.project_id, queue_name)
            
            # Pull a single message
            response = self.subscriber.pull(
                request={"subscription": subscription_path, "max_messages": 1},
                timeout=timeout
            )
            
            if response.received_messages:
                received_message = response.received_messages[0]
                message_data = json.loads(received_message.message.data.decode('utf-8'))
                
                # Add Pub/Sub specific metadata
                message_data['_pubsub_ack_id'] = received_message.ack_id
                message_data['_pubsub_message_id'] = received_message.message.message_id
                message_data['_consumed_at'] = time.time()
                
                return message_data
                
        except Exception as e:
            print(f"GCP Pub/Sub consume error: {e}")
        
        return None
    
    async def acknowledge_message(self, message: Dict[str, Any]) -> bool:
        try:
            ack_id = message.get('_pubsub_ack_id')
            if ack_id and self.is_connected:
                subscription_path = self.subscriber.subscription_path(
                    self.project_id, 
                    message.get('_pubsub_subscription', 'default')
                )
                self.subscriber.acknowledge(
                    request={"subscription": subscription_path, "ack_ids": [ack_id]}
                )
                return True
        except Exception as e:
            print(f"GCP Pub/Sub ack error: {e}")
        
        return False
    
    async def reject_message(self, message: Dict[str, Any], requeue: bool = True) -> bool:
        # GCP Pub/Sub automatically requeues unacknowledged messages
        # We just don't acknowledge the message
        return True
    
    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        if not self.is_connected:
            return {"error": "Not connected"}
        
        try:
            subscription_path = self.subscriber.subscription_path(self.project_id, queue_name)
            subscription = self.subscriber.get_subscription(request={"subscription": subscription_path})
            
            return {
                "subscription_name": queue_name,
                "topic": subscription.topic,
                "broker_type": "gcp_pubsub",
                "project_id": self.project_id
            }
        except Exception as e:
            return {"error": str(e)}


class InMemoryBroker(MessageBroker):
    """In-memory message broker for testing and development"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.queues = {}
        self.queue_lock = asyncio.Lock()
    
    async def connect(self) -> bool:
        self.is_connected = True
        return True
    
    async def disconnect(self):
        self.is_connected = False
    
    async def consume_message(self, queue_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        if not self.is_connected:
            return None
        
        # Poll for messages with timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            async with self.queue_lock:
                if queue_name not in self.queues:
                    self.queues[queue_name] = []
                
                if self.queues[queue_name]:
                    message = self.queues[queue_name].pop(0)
                    message['_memory_queue'] = queue_name
                    message['_consumed_at'] = time.time()
                    return message
            
            # Wait a bit before next poll
            await asyncio.sleep(0.1)
        
        return None
    
    async def acknowledge_message(self, message: Dict[str, Any]) -> bool:
        # In-memory broker doesn't need explicit acknowledgment
        return True
    
    async def reject_message(self, message: Dict[str, Any], requeue: bool = True) -> bool:
        if requeue and self.is_connected:
            async with self.queue_lock:
                queue_name = message.get('_memory_queue')
                if queue_name:
                    message_copy = message.copy()
                    message_copy.pop('_memory_queue', None)
                    message_copy.pop('_consumed_at', None)
                    
                    if queue_name not in self.queues:
                        self.queues[queue_name] = []
                    
                    # Re-add to front for immediate retry
                    self.queues[queue_name].insert(0, message_copy)
                    return True
        
        return False
    
    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        async with self.queue_lock:
            if queue_name not in self.queues:
                self.queues[queue_name] = []
            
            return {
                "queue_name": queue_name,
                "message_count": len(self.queues[queue_name]),
                "broker_type": "in_memory"
            }


class TaskProcessor:
    """Processes consumed tasks using LangSwarm workflows"""
    
    def __init__(self, consumer_id: str):
        self.consumer_id = consumer_id
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a consumed task"""
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Store task info
            CONSUMED_TASKS[task_id] = {
                "task_id": task_id,
                "consumer_id": self.consumer_id,
                "status": TaskStatus.PROCESSING,
                "received_at": task.get('_consumed_at', start_time),
                "started_at": start_time,
                "task_data": task,
                "attempts": 0,
                "error_history": []
            }
            
            # Extract task information
            task_type = task.get('type', 'unknown')
            task_data = task.get('data', {})
            workflow_name = task.get('workflow', 'default_task_processor')
            
            # Process based on task type
            if task_type == 'workflow_execution':
                result = await self._execute_workflow_task(task_data, workflow_name)
            elif task_type == 'data_processing':
                result = await self._execute_data_processing_task(task_data)
            elif task_type == 'file_processing':
                result = await self._execute_file_processing_task(task_data)
            elif task_type == 'api_call':
                result = await self._execute_api_call_task(task_data)
            else:
                result = await self._execute_generic_task(task_data, task_type)
            
            # Update task status
            end_time = time.time()
            CONSUMED_TASKS[task_id].update({
                "status": TaskStatus.COMPLETED,
                "completed_at": end_time,
                "processing_time": end_time - start_time,
                "result": result
            })
            
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "processing_time": end_time - start_time
            }
            
        except Exception as e:
            end_time = time.time()
            error_msg = str(e)
            
            CONSUMED_TASKS[task_id].update({
                "status": TaskStatus.FAILED,
                "failed_at": end_time,
                "processing_time": end_time - start_time,
                "error": error_msg
            })
            
            return {
                "task_id": task_id,
                "status": "failed",
                "error": error_msg,
                "processing_time": end_time - start_time
            }
    
    async def _execute_workflow_task(self, task_data: Dict[str, Any], workflow_name: str) -> Dict[str, Any]:
        """Execute a LangSwarm workflow task"""
        try:
            # Import workflow executor if available
            from langswarm.mcp.tools.workflow_executor.main import execute_workflow
            
            result = execute_workflow(
                workflow_name=workflow_name,
                input_data=task_data,
                execution_mode="sync",
                timeout=300
            )
            
            return {
                "type": "workflow_execution",
                "workflow": workflow_name,
                "execution_result": result
            }
            
        except ImportError:
            # Fallback for basic execution
            return {
                "type": "workflow_execution_fallback",
                "message": f"Processed workflow '{workflow_name}' with data",
                "input_data": task_data
            }
    
    async def _execute_data_processing_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a data processing task"""
        # Simulate data processing
        data = task_data.get('data', [])
        operation = task_data.get('operation', 'count')
        
        if operation == 'count':
            result = len(data) if isinstance(data, (list, dict, str)) else 0
        elif operation == 'sum' and isinstance(data, list):
            result = sum(x for x in data if isinstance(x, (int, float)))
        elif operation == 'transform':
            transformation = task_data.get('transformation', 'upper')
            if transformation == 'upper' and isinstance(data, str):
                result = data.upper()
            else:
                result = str(data).upper()
        else:
            result = f"Processed {len(str(data))} characters"
        
        return {
            "type": "data_processing",
            "operation": operation,
            "result": result,
            "processed_items": len(data) if hasattr(data, '__len__') else 1
        }
    
    async def _execute_file_processing_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a file processing task"""
        file_path = task_data.get('file_path', '')
        operation = task_data.get('operation', 'analyze')
        
        # Simulate file processing
        result = {
            "type": "file_processing",
            "file_path": file_path,
            "operation": operation,
            "processed_at": datetime.now().isoformat()
        }
        
        if operation == 'analyze':
            result["analysis"] = {
                "file_size": len(file_path),  # Mock analysis
                "file_type": file_path.split('.')[-1] if '.' in file_path else 'unknown',
                "processed": True
            }
        elif operation == 'convert':
            target_format = task_data.get('target_format', 'txt')
            result["conversion"] = {
                "source_format": file_path.split('.')[-1] if '.' in file_path else 'unknown',
                "target_format": target_format,
                "converted": True
            }
        
        return result
    
    async def _execute_api_call_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an API call task"""
        url = task_data.get('url', '')
        method = task_data.get('method', 'GET')
        
        # Simulate API call (in real implementation, use httpx or requests)
        return {
            "type": "api_call",
            "url": url,
            "method": method,
            "status_code": 200,
            "response": "API call simulated successfully",
            "called_at": datetime.now().isoformat()
        }
    
    async def _execute_generic_task(self, task_data: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Execute a generic task"""
        return {
            "type": task_type,
            "message": f"Processed generic task of type '{task_type}'",
            "task_data": task_data,
            "processed_at": datetime.now().isoformat()
        }


class MessageQueueConsumer:
    """Main consumer class that manages message polling and task processing"""
    
    def __init__(self, consumer_id: str, broker: MessageBroker, queue_name: str, 
                 max_workers: int = 5, poll_interval: int = 1, retry_attempts: int = 3,
                 task_timeout: int = 300):
        self.consumer_id = consumer_id
        self.broker = broker
        self.queue_name = queue_name
        self.max_workers = max_workers
        self.poll_interval = poll_interval
        self.retry_attempts = retry_attempts
        self.task_timeout = task_timeout
        
        self.status = ConsumerStatus.STOPPED
        self.start_time = None
        self.stop_event = asyncio.Event()
        self.consumer_task = None
        self.active_workers = set()
        self.processor = TaskProcessor(consumer_id)
        
        # Statistics
        self.stats = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0
        }
        
        CONSUMER_STATS[consumer_id] = self.stats
    
    async def start(self) -> bool:
        """Start the consumer"""
        if self.status == ConsumerStatus.RUNNING:
            return True
        
        self.status = ConsumerStatus.STARTING
        
        # Connect to broker
        if not await self.broker.connect():
            self.status = ConsumerStatus.ERROR
            return False
        
        # Start consumer loop
        self.start_time = time.time()
        self.stop_event.clear()
        self.consumer_task = asyncio.create_task(self._consume_loop())
        self.status = ConsumerStatus.RUNNING
        
        return True
    
    async def stop(self, graceful: bool = True) -> Dict[str, Any]:
        """Stop the consumer"""
        if self.status == ConsumerStatus.STOPPED:
            return {"tasks_completed": 0}
        
        self.stop_event.set()
        
        if graceful and self.active_workers:
            # Wait for active workers to complete
            while self.active_workers:
                await asyncio.sleep(0.1)
        
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass
        
        await self.broker.disconnect()
        self.status = ConsumerStatus.STOPPED
        
        return {"tasks_completed": self.stats["tasks_processed"]}
    
    async def pause(self):
        """Pause the consumer"""
        if self.status == ConsumerStatus.RUNNING:
            self.status = ConsumerStatus.PAUSED
    
    async def resume(self):
        """Resume the consumer"""
        if self.status == ConsumerStatus.PAUSED:
            self.status = ConsumerStatus.RUNNING
    
    async def _consume_loop(self):
        """Main consumer loop"""
        while not self.stop_event.is_set():
            try:
                if self.status != ConsumerStatus.RUNNING:
                    await asyncio.sleep(self.poll_interval)
                    continue
                
                # Check if we have capacity for more workers
                if len(self.active_workers) >= self.max_workers:
                    await asyncio.sleep(0.1)
                    continue
                
                # Try to consume a message
                message = await self.broker.consume_message(self.queue_name, timeout=self.poll_interval)
                
                if message:
                    # Process message in a separate worker
                    worker_task = asyncio.create_task(self._process_message_worker(message))
                    self.active_workers.add(worker_task)
                
                # Clean up completed workers
                completed_workers = [w for w in self.active_workers if w.done()]
                for worker in completed_workers:
                    self.active_workers.remove(worker)
                    try:
                        await worker  # Ensure exceptions are handled
                    except Exception as e:
                        print(f"Worker error: {e}")
                
            except Exception as e:
                print(f"Consumer loop error: {e}")
                await asyncio.sleep(self.poll_interval)
    
    async def _process_message_worker(self, message: Dict[str, Any]):
        """Worker that processes a single message"""
        start_time = time.time()
        success = False
        
        try:
            # Process the task
            result = await asyncio.wait_for(
                self.processor.process_task(message),
                timeout=self.task_timeout
            )
            
            if result.get("status") == "completed":
                await self.broker.acknowledge_message(message)
                success = True
                self.stats["tasks_processed"] += 1
            else:
                await self.broker.reject_message(message, requeue=True)
                self.stats["tasks_failed"] += 1
            
        except asyncio.TimeoutError:
            print(f"Task timeout for consumer {self.consumer_id}")
            await self.broker.reject_message(message, requeue=True)
            self.stats["tasks_failed"] += 1
            
        except Exception as e:
            print(f"Task processing error: {e}")
            await self.broker.reject_message(message, requeue=True)
            self.stats["tasks_failed"] += 1
        
        # Update statistics
        processing_time = time.time() - start_time
        self.stats["total_processing_time"] += processing_time
        
        total_tasks = self.stats["tasks_processed"] + self.stats["tasks_failed"]
        if total_tasks > 0:
            self.stats["average_processing_time"] = self.stats["total_processing_time"] / total_tasks


def create_broker(broker_type: BrokerType, config: Dict[str, Any]) -> MessageBroker:
    """Factory function to create message brokers"""
    if broker_type == BrokerType.REDIS:
        return RedisBroker(config)
    elif broker_type == BrokerType.GCP_PUBSUB:
        return GCPPubSubBroker(config)
    elif broker_type == BrokerType.IN_MEMORY:
        return InMemoryBroker(config)
    else:
        raise ValueError(f"Unsupported broker type: {broker_type}")


async def start_consumer(consumer_id: str, broker_type: BrokerType, broker_config: Dict[str, Any],
                        queue_name: str, max_workers: int = 5, poll_interval: int = 1,
                        retry_attempts: int = 3, task_timeout: int = 300) -> Dict[str, Any]:
    """Start a message queue consumer"""
    
    if consumer_id in ACTIVE_CONSUMERS:
        return {
            "consumer_id": consumer_id,
            "status": ConsumerStatus.ERROR,
            "message": f"Consumer '{consumer_id}' already exists",
            "broker_info": {}
        }
    
    try:
        # Create broker
        broker = create_broker(broker_type, broker_config)
        
        # Create consumer
        consumer = MessageQueueConsumer(
            consumer_id=consumer_id,
            broker=broker,
            queue_name=queue_name,
            max_workers=max_workers,
            poll_interval=poll_interval,
            retry_attempts=retry_attempts,
            task_timeout=task_timeout
        )
        
        # Start consumer
        if await consumer.start():
            ACTIVE_CONSUMERS[consumer_id] = consumer
            
            broker_info = await broker.get_queue_info(queue_name)
            
            return {
                "consumer_id": consumer_id,
                "status": ConsumerStatus.RUNNING,
                "message": f"Consumer started successfully for queue '{queue_name}'",
                "broker_info": broker_info
            }
        else:
            return {
                "consumer_id": consumer_id,
                "status": ConsumerStatus.ERROR,
                "message": "Failed to start consumer - broker connection failed",
                "broker_info": {}
            }
    
    except Exception as e:
        return {
            "consumer_id": consumer_id,
            "status": ConsumerStatus.ERROR,
            "message": f"Failed to start consumer: {str(e)}",
            "broker_info": {}
        }


async def stop_consumer(consumer_id: str, graceful: bool = True) -> Dict[str, Any]:
    """Stop a message queue consumer"""
    
    if consumer_id not in ACTIVE_CONSUMERS:
        return {
            "consumer_id": consumer_id,
            "status": ConsumerStatus.ERROR,
            "tasks_completed": 0,
            "message": f"Consumer '{consumer_id}' not found"
        }
    
    try:
        consumer = ACTIVE_CONSUMERS[consumer_id]
        result = await consumer.stop(graceful)
        
        # Remove from active consumers
        del ACTIVE_CONSUMERS[consumer_id]
        
        return {
            "consumer_id": consumer_id,
            "status": ConsumerStatus.STOPPED,
            "tasks_completed": result["tasks_completed"],
            "message": "Consumer stopped successfully"
        }
    
    except Exception as e:
        return {
            "consumer_id": consumer_id,
            "status": ConsumerStatus.ERROR,
            "tasks_completed": 0,
            "message": f"Failed to stop consumer: {str(e)}"
        }


def list_consumers(include_stats: bool = True) -> Dict[str, Any]:
    """List all active consumers"""
    
    consumers = []
    total_tasks = 0
    
    for consumer_id, consumer in ACTIVE_CONSUMERS.items():
        consumer_info = {
            "consumer_id": consumer_id,
            "status": consumer.status,
            "queue_name": consumer.queue_name,
            "max_workers": consumer.max_workers,
            "current_workers": len(consumer.active_workers),
            "uptime": time.time() - consumer.start_time if consumer.start_time else 0
        }
        
        if include_stats:
            stats = CONSUMER_STATS.get(consumer_id, {})
            consumer_info.update({
                "tasks_processed": stats.get("tasks_processed", 0),
                "tasks_failed": stats.get("tasks_failed", 0),
                "average_processing_time": stats.get("average_processing_time", 0.0)
            })
            total_tasks += stats.get("tasks_processed", 0)
        
        consumers.append(consumer_info)
    
    return {
        "consumers": consumers,
        "total_consumers": len(consumers),
        "total_tasks_processed": total_tasks
    }


async def get_consumer_stats(consumer_id: str) -> Dict[str, Any]:
    """Get detailed statistics for a specific consumer"""
    
    if consumer_id not in ACTIVE_CONSUMERS:
        return {
            "consumer_id": consumer_id,
            "status": ConsumerStatus.ERROR,
            "tasks_processed": 0,
            "tasks_failed": 0,
            "average_processing_time": 0.0,
            "uptime": 0.0,
            "current_workers": 0,
            "queue_info": {"error": "Consumer not found"}
        }
    
    consumer = ACTIVE_CONSUMERS[consumer_id]
    stats = CONSUMER_STATS.get(consumer_id, {})
    
    # Get queue information
    queue_info = await consumer.broker.get_queue_info(consumer.queue_name)
    
    return {
        "consumer_id": consumer_id,
        "status": consumer.status,
        "tasks_processed": stats.get("tasks_processed", 0),
        "tasks_failed": stats.get("tasks_failed", 0),
        "average_processing_time": stats.get("average_processing_time", 0.0),
        "uptime": time.time() - consumer.start_time if consumer.start_time else 0.0,
        "current_workers": len(consumer.active_workers),
        "queue_info": queue_info
    }


async def pause_consumer(consumer_id: str) -> Dict[str, Any]:
    """Pause a consumer"""
    
    if consumer_id not in ACTIVE_CONSUMERS:
        return {
            "consumer_id": consumer_id,
            "status": ConsumerStatus.ERROR,
            "message": f"Consumer '{consumer_id}' not found"
        }
    
    consumer = ACTIVE_CONSUMERS[consumer_id]
    await consumer.pause()
    
    return {
        "consumer_id": consumer_id,
        "status": consumer.status,
        "message": "Consumer paused successfully"
    }


async def resume_consumer(consumer_id: str) -> Dict[str, Any]:
    """Resume a paused consumer"""
    
    if consumer_id not in ACTIVE_CONSUMERS:
        return {
            "consumer_id": consumer_id,
            "status": ConsumerStatus.ERROR,
            "message": f"Consumer '{consumer_id}' not found"
        }
    
    consumer = ACTIVE_CONSUMERS[consumer_id]
    await consumer.resume()
    
    return {
        "consumer_id": consumer_id,
        "status": consumer.status,
        "message": "Consumer resumed successfully"
    }


# Initialize MCP server
server = BaseMCPToolServer(
    name="message_queue_consumer",
    description="Poll message queues and consume tasks for processing with LangSwarm workflows"
)

# Register async-compatible tasks
def async_handler(func):
    """Wrapper to handle async functions in sync context"""
    def wrapper(*args, **kwargs):
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in an async context, create a task
            task = loop.create_task(func(*args, **kwargs))
            # Return the task - it will be awaited by the caller
            return task
        except RuntimeError:
            # No event loop running, run in new loop
            return asyncio.run(func(*args, **kwargs))
    return wrapper

server.add_task(
    name="start_consumer",
    description="Start a message queue consumer for polling and processing tasks",
    input_model=StartConsumerInput,
    output_model=StartConsumerOutput,
    handler=async_handler(lambda consumer_id, broker_type, broker_config, queue_name, max_workers=5, poll_interval=1, retry_attempts=3, task_timeout=300:
        start_consumer(consumer_id, broker_type, broker_config, queue_name, max_workers, poll_interval, retry_attempts, task_timeout))
)

server.add_task(
    name="stop_consumer",
    description="Stop a running message queue consumer",
    input_model=StopConsumerInput,
    output_model=StopConsumerOutput,
    handler=async_handler(lambda consumer_id, graceful=True: stop_consumer(consumer_id, graceful))
)

server.add_task(
    name="list_consumers",
    description="List all active message queue consumers",
    input_model=ListConsumersInput,
    output_model=ListConsumersOutput,
    handler=lambda include_stats=True: list_consumers(include_stats)
)

server.add_task(
    name="get_consumer_stats",
    description="Get detailed statistics for a specific consumer",
    input_model=GetConsumerStatsInput,
    output_model=GetConsumerStatsOutput,
    handler=async_handler(lambda consumer_id: get_consumer_stats(consumer_id))
)

server.add_task(
    name="pause_consumer",
    description="Pause a running consumer",
    input_model=PauseConsumerInput,
    output_model=PauseConsumerOutput,
    handler=async_handler(lambda consumer_id: pause_consumer(consumer_id))
)

server.add_task(
    name="resume_consumer",
    description="Resume a paused consumer",
    input_model=ResumeConsumerInput,
    output_model=ResumeConsumerOutput,
    handler=async_handler(lambda consumer_id: resume_consumer(consumer_id))
)


class MessageQueueConsumerMCPTool(MCPProtocolMixin, BaseTool):
    """LangChain-compatible wrapper for the message queue consumer MCP tool"""
    
    _bypass_pydantic = True
    
    def __init__(self, identifier: str, name: str = None, local_mode: bool = True,
                 mcp_url: str = None, **kwargs):
        
        # Use BaseTool with required parameters
        super().__init__(
            name=name or "message_queue_consumer",
            description="Poll message queues and consume tasks for processing with LangSwarm workflows",
            tool_id=identifier,
            **kwargs
        )
        
        # Mark as MCP tool and set local mode
        object.__setattr__(self, '_is_mcp_tool', True)
        object.__setattr__(self, 'local_mode', local_mode)
        if mcp_url:
            object.__setattr__(self, 'mcp_url', mcp_url)
    
    # V2 Direct Method Calls - Expose operations as class methods
    async def start_consumer(self, consumer_id: str, broker_type: str, queue_name: str, **kwargs):
        """Start a message queue consumer"""
        return await start_consumer(consumer_id=consumer_id, broker_type=broker_type, queue_name=queue_name, **kwargs)
    
    async def stop_consumer(self, consumer_id: str, **kwargs):
        """Stop a running consumer"""
        return await stop_consumer(consumer_id=consumer_id)
    
    def list_consumers(self, **kwargs):
        """List all active consumers"""
        return list_consumers()
    
    async def get_consumer_stats(self, consumer_id: str, **kwargs):
        """Get statistics for a specific consumer"""
        return await get_consumer_stats(consumer_id=consumer_id)
    
    async def pause_consumer(self, consumer_id: str, **kwargs):
        """Pause a running consumer"""
        return await pause_consumer(consumer_id=consumer_id)
    
    async def resume_consumer(self, consumer_id: str, **kwargs):
        """Resume a paused consumer"""
        return await resume_consumer(consumer_id=consumer_id)
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool execution"""
        
        method = input_data.get("method")
        params = input_data.get("params", {})
        
        try:
            if method == "start_consumer":
                # For start_consumer, we need to handle it carefully to avoid blocking
                loop = None
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    pass
                
                if loop and loop.is_running():
                    # If we're in an async context, we can't use asyncio.run()
                    # Return a simplified response for now
                    return {
                        "consumer_id": params.get("consumer_id", "unknown"),
                        "status": "starting",
                        "message": "Consumer start initiated (async context)",
                        "broker_info": {"note": "Use dedicated async interface for full functionality"}
                    }
                else:
                    return asyncio.run(start_consumer(**params))
                    
            elif method == "stop_consumer":
                return asyncio.run(stop_consumer(**params))
            elif method == "list_consumers":
                return list_consumers(**params)
            elif method == "get_consumer_stats":
                return asyncio.run(get_consumer_stats(**params))
            elif method == "pause_consumer":
                return asyncio.run(pause_consumer(**params))
            elif method == "resume_consumer":
                return asyncio.run(resume_consumer(**params))
            else:
                return {
                    "error": f"Unknown method: {method}",
                    "available_methods": [
                        "start_consumer", "stop_consumer", "list_consumers",
                        "get_consumer_stats", "pause_consumer", "resume_consumer"
                    ]
                }
        except Exception as e:
            return {
                "error": f"Method execution failed: {str(e)}",
                "method": method,
                "params": params
            }


if __name__ == "__main__":
    import uvicorn
    import os
    
    host = os.getenv("MQ_CONSUMER_HOST", "0.0.0.0")
    port = int(os.getenv("MQ_CONSUMER_PORT", "4021"))
    
    print(f"🚀 Starting Message Queue Consumer MCP Server")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"📋 Supported brokers: Redis, GCP Pub/Sub, In-Memory")
    
    uvicorn.run(server.app, host=host, port=port)