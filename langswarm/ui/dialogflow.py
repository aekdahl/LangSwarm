# dialogflow_webhook_handler.py

"""
Setup Instructions for Google Dialogflow
✅ Prerequisites:
Google Cloud project with Dialogflow ES or CX enabled.

Install Python packages:

bash
Copy
Edit
pip install flask
🧭 Steps:
Create a Dialogflow Agent:

Use the Dialogflow console.

Go to Fulfillment > Enable Webhook and point it to your public URL (see ngrok below).

Run Your Flask Gateway:

bash
Copy
Edit
python dialogflow_webhook_handler.py
Expose It Publicly:

bash
Copy
Edit
ngrok http 5000
Copy the HTTPS URL from ngrok.

Paste it into the Fulfillment URL section in Dialogflow:

arduino
Copy
Edit
https://your-ngrok-url.ngrok.io/dialogflow-webhook
Enable Webhook Call in Intents:

In your intent settings, scroll down to the “Fulfillment” section and check "Enable webhook call for this intent".

🧪 Test
Try chatting with your Dialogflow agent. All input is forwarded to your LangSwarm agent for a response.
"""

from flask import Flask, request, jsonify

class DialogflowAgentHandler:
    """
    A webhook handler for Google Dialogflow that routes user input to a LangSwarm agent.
    """
    def __init__(self, agent):
        self.agent = agent

    def process_input(self, user_text: str) -> str:
        """
        Forward the input to the LangSwarm agent and return its response.
        """
        return self.agent.chat(user_text)

    def run_flask_gateway(self, host="0.0.0.0", port=5000):
        """
        Starts a Flask app that listens for Dialogflow webhook requests.
        """
        app = Flask(__name__)

        @app.route("/dialogflow-webhook", methods=["POST"])
        def webhook():
            payload = request.get_json()
            
            # Dialogflow ES format
            user_text = payload["queryResult"]["queryText"]
            fulfillment_text = self.process_input(user_text)

            return jsonify({
                "fulfillmentText": fulfillment_text
            })

        app.run(host=host, port=port)
