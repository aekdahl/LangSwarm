# lex_handler.py

"""
Amazon Lex Integration for LangSwarm Agent

Setup Instructions:
-------------------
1. Go to AWS Console > Amazon Lex > Create a new bot.
2. Configure your bot with basic intents (you can keep defaults for now).
3. Set up a Lambda function in AWS Lambda:
   - Runtime: Python 3.9 or 3.11
   - Handler: `lex_handler.lambda_handler`
4. Add Lex as a trigger to your Lambda.
5. (Optional) Set up API Gateway to bridge Lex ↔️ external agent if needed.

IAM Permissions:
----------------
Ensure your Lambda function has permissions to:
- Log to CloudWatch
- (Optional) Call external services if your agent is hosted elsewhere

"""

# lex_adapter.py

"""
Amazon Lex Integration Adapter for LangSwarm

Usage:
    from lex_adapter import LexAdapter
    from my_langswarm_agent import agent

    handler = LexAdapter(agent).lambda_handler

    # In AWS Lambda, set handler to: lex_adapter.handler
"""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class LexAdapter:
    def __init__(self, agent):
        """
        Initialize with a LangSwarm-compatible agent.
        :param agent: An object with a `.chat(query: str) -> str` method.
        """
        self.agent = agent

    def lambda_handler(self, event, context):
        """
        AWS Lambda entry point for Amazon Lex.
        """
        logger.info("Lex Event Received: %s", json.dumps(event))

        try:
            user_input = event.get("inputTranscript", "")
            session_attributes = event.get("sessionAttributes", {})

            if not user_input:
                return self._lex_response("I'm sorry, I didn't catch that. Could you repeat?", session_attributes)

            response_text = self.agent.chat(user_input)
            return self._lex_response(response_text, session_attributes)

        except Exception as e:
            logger.exception("Exception while handling Lex event")
            return self._lex_response("Something went wrong. Please try again later.")

    def _lex_response(self, message: str, session_attributes=None):
        """
        Formats a Lex-compatible response.
        """
        return {
            "sessionAttributes": session_attributes or {},
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": message
                }
            }
        }

# Optional Lambda entry point (you can point your handler directly to this)
# from my_langswarm_agent import agent
# handler = LexAdapter(agent).lambda_handler
