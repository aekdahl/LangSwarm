# langswarm/messaging/loader.py

from .brokers import RedisMessageBroker, GCPMessageBroker, InternalQueueBroker
from .queues import RedisMessageQueue, GCPPubSubMessageQueue, InternalMessageQueue

def load_brokers_from_config(config: dict):
    brokers = {}
    for broker_id, info in config.get("brokers", {}).items():
        btype = info["type"]
        cfg = info.get("config", {})

        if btype == "redis":
            brokers[broker_id] = RedisMessageBroker(**cfg)
        elif btype == "gcp":
            brokers[broker_id] = GCPMessageBroker(**cfg)
        elif btype == "internal":
            brokers[broker_id] = InternalQueueBroker()
        else:
            print(f"⚠️ Unknown broker type: {btype}")
    
    return brokers


def load_async_queues_from_config(config: dict):
    queues = {}
    for queue_id, info in config.get("queues", {}).items():
        qtype = info["type"]
        cfg = info.get("config", {})

        if qtype == "redis":
            queues[queue_id] = RedisMessageQueue(**cfg)
        elif qtype == "gcp":
            queues[queue_id] = GCPPubSubMessageQueue(**cfg)
        elif qtype == "internal":
            queues[queue_id] = InternalMessageQueue()
        else:
            print(f"⚠️ Unknown async queue type: {qtype}")
    
    return queues
