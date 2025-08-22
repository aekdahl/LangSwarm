#!/usr/bin/env python3
"""
Message Queue Publisher MCP Tool
================================

An MCP-compatible tool for publishing messages to various message brokers.
Supports Redis, Google Cloud Pub/Sub, and in-memory queues for asynchronous
communication between agents and external systems.
"""

import os
import json
import threading
import queue
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel

# LangSwarm imports
from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.synapse.tools.base import BaseTool

# === Message Broker Implementations ===

class MessageBroker:
    """Abstract base class for message brokers"""
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a specific channel"""
        raise NotImplementedError
    
    def subscribe(self, channel: str, callback) -> None:
        """Subscribe to a channel with callback"""
        raise NotImplementedError

class InMemoryBroker(MessageBroker):
    """In-memory message broker for development and testing"""
    
    def __init__(self):
        self.queues = {}
        self.subscribers = {}
        
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish message to in-memory queue"""
        try:
            if channel not in self.queues:
                self.queues[channel] = queue.Queue()
            
            # Add timestamp and metadata
            enriched_message = {
                **message,
                "_timestamp": datetime.utcnow().isoformat(),
                "_channel": channel,
                "_broker_type": "in_memory"
            }
            
            self.queues[channel].put(enriched_message)
            
            # Notify subscribers if any
            if channel in self.subscribers:
                for callback in self.subscribers[channel]:
                    try:
                        callback(enriched_message)
                    except Exception as e:
                        print(f"Warning: Subscriber callback failed: {e}")
            
            return True
        except Exception as e:
            print(f"Error publishing to in-memory queue: {e}")
            return False
    
    def subscribe(self, channel: str, callback) -> None:
        """Subscribe to a channel"""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)
    
    def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about queue sizes"""
        return {channel: q.qsize() for channel, q in self.queues.items()}

class RedisBroker(MessageBroker):
    """Redis message broker for production use"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, 
                 password: Optional[str] = None):
        try:
            import redis
            self.client = redis.StrictRedis(
                host=host, port=port, db=db, password=password,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            self.available = True
        except Exception as e:
            print(f"Warning: Redis not available: {e}")
            self.client = None
            self.available = False
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish message to Redis channel"""
        if not self.available:
            return False
        
        try:
            enriched_message = {
                **message,
                "_timestamp": datetime.utcnow().isoformat(),
                "_channel": channel,
                "_broker_type": "redis"
            }
            
            self.client.publish(channel, json.dumps(enriched_message))
            return True
        except Exception as e:
            print(f"Error publishing to Redis: {e}")
            return False
    
    def subscribe(self, channel: str, callback) -> None:
        """Subscribe to Redis channel"""
        if not self.available:
            return
            
        def listen():
            pubsub = self.client.pubsub()
            pubsub.subscribe(channel)
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        callback(data)
                    except Exception as e:
                        print(f"Error processing Redis message: {e}")
        
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

class GCPPubSubBroker(MessageBroker):
    """Google Cloud Pub/Sub message broker"""
    
    def __init__(self, project_id: str):
        try:
            from google.cloud import pubsub_v1
            self.project_id = project_id
            self.publisher = pubsub_v1.PublisherClient()
            self.subscriber = pubsub_v1.SubscriberClient()
            self.available = True
        except Exception as e:
            print(f"Warning: GCP Pub/Sub not available: {e}")
            self.available = False
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish message to GCP Pub/Sub topic"""
        if not self.available:
            return False
        
        try:
            topic_path = self.publisher.topic_path(self.project_id, channel)
            
            enriched_message = {
                **message,
                "_timestamp": datetime.utcnow().isoformat(),
                "_channel": channel,
                "_broker_type": "gcp_pubsub"
            }
            
            data = json.dumps(enriched_message).encode("utf-8")
            self.publisher.publish(topic_path, data=data)
            return True
        except Exception as e:
            print(f"Error publishing to GCP Pub/Sub: {e}")
            return False
    
    def subscribe(self, channel: str, callback) -> None:
        """Subscribe to GCP Pub/Sub topic"""
        if not self.available:
            return
        
        subscription_path = self.subscriber.subscription_path(self.project_id, channel)
        
        def callback_wrapper(message):
            try:
                data = json.loads(message.data)
                callback(data)
                message.ack()
            except Exception as e:
                print(f"Error processing GCP Pub/Sub message: {e}")
                message.nack()
        
        thread = threading.Thread(
            target=self.subscriber.subscribe,
            args=(subscription_path, callback_wrapper),
            daemon=True
        )
        thread.start()

# === Pydantic Schemas ===

class PublishMessageInput(BaseModel):
    channel: str
    message: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class PublishMessageOutput(BaseModel):
    success: bool
    channel: str
    message_id: Optional[str] = None
    timestamp: str
    broker_type: str
    error: Optional[str] = None

class ListChannelsOutput(BaseModel):
    channels: List[str]
    broker_type: str
    total_count: int

class GetBrokerStatsOutput(BaseModel):
    broker_type: str
    available: bool
    stats: Dict[str, Any]

class ListChannelsInput(BaseModel):
    pass  # No parameters needed

class GetBrokerStatsInput(BaseModel):
    pass  # No parameters needed

# === Message Queue Storage ===

class MessageQueueManager:
    """Manages message brokers and routing"""
    
    def __init__(self):
        self.brokers = {}
        self.default_broker = self._create_default_broker()
        
    def _create_default_broker(self) -> MessageBroker:
        """Create default broker based on environment"""
        # Try Redis first
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                # Parse Redis URL
                import urllib.parse
                parsed = urllib.parse.urlparse(redis_url)
                broker = RedisBroker(
                    host=parsed.hostname or "localhost",
                    port=parsed.port or 6379,
                    password=parsed.password
                )
                if broker.available:
                    return broker
            except Exception:
                pass
        
        # Try GCP Pub/Sub
        gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if gcp_project:
            try:
                broker = GCPPubSubBroker(gcp_project)
                if broker.available:
                    return broker
            except Exception:
                pass
        
        # Fallback to in-memory
        return InMemoryBroker()
    
    def get_broker(self, broker_id: Optional[str] = None) -> MessageBroker:
        """Get broker by ID or return default"""
        if broker_id and broker_id in self.brokers:
            return self.brokers[broker_id]
        return self.default_broker
    
    def add_broker(self, broker_id: str, broker: MessageBroker):
        """Add a custom broker"""
        self.brokers[broker_id] = broker
    
    def publish_message(self, channel: str, message: Dict[str, Any], 
                       broker_id: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Publish message with metadata"""
        broker = self.get_broker(broker_id)
        
        # Enrich message with metadata
        enriched_message = {**message}
        if metadata:
            enriched_message["_metadata"] = metadata
        
        success = broker.publish(channel, enriched_message)
        
        return {
            "success": success,
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat(),
            "broker_type": type(broker).__name__,
            "message_id": f"msg_{datetime.utcnow().timestamp()}",
            "error": None if success else "Failed to publish message"
        }

# Global message queue manager
message_manager = MessageQueueManager()

# === MCP Tool Methods ===

def publish_message(channel: str, message: Dict[str, Any], 
                   broker_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None):
    """Publish a message to the specified channel"""
    result = message_manager.publish_message(channel, message, broker_id, metadata)
    
    if result["success"]:
        return PublishMessageOutput(**result)
    else:
        return PublishMessageOutput(
            success=False,
            channel=channel,
            timestamp=result["timestamp"],
            broker_type=result["broker_type"],
            error=result.get("error", "Unknown error")
        )

def list_channels():
    """List available channels (for in-memory broker)"""
    broker = message_manager.get_broker()
    
    if isinstance(broker, InMemoryBroker):
        channels = list(broker.queues.keys())
        return ListChannelsOutput(
            channels=channels,
            broker_type="InMemoryBroker",
            total_count=len(channels)
        )
    else:
        return ListChannelsOutput(
            channels=[],
            broker_type=type(broker).__name__,
            total_count=0
        )

def get_broker_stats():
    """Get statistics about the message broker"""
    broker = message_manager.get_broker()
    
    stats = {
        "available": True,
        "type": type(broker).__name__
    }
    
    if isinstance(broker, InMemoryBroker):
        stats["queue_stats"] = broker.get_queue_stats()
    elif isinstance(broker, RedisBroker):
        stats["available"] = broker.available
    elif isinstance(broker, GCPPubSubBroker):
        stats["available"] = broker.available
        stats["project_id"] = getattr(broker, 'project_id', None)
    
    return GetBrokerStatsOutput(
        broker_type=type(broker).__name__,
        available=stats["available"],
        stats=stats
    )

# === MCP Server Setup ===

server = BaseMCPToolServer(
    name="message_queue_publisher",
    description="Message queue publisher for asynchronous communication between agents and external systems",
    local_mode=True
)

# Register MCP tasks
server.add_task(
    name="publish_message",
    description="Publish a message to a specific channel/queue",
    input_model=PublishMessageInput,
    output_model=PublishMessageOutput,
    handler=lambda channel, message, metadata=None: publish_message(channel, message, metadata)
)

server.add_task(
    name="list_channels", 
    description="List available channels/queues",
    input_model=ListChannelsInput,
    output_model=ListChannelsOutput,
    handler=lambda: list_channels()
)

server.add_task(
    name="get_broker_stats",
    description="Get statistics about the message broker",
    input_model=GetBrokerStatsInput,
    output_model=GetBrokerStatsOutput,
    handler=lambda: get_broker_stats()
)

# Build app (None if local_mode=True)
app = server.build_app()

# === LangChain-Compatible Tool Class ===

class MessageQueuePublisherMCPTool(BaseTool):
    """
    Message Queue Publisher MCP tool for publishing messages to various message brokers.
    
    Supports Redis, Google Cloud Pub/Sub, and in-memory queues for asynchronous
    communication between agents, event dispatching, and integration with external systems.
    
    Features:
    - Auto-detection of available message brokers (Redis, GCP Pub/Sub, in-memory)
    - Message enrichment with timestamps and metadata
    - Error handling and fallback mechanisms
    - Support for multiple broker types simultaneously
    """
    _bypass_pydantic = True  # Bypass Pydantic validation
    
    def __init__(self, identifier: str, name: str = None, local_mode: bool = True, mcp_url: str = None, 
                 broker_id: Optional[str] = None, **kwargs):
        # Set defaults for message queue publisher MCP tool
        description = kwargs.pop('description', "Message queue publisher for asynchronous communication and event dispatching")
        instruction = kwargs.pop('instruction', "Use this tool to publish messages to queues with publish_message, list_channels, and get_broker_stats operations")
        brief = kwargs.pop('brief', "Message Queue Publisher MCP tool")
        
        # Add MCP server reference
        kwargs['mcp_server'] = server
        
        # Set MCP tool attributes to bypass Pydantic validation issues
        object.__setattr__(self, '_is_mcp_tool', True)
        object.__setattr__(self, 'local_mode', local_mode)
        object.__setattr__(self, 'broker_id', broker_id)
        
        # Initialize with BaseTool (handles all MCP setup automatically)
        super().__init__(
            name=name or "MessageQueuePublisherMCPTool",
            description=description,
            instruction=instruction,
            identifier=identifier,
            brief=brief,
            **kwargs
        )
    
    def run(self, input_data=None):
        """Execute message queue publisher MCP methods locally"""
        # Define method handlers for this tool
        method_handlers = {
            "publish_message": publish_message,
            "list_channels": list_channels,
            "get_broker_stats": get_broker_stats,
        }
        
        # Use BaseTool's common MCP input handler
        try:
            return self._handle_mcp_structured_input(input_data, method_handlers)
        except Exception as e:
            return f"Error: {str(e)}. Available methods: {list(method_handlers.keys())}"

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        print(f"Default broker: {type(message_manager.default_broker).__name__}")
        # In local mode, server is ready to use - no uvicorn needed
    else:
        # Only run uvicorn server if not in local mode
        import uvicorn
        uvicorn.run("mcp.tools.message_queue_publisher.main:app", host="0.0.0.0", port=4022, reload=True)