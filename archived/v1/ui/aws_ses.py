# --- SESEmailWebhookAdapter.py ---
from aiohttp import web
import json
import base64

class SESEmailWebhookAdapter:
    def __init__(self, agent_wrapper):
        """
        Adapter for handling AWS SES Inbound Email via SNS Notification.

        :param agent_wrapper: An instance of your LLM or AgentWrapper class.
        """
        self.agent = agent_wrapper

    async def handle_ses_email(self, request: web.Request):
        body = await request.json()

        # SNS sends a JSON body
        message = json.loads(body.get('Message', '{}'))
        mail_data = message.get('mail', {})
        content_data = message.get('content', '')

        sender = mail_data.get('source')
        subject = mail_data.get('commonHeaders', {}).get('subject')
        
        # The 'content' is usually base64 encoded raw email (optional)
        # We'll treat 'subject' and 'source' as the main input

        user_input = f"Email from {sender}\nSubject: {subject}\n\n(content omitted)".strip()

        try:
            response = self.agent.chat(user_input)
            if isinstance(response, tuple):
                _, response = response
        except Exception as e:
            response = f"An error occurred: {str(e)}"

        print(f"Processed SES email response: {response}")

        return web.Response(text="OK", status=200)

# --- Web server setup (aiohttp) ---
from your_project.agent_wrapper import AgentWrapper

agent_instance = AgentWrapper(...)
bot = SESEmailWebhookAdapter(agent_instance)

app = web.Application()
app.router.add_post("/ses-email", bot.handle_ses_email)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8082)
