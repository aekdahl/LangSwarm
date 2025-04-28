"""
# run_discord_gateway.py

from your_langswarm_agent import agent_instance  # Replace with your agent
from discord_gateway import DiscordAgentGateway
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = DiscordAgentGateway(agent=agent_instance, intents=intents)
client.run(os.getenv("DISCORD_BOT_TOKEN"))


---


📦 Dependencies
Install the official Discord library:

bash
Copy
Edit
pip install discord.py
🔐 Discord Setup
Go to the Discord Developer Portal

Create a New Application

Go to Bot → Add Bot → Save Token

Under OAuth2 > URL Generator:

Scopes: bot

Bot Permissions: Send Messages, Read Message History

Use the generated URL to invite your bot to your server

--

💡 Notes
Discord requires "Message Content Intent" to be enabled in the Developer Portal under Bot > Privileged Gateway Intents.

This bot will respond to any message in a server it's part of. You can add prefix filters like !ask if needed.
"""

# discord_gateway.py

import discord

class DiscordAgentGateway(discord.Client):
    def __init__(self, agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = agent

    async def on_ready(self):
        print(f"[Discord] Logged in as {self.user} (ID: {self.user.id})")

    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.user:
            return

        user_input = message.content
        print(f"[Discord] Message from {message.author}: {user_input}")
        
        # Send the query to the agent
        response = self.agent.chat(user_input)

        # Reply back to user
        await message.channel.send(response)
