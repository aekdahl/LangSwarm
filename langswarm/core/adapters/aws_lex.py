# aws_lex.py

"""
Setup Instructions for AWS Lex
✅ Prerequisites:
AWS account

Python SDK: pip install boto3 flask

IAM Role with Lex permissions

🧭 Steps:
Create a Lex V1 Bot (you can use Lex V2 but this example assumes V1):

Configure a sample intent like FallbackIntent or ChatIntent.

In the fulfillment section, configure a Lambda Function or Webhook pointing to your Flask gateway.

Enable inputTranscript forwarding.

Run the Gateway:

python aws_lex_handler.py
Expose Public URL:

Use a tool like ngrok:

ngrok http 5000
Copy and paste the public URL in your Lex bot’s webhook configuration.
"""

import boto3
import json
from flask import Flask, request, jsonify

class AWSLexBotHandler:
    """
    A wrapper to handle AWS Lex interactions with a LangSwarm agent.
    """
    def __init__(self, agent, bot_name, bot_alias, region_name="us-east-1"):
        self.agent = agent
        self.bot_name = bot_name
        self.bot_alias = bot_alias
        self.lex_client = boto3.client("lex-runtime", region_name=region_name)

    def process_input(self, user_id: str, text: str) -> str:
        """
        Processes input from AWS Lex and returns response from LangSwarm agent.
        """
        # Forward to LangSwarm agent
        response = self.agent.chat(text)
        return response

    def run_flask_gateway(self, host="0.0.0.0", port=5000):
        """
        Run a Flask server to handle AWS Lex POST events.
        AWS Lex should be configured to hit /lex-webhook endpoint.
        """
        app = Flask(__name__)

        @app.route("/lex-webhook", methods=["POST"])
        def lex_webhook():
            event = request.get_json()
            user_id = event.get("userId")
            text = event.get("inputTranscript")

            response_text = self.process_input(user_id, text)

            return jsonify({
                "dialogAction": {
                    "type": "Close",
                    "fulfillmentState": "Fulfilled",
                    "message": {
                        "contentType": "PlainText",
                        "content": response_text
                    }
                }
            })

        app.run(host=host, port=port)
