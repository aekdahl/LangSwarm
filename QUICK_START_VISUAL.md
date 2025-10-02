# 🚀 LangSwarm Quick Start - Visual Guide

## 🎯 Goal: Working AI Chatbot in 2 Minutes

```mermaid
graph LR
    A[Install] --> B[Set API Key] --> C[Write Code] --> D[Run] --> E[Chat!]
    
    style A fill:#e1f5fe
    style B fill:#fff9c4
    style C fill:#c8e6c9
    style D fill:#ffccbc
    style E fill:#f8bbd0
```

---

## 1️⃣ **Install** (30 seconds)

```bash
pip install langswarm openai
```

✅ **Check:** No errors = Success!

---

## 2️⃣ **Set API Key** (30 seconds)

```bash
export OPENAI_API_KEY='sk-...'
```

🔑 **Get key:** https://platform.openai.com/api-keys

---

## 3️⃣ **Write Code** (30 seconds)

**`chatbot.py`:**
```python
import asyncio
from langswarm import create_agent

async def main():
    # Create chatbot with memory
    bot = create_agent(model="gpt-3.5-turbo", memory=True)
    
    # Chat loop
    print("Bot: Hello! Type 'quit' to exit.")
    while True:
        user = input("\nYou: ")
        if user.lower() == 'quit':
            break
        response = await bot.chat(user)
        print(f"\nBot: {response}")

asyncio.run(main())
```

---

## 4️⃣ **Run** (10 seconds)

```bash
python chatbot.py
```

---

## 5️⃣ **Chat!** ✨

```
Bot: Hello! Type 'quit' to exit.

You: Hi! My name is Alice
Bot: Hello Alice! It's nice to meet you. How can I help you today?

You: What's my name?
Bot: Your name is Alice. How can I assist you?

You: quit
```

---

## 🎉 **Success! You Built an AI Chatbot!**

### **What You Just Did:**
- ✅ Installed LangSwarm
- ✅ Created an AI agent
- ✅ Added conversation memory
- ✅ Built an interactive chatbot

### **Total Time: 2 minutes**
### **Lines of Code: 15**

---

## 🚀 **Level Up Your Bot** (Optional)

### **Make It Smarter**
```python
bot = create_agent(model="gpt-4")  # Better but $$
```

### **Give It Personality**
```python
bot = create_agent(
    model="gpt-3.5-turbo",
    system_prompt="You are a friendly pirate. Say 'Ahoy!'"
)
```

### **Stream Responses**
```python
async for chunk in bot.chat_stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

### **Track Costs**
```python
bot = create_agent(track_costs=True)
# Later...
print(f"Cost: ${bot.get_usage_stats()['estimated_cost']}")
```

---

## 🔧 **Common Issues**

| Problem | Solution |
|---------|----------|
| **"No API key"** | `export OPENAI_API_KEY='sk-...'` |
| **"Module not found"** | `pip install langswarm openai` |
| **"Rate limit"** | Use `gpt-3.5-turbo` or wait |
| **"Too long"** | Start new conversation |

---

## 📚 **What's Next?**

**Now that you have the basics:**

1. **Explore Examples**
   - `examples/simple/01_basic_chat.py`
   - `examples/simple/03_two_agents.py`
   - `examples/simple/05_with_tools.py`

2. **Try Templates**
   - `templates/chatbot.yaml`
   - `templates/customer-support.yaml`
   - `templates/code-assistant.yaml`

3. **Read Full Docs**
   - [Configuration Guide](docs/SIMPLIFIED_CONFIGURATION_STRATEGY.md)
   - [API Reference](docs/api-reference/)
   - [Advanced Features](docs/features/)

---

## 💡 **Remember**

**The 80% use case is just:**
```python
from langswarm import create_agent
bot = create_agent(model="gpt-3.5-turbo", memory=True)
response = await bot.chat("Hello!")
```

**Everything else is optional!**