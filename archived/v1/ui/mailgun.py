# --- MailgunEmailWebhookAdapter.py ---
from aiohttp import web

class MailgunEmailWebhookAdapter:
    def __init__(self, agent_wrapper):
        """
        Adapter for handling inbound emails via Mailgun Routes.

        :param agent_wrapper: An instance of your LLM or AgentWrapper class.
        """
        self.agent = agent_wrapper

    async def handle_mailgun_email(self, request: web.Request):
        data = await request.post()

        sender = data.get('sender') or data.get('from')
        subject = data.get('subject')
        email_body = data.get('body-plain') or data.get('stripped-text') or ''

        user_input = f"Email from {sender}\nSubject: {subject}\n\n{email_body}".strip()

        try:
            response = self.agent.chat(user_input)
            if isinstance(response, tuple):
                _, response = response
        except Exception as e:
            response = f"An error occurred: {str(e)}"

        print(f"Processed Mailgun email response: {response}")

        return web.Response(text="OK", status=200)

# --- Web server setup (aiohttp) ---
from your_project.agent_wrapper import AgentWrapper

agent_instance = AgentWrapper(...)
bot = MailgunEmailWebhookAdapter(agent_instance)

app = web.Application()
app.router.add_post("/mailgun-email", bot.handle_mailgun_email)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8083)
