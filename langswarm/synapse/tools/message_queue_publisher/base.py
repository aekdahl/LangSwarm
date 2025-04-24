# langswarm/messaging/base.py

import abc
from typing import Callable, Dict, Any, Optional


class MessageBroker(abc.ABC):
    """Synchronous message broker interface for publish/subscribe style."""

    @abc.abstractmethod
    def publish(self, channel: str, message: Dict[str, Any]):
        """Publish a message to a specific channel."""
        pass

    @abc.abstractmethod
    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to a channel and call callback when a message arrives."""
        pass


class AsyncMessageQueue(abc.ABC):
    """Asynchronous message queue interface for coroutine-based processing."""

    @abc.abstractmethod
    async def publish(self, message: Dict[str, Any]):
        """Publish a message to the async queue."""
        pass

    @abc.abstractmethod
    async def consume(self) -> Dict[str, Any]:
        """Consume and return a message from the queue."""
        pass

    @abc.abstractmethod
    async def listen(self, callback: Callable[[Dict[str, Any]], None]):
        """Start listening to messages and call the provided callback."""
        pass
