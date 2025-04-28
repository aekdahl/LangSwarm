# slack_gateway.py

"""
# run_slack_gateway.py

from your_langswarm_agent import agent_instance  # Replace with your agent
from slack_gateway import SlackAgentGateway
import os

gateway = SlackAgentGateway(
    agent=agent_instance,
    slack_bot_token=os.getenv("SLACK_BOT_TOKEN"),
    slack_signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

gateway.run()


---


📦 Dependencies
Install the official Slack SDK:

bash
Copy
Edit
pip install slack_bolt slack_sdk
🔐 Slack App Setup
Go to: https://api.slack.com/apps → Create New App

From Scratch → Name your app + pick a workspace

Under OAuth & Permissions, add the following Bot Token Scopes:

app_mentions:read

chat:write

channels:history

im:history

groups:history

Install the app to your workspace and copy the Bot User OAuth Token

Under Event Subscriptions:

Enable Events

Set your public URL (https://your-ngrok-url/slack/events)

Subscribe to app_mention and/or message.im events

--

🌐 Local Development
Use ngrok to expose your Flask server:

bash
Copy
Edit
ngrok http 3000
Paste the URL (e.g., https://your-ngrok-url.ngrok.io/slack/events) in Slack's Event Subscriptions config.
"""

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import os


class SlackAgentGateway:
    def __init__(self, agent, slack_bot_token, slack_signing_secret):
        self.agent = agent
        self.slack_app = App(token=slack_bot_token, signing_secret=slack_signing_secret)
        self.handler = SlackRequestHandler(self.slack_app)
        self._register_events()

    def _register_events(self):
        @self.slack_app.event("app_mention")
        def handle_app_mention(event, say):
            user_input = event["text"]
            print(f"Slack mention: {user_input}")
            response = self.agent.chat(user_input)
            say(response)

        @self.slack_app.event("message")
        def handle_dm(event, say):
            if event.get("channel_type") == "im":  # Only reply to direct messages
                user_input = event["text"]
                print(f"Slack DM: {user_input}")
                response = self.agent.chat(user_input)
                say(response)

    def create_flask_app(self):
        flask_app = Flask(__name__)

        @flask_app.route("/slack/events", methods=["POST"])
        def slack_events():
            return self.handler.handle(request)

        return flask_app

    def run(self, host="0.0.0.0", port=3000):
        app = self.create_flask_app()
        app.run(host=host, port=port)
