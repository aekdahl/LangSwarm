# twilio_gateway.py

"""
# run_twilio_gateway.py

from your_langswarm_agent import agent_instance  # Replace with your agent
from twilio_gateway import TwilioAgentGateway

gateway = TwilioAgentGateway(agent=agent_instance)
gateway.run()

---

Setup on Twilio Console
Get a Twilio Number:

Go to Twilio Console → Buy a number with SMS / WhatsApp / Voice.

Set Your Webhook:

Under “Messaging” > “A message comes in”, paste your public endpoint (e.g., via ngrok):

arduino
Copy
Edit
https://your-ngrok-url.ngrok.io/twilio-webhook
Test It:

Send an SMS or WhatsApp message to your Twilio number.

Your LangSwarm agent should reply instantly.

✅ Optional Voice Support
To support voice calls, you can adapt the same webhook and return spoken TwiML instead.

"""
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse


class TwilioAgentGateway:
    """
    Flask-based webhook gateway for Twilio SMS and WhatsApp.
    """
    def __init__(self, agent):
        self.agent = agent

    def create_app(self):
        app = Flask(__name__)

        @app.route("/twilio-webhook", methods=["POST"])
        def handle_twilio_message():
            incoming_msg = request.form.get("Body", "")
            print(f"Received from Twilio: {incoming_msg}")

            agent_response = self.agent.chat(incoming_msg)

            twilio_response = MessagingResponse()
            twilio_response.message(agent_response)

            return Response(str(twilio_response), mimetype="application/xml")

        return app

    def run(self, host="0.0.0.0", port=5000):
        app = self.create_app()
        app.run(host=host, port=port)
