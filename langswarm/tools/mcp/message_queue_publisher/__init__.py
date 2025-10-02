"""
Message Queue Publisher MCP Tool
================================

An MCP-compatible tool for publishing messages to various message brokers including:
- Redis
- Google Cloud Pub/Sub  
- In-memory queues

Supports asynchronous communication between agents, event dispatching, 
and integration with external systems through message queues.
"""

from .main import MessageQueuePublisherMCPTool

__all__ = ["MessageQueuePublisherMCPTool"]