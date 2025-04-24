
import inspect
from typing import Type, Optional, List, Dict, Any

from ..base import BaseTool
from .config import ToolSettings

class MessageQueuePublisher(BaseTool):
    """
    A tool that allows agents to send messages to a queue when explicitly called.
    
    This tool integrates with different message brokers (e.g., Redis, GCP Pub/Sub),
    but is only executed when the agent decides to use it.
    """

    def __init__(
        self, 
        identifier, 
        broker: Optional[MessageBroker] = None
    ):
        super().__init__(
            name="MessageQueuePublisher",
            description="""Use the MessageQueuePublisher tool to send messages to a queue. It is useful for enabling asynchronous communication between agents, triggering events, dispatching tasks, or integrating with external systems through message queues.""",
            instruction=ToolSettings.instructions
        )
        
        self.identifier = identifier
        self.brief = (
            f"Use the {identifier} tool to send messages to a queue.. "
            f"Use the help action to get instructions."
        )
        self.broker = broker  # Can be None if no message broker is in use

    def run(self, method="send_message", params={}):
        """
        Execute the tool's actions.
        :param payload: str or dict - The input query or tool details.
        :param action: str - The action to perform.
        :return: str or List[str] - The result of the action.
        """
        
        # Map actions to corresponding functions
        action_map = {
            "help": self._help,
            "send_message": self.send_message
        }

        # Execute the corresponding action
        if action in action_map: 
            params["output"] = self._safe_call(action_map[method], **params)
            return params
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )
        
    def send_message(self, channel: str, message: Dict[str, Any]):
        """
        Sends a message to the specified channel.

        :param channel: The name of the queue or channel to publish to.
        :param message: A dictionary containing message data.
        :return: Confirmation message or error.
        """
        if not self.broker:
            return "[ERROR] No message broker configured. Message not sent."

        try:
            self.broker.publish(channel, message)
            return f"[INFO] Message successfully sent to {channel}."
        except Exception as e:
            return f"[ERROR] Failed to send message: {str(e)}"
    
    def _help(self):
        return self.instruction
