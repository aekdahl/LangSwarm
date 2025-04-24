import abc
import threading
import redis
import json
from google.cloud import pubsub_v1
import queue

from abc import ABC, abstractmethod
from typing import Any, Dict, Callable

class BaseMessageQueue(ABC):
    """
    Abstract base class for message brokers.
    Defines the contract for all message brokers (internal, Redis, GCP Pub/Sub, etc.).
    """

    @abstractmethod
    async def publish(self, message: Dict[str, Any]):
        """Publish a message to the queue."""
        pass

    @abstractmethod
    async def consume(self) -> Dict[str, Any]:
        """Retrieve a message from the queue."""
        pass

    @abstractmethod
    async def listen(self, callback: Callable[[Dict[str, Any]], None]):
        """Listen for messages and process them using the given callback."""
        pass


import asyncio
from typing import Any, Dict, Callable

class InternalMessageQueue(BaseMessageQueue):
    """
    An internal async message queue for agent communication.
    Uses asyncio.Queue for non-blocking message passing.
    """

    def __init__(self):
        self.queue = asyncio.Queue()

    async def publish(self, message: Dict[str, Any]):
        """
        Publishes a message to the queue.
        :param message: A dictionary containing the message details.
        """
        await self.queue.put(message)

    async def consume(self) -> Dict[str, Any]:
        """
        Retrieves a message from the queue asynchronously.
        :return: A message dictionary if available.
        """
        return await self.queue.get()

    async def listen(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Listens for incoming messages and processes them with a callback function.
        Runs indefinitely in an async loop.
        :param callback: A function to process each message.
        """
        while True:
            message = await self.consume()
            await callback(message)


import aioredis
import json
from typing import Any, Dict, Callable

class RedisMessageQueue(BaseMessageBroker):
    """
    Redis-based message queue for multi-agent communication.
    Supports persistent messages and cross-process messaging.
    """

    def __init__(self, redis_url="redis://localhost:6379", channel="agent_queue"):
        self.redis_url = redis_url
        self.channel = channel
        self.redis = None

    async def connect(self):
        """ Connect to Redis asynchronously. """
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)

    async def publish(self, message: Dict[str, Any]):
        """ Publish message to Redis queue. """
        await self.redis.lpush(self.channel, json.dumps(message))

    async def consume(self) -> Dict[str, Any]:
        """ Retrieve message from Redis queue. """
        _, message = await self.redis.brpop(self.channel)
        return json.loads(message)

    async def listen(self, callback: Callable[[Dict[str, Any]], None]):
        """ Continuously listen for messages. """
        while True:
            message = await self.consume()
            await callback(message)

    async def close(self):
        """ Close Redis connection. """
        if self.redis:
            await self.redis.close()


from google.cloud import pubsub_v1
import json
import asyncio

class GCPPubSubMessageQueue(BaseMessageBroker):
    """
    Google Cloud Pub/Sub-based message broker.
    Supports event-driven triggers and global scalability.
    """

    def __init__(self, project_id: str, topic_id: str, subscription_id: str):
        self.project_id = project_id
        self.topic_id = topic_id
        self.subscription_id = subscription_id
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()

    async def publish(self, message: Dict[str, Any]):
        """ Publish message to GCP Pub/Sub topic. """
        topic_path = self.publisher.topic_path(self.project_id, self.topic_id)
        data = json.dumps(message).encode("utf-8")
        self.publisher.publish(topic_path, data)

    async def consume(self) -> Dict[str, Any]:
        """ Retrieve message from GCP Pub/Sub subscription. """
        subscription_path = self.subscriber.subscription_path(self.project_id, self.subscription_id)

        future = self.subscriber.subscribe(subscription_path, self._callback)
        await asyncio.sleep(1)  # Allow time to receive messages
        return future.result()

    async def listen(self, callback: Callable[[Dict[str, Any]], None]):
        """ Continuously listen for messages. """
        while True:
            message = await self.consume()
            await callback(message)

    def _callback(self, message):
        """ Internal callback for Pub/Sub messages. """
        print(f"Received message: {message.data}")
        message.ack()
