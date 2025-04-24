# langswarm/messaging/shims.py
from typing import Dict, Callable
from ..agents.base import BaseAgent
from .base import MessageBroker

class MCPShim:
    """
    Base class for bridging message brokers with LangSwarm agents.
    """
    def __init__(self, agent: BaseAgent, broker: MessageBroker):
        self.agent = agent
        self.broker = broker

    def start(self):
        """Start listening to the agent's incoming queue."""
        channel = f"{self.agent.identifier}_incoming"
        print(f"[MCPShim] Subscribing to {channel}")
        self.broker.subscribe(channel, self.route_message)

    def route_message(self, message: Dict):
        """
        Handle incoming message and invoke the agent.
        You can customize how the payload is parsed here.
        """
        print(f"[MCPShim] Received message for {self.agent.identifier}: {message}")
        input_text = message.get("text", "")
        response = self.agent.chat(input_text)

        # Optionally respond via the broker
        reply_channel = message.get("reply_channel")
        if reply_channel:
            self.broker.publish(reply_channel, {
                "from": self.agent.identifier,
                "response": response
            })


# Example usage
if __name__ == "__main__":
    from ..brokers import RedisMessageBroker
    from ..agents.mock import MockAgent  # Replace with actual implementation

    agent = MockAgent(identifier="example_agent")
    broker = RedisMessageBroker()
    shim = MCPShim(agent, broker)
    shim.start()
