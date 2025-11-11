# LangSwarm Quick Start - One Page

## Install & Setup (1 minute)
```bash
pip install langswarm openai
export OPENAI_API_KEY='sk-...'  # Get from platform.openai.com
```

## Your First Chatbot (1 minute)

```python
# chatbot.py
import asyncio
from langswarm import create_agent

async def main():
    # Create AI chatbot
    bot = create_agent(model="gpt-3.5-turbo", memory=True)
    
    # Chat loop
    print("Bot: Hi! I'm ready to chat. Type 'quit' to exit.\n")
    while True:
        user = input("You: ")
        if user.lower() == 'quit':
            break
        response = await bot.chat(user)
        print(f"Bot: {response}\n")

asyncio.run(main())
```

## Run It
```bash
python chatbot.py
```

## That's It! 🎉

You now have a working AI chatbot that:
- ✅ Responds intelligently
- ✅ Remembers the conversation
- ✅ Works immediately

## Common Tweaks

**Smarter responses:** `model="gpt-4"`  
**Add personality:** `system_prompt="You are a pirate"`  
**Stream responses:** `bot.chat_stream("Hello")`  
**Track costs:** `bot = create_agent(track_costs=True)`

## Next Steps
- Try examples in `examples/simple/`
- Check templates in `templates/`
- Read full docs when needed

**Total time: 2 minutes to a working chatbot!**