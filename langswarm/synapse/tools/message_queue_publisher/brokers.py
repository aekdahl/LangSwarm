import abc
import threading
import redis
import json
from google.cloud import pubsub_v1
import queue

class MessageBroker(abc.ABC):
    """
    Abstract base class for a message broker.
    Supports publishing and subscribing to messages.
    """

    @abc.abstractmethod
    def publish(self, channel: str, message: dict):
        """Publish a message to a specific channel."""
        pass

    @abc.abstractmethod
    def subscribe(self, channel: str, callback):
        """
        Subscribe to a channel and call the callback function 
        whenever a new message is received.
        """
        pass


class RedisMessageBroker(MessageBroker):
    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db)

    def publish(self, channel: str, message: dict):
        """Publish message to Redis channel."""
        self.client.publish(channel, json.dumps(message))

    def subscribe(self, channel: str, callback):
        """Subscribe to a Redis channel and process messages asynchronously."""
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)

        def listen():
            for message in pubsub.listen():
                if message["type"] == "message":
                    callback(json.loads(message["data"]))

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()


class GCPMessageBroker(MessageBroker):
    def __init__(self, project_id):
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_threads = {}

    def publish(self, channel: str, message: dict):
        """Publish a message to a GCP Pub/Sub topic."""
        topic_path = self.publisher.topic_path(self.project_id, channel)
        data = json.dumps(message).encode("utf-8")
        self.publisher.publish(topic_path, data=data)

    def subscribe(self, channel: str, callback):
        """Subscribe to a GCP Pub/Sub topic and process messages."""
        subscription_path = self.subscriber.subscription_path(self.project_id, channel)

        def callback_wrapper(message):
            callback(json.loads(message.data))
            message.ack()  # Acknowledge message receipt

        self.subscription_threads[channel] = threading.Thread(
            target=self.subscriber.subscribe,
            args=(subscription_path, callback_wrapper),
            daemon=True
        )
        self.subscription_threads[channel].start()


class InternalQueueBroker(MessageBroker):
    def __init__(self):
        self.queues = {}
        self.sync_response_buffer = {}

    def publish(self, channel: str, message: dict):
        if channel not in self.queues:
            self.queues[channel] = queue.Queue()
        self.queues[channel].put(message)

    def subscribe(self, channel: str, callback):
        if channel not in self.queues:
            self.queues[channel] = queue.Queue()

        def listen():
            while True:
                message = self.queues[channel].get()
                callback(message)

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    # ✅ This is the important addition:
    def return_to_user(self, message: str, context=None):
        request_id = (context or {}).get("request_id", "default")
        self.sync_response_buffer[request_id] = message

    def get_response_for_request(self, request_id: str):
        return self.sync_response_buffer.pop(request_id, None)

