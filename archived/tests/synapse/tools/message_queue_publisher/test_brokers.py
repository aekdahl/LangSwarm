import json
import threading
import queue
from unittest.mock import MagicMock, patch

import pytest

from langswarm.synapse.tools.message_queue_publisher.brokers import (
    InternalQueueBroker, RedisMessageBroker, GCPMessageBroker
)


def test_internal_queue_broker_publish_and_subscribe():
    broker = InternalQueueBroker()
    received = []

    def callback(msg):
        received.append(msg)

    broker.subscribe("test", callback)
    broker.publish("test", {"hello": "world"})

    threading.Event().wait(0.1)  # Let the thread handle it
    assert received == [{"hello": "world"}]


@patch("langswarm.synapse.tools.message_queue_publisher.brokers.redis.StrictRedis")
def test_redis_message_broker_publish(mock_redis):
    mock_client = MagicMock()
    mock_redis.return_value = mock_client

    broker = RedisMessageBroker()
    broker.publish("test", {"foo": "bar"})

    mock_client.publish.assert_called_once_with("test", json.dumps({"foo": "bar"}))


@patch("langswarm.synapse.tools.message_queue_publisher.brokers.redis.StrictRedis")
def test_redis_message_broker_subscribe_starts_thread(mock_redis):
    mock_pubsub = MagicMock()
    mock_pubsub.listen.return_value = iter([
        {"type": "message", "data": json.dumps({"msg": "ping"})}
    ])
    mock_client = MagicMock()
    mock_client.pubsub.return_value = mock_pubsub
    mock_redis.return_value = mock_client

    broker = RedisMessageBroker()
    callback = MagicMock()
    broker.subscribe("chan", callback)

    threading.Event().wait(0.1)
    callback.assert_called_once_with({"msg": "ping"})


@patch("langswarm.synapse.tools.message_queue_publisher.brokers.pubsub_v1.PublisherClient")
@patch("langswarm.synapse.tools.message_queue_publisher.brokers.pubsub_v1.SubscriberClient")
def test_gcp_message_broker_publish(mock_subscriber, mock_publisher):
    mock_publisher_instance = MagicMock()
    mock_publisher.return_value = mock_publisher_instance

    broker = GCPMessageBroker("test-project")
    broker.publish("test-topic", {"x": 42})

    topic_path = mock_publisher_instance.topic_path.return_value
    mock_publisher_instance.publish.assert_called_once_with(
        topic_path,
        data=json.dumps({"x": 42}).encode("utf-8")
    )
