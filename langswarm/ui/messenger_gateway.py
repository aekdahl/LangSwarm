
"""
🔧 Setup Instructions
1. Create a Facebook App and Page
Go to Facebook for Developers

Create a new App → Select “Business” type

Add Messenger as a product

Create a Facebook Page if you don’t already have one

2. Generate Tokens and Set Webhook
In Messenger > Settings:

Generate a Page Access Token

Set the webhook callback URL (pointing to your Flask app)

Subscribe to messages (messages, messaging_postbacks)

--

🌐 Exposing Locally (for Testing)
Use ngrok to expose your webhook URL:

bash
Copy
Edit
ngrok http 5000
Set your webhook URL in Meta Dashboard:

arduino
Copy
Edit
https://your-ngrok-url/webhook

"""

import os
import json
import requests
from flask import Flask, request
from langswarm.core.agent import LangSwarmAgent  # Replace with actual import

VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "secure_verify_token")
PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_TOKEN", "your_page_access_token")

app = Flask(__name__)

class MessengerGateway:
    def __init__(self, agent: LangSwarmAgent):
        self.agent = agent

    def send_message(self, recipient_id, text):
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text},
        }
        auth = {"access_token": PAGE_ACCESS_TOKEN}
        response = requests.post(
            "https://graph.facebook.com/v17.0/me/messages",
            params=auth,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
        )
        return response.json()

    def handle_event(self, data):
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if "message" in messaging_event:
                    user_input = messaging_event["message"].get("text", "")
                    response = self.agent.chat(user_input)
                    self.send_message(sender_id, response)

# Flask routes
messenger_gateway = None  # Will be assigned in main block

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Invalid verification token", 403
    else:
        data = request.get_json()
        messenger_gateway.handle_event(data)
        return "ok", 200

# For local testing
if __name__ == "__main__":
    from langswarm.examples import my_agent  # Load your LangSwarm agent instance
    messenger_gateway = MessengerGateway(agent=my_agent)
    app.run(port=5000)
