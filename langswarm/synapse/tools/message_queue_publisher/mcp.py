from .base import MessageBroker

class MCP:
    def __init__(self, broker: MessageBroker):
        self.broker = broker

    def send(self, channel: str, payload: dict):
        self.broker.publish(channel, payload)

    def on(self, channel: str, handler):
        self.broker.subscribe(channel, handler)
