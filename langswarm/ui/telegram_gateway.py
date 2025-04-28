"""
# run_telegram_gateway.py

from telegram_gateway import TelegramAgentGateway
from your_langswarm_agent import agent_instance  # Replace with your agent

import os

telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
bot = TelegramAgentGateway(agent=agent_instance, token=telegram_token)
bot.run()


---


📦 Dependencies
Install the official Telegram library:

bash
Copy
Edit
pip install python-telegram-bot==20.6
🔐 Telegram Setup
Open Telegram and search for @BotFather

Run /newbot and follow the steps to:

Name your bot

Get your bot token

Save the token and plug it into your environment or script

--

💡 Notes
You can expand the handler to filter specific commands or groups.

To deploy, you can run this bot anywhere Python is available, even on serverless platforms.
"""

# telegram_gateway.py

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

class TelegramAgentGateway:
    def __init__(self, agent, token: str):
        self.agent = agent
        self.token = token

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text
        print(f"[Telegram] Message from {update.effective_user.username}: {user_input}")
        response = self.agent.chat(user_input)
        await update.message.reply_text(response)

    def run(self):
        app = ApplicationBuilder().token(self.token).build()

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        print("[Telegram] Bot is polling...")
        app.run_polling()
