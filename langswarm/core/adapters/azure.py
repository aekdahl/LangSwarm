from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity


class AzureBotAdapter(ActivityHandler):
    def __init__(self, agent_wrapper):
        """
        Adapter for Azure Bot Framework to integrate with your AgentWrapper.

        :param agent_wrapper: An instance of your LLM or AgentWrapper class.
        """
        super().__init__()
        self.agent = agent_wrapper

    async def on_message_activity(self, turn_context: TurnContext):
        user_input = turn_context.activity.text.strip()

        # Run the LLM agent
        try:
            response = self.agent.chat(user_input)
            if isinstance(response, tuple):
                _, response = response
        except Exception as e:
            response = f"An error occurred while processing your message: {str(e)}"

        await turn_context.send_activity(response)


# --- Web server setup (aiohttp) ---

from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity

# Replace these with your real credentials from Azure Bot registration
APP_ID = "YOUR_MICROSOFT_APP_ID"
APP_PASSWORD = "YOUR_MICROSOFT_APP_PASSWORD"

adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)

# Hook up your LLM-powered agent
from your_project.agent_wrapper import AgentWrapper  # replace with actual import
agent_instance = AgentWrapper(...)
bot = AzureBotAdapter(agent_instance)

async def handle_messages(request: web.Request):
    body = await request.json()
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")
    response = await adapter.process_activity(activity, auth_header, bot.on_turn)
    return web.Response(status=response.status if response else 200)

app = web.Application()
app.router.add_post("/api/messages", handle_messages)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=3978)
