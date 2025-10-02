# --- GoogleChatAdapter.py ---
from aiohttp import web
import json

class GoogleChatAdapter:
    def __init__(self, agent_wrapper):
        """
        Adapter for Google Chat Webhook to integrate with your AgentWrapper.

        :param agent_wrapper: An instance of your LLM or AgentWrapper class.
        """
        self.agent = agent_wrapper

    async def handle_message(self, request: web.Request):
        body = await request.json()
        user_input = body.get('message', {}).get('text', '').strip()

        if not user_input:
            return web.Response(status=200)

        try:
            response = self.agent.chat(user_input)
            if isinstance(response, tuple):
                _, response = response
        except Exception as e:
            response = f"An error occurred: {str(e)}"

        reply = {
            "text": response
        }

        return web.json_response(reply)

# --- Web server setup (aiohttp) ---
# Replace with your own import
from your_project.agent_wrapper import AgentWrapper

agent_instance = AgentWrapper(...)
bot = GoogleChatAdapter(agent_instance)

app = web.Application()
app.router.add_post("/googlechat", bot.handle_message)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
