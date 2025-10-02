# --- EmailWebhookAdapter.py ---
from aiohttp import web

class EmailWebhookAdapter:
    def __init__(self, agent_wrapper):
        """
        Adapter for handling inbound emails (e.g., via SendGrid Inbound Parse) to integrate with your AgentWrapper.

        :param agent_wrapper: An instance of your LLM or AgentWrapper class.
        """
        self.agent = agent_wrapper

    async def handle_email(self, request: web.Request):
        data = await request.post()

        # Common fields in SendGrid Parse (others like attachments can exist too)
        sender = data.get('from')
        subject = data.get('subject')
        email_body = data.get('text') or data.get('html') or ''

        user_input = f"Email from {sender}\nSubject: {subject}\n\n{email_body}".strip()

        try:
            response = self.agent.chat(user_input)
            if isinstance(response, tuple):
                _, response = response
        except Exception as e:
            response = f"An error occurred: {str(e)}"

        # Typically, we just log it or forward it elsewhere. No direct HTTP response needed.
        print(f"Processed email response: {response}")

        return web.Response(text="OK", status=200)


# --- SendGridEmailSender.py ---
import sendgrid
from sendgrid.helpers.mail import Mail

class SendGridEmailSender:
    def __init__(self, api_key, from_email):
        """
        :param api_key: Your SendGrid API Key
        :param from_email: Default From Email Address
        """
        self.sg = sendgrid.SendGridAPIClient(api_key)
        self.from_email = from_email

    def send_email(self, to_email: str, subject: str, body: str):
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )
        try:
            response = self.sg.send(message)
            print(f"Email sent! Status code: {response.status_code}")
        except Exception as e:
            print(f"Failed to send email: {str(e)}")


# --- Web server setup (aiohttp) ---
# Replace with your own import
from your_project.agent_wrapper import AgentWrapper

agent_instance = AgentWrapper(...)
bot = EmailWebhookAdapter(agent_instance)

app = web.Application()
app.router.add_post("/email", bot.handle_email)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8081)


sender = SendGridEmailSender(api_key="YOUR_KEY", from_email="noreply@yourdomain.com")
sender.send_email("user@example.com", "Subject", "Body text here")
