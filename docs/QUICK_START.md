# 🚀 LangSwarm Quick Start Guide

**Build your first AI agent in 2 minutes!**

This guide covers the 80% use case: creating a simple AI chatbot with OpenAI's GPT models.

## 📋 Prerequisites (30 seconds)

1. **Python 3.8+** installed
2. **OpenAI API key** ([Get one here](https://platform.openai.com/api-keys))

## 🏃 Quick Install (30 seconds)

```bash
# Install LangSwarm and OpenAI
pip install langswarm openai

# Set your API key
export OPENAI_API_KEY='your-api-key-here'
```

## 🤖 Your First Agent (1 minute)

### **1. Create `my_first_agent.py`:**

```python
import asyncio
from langswarm import create_agent

async def main():
    # Create an AI agent
    agent = create_agent(model="gpt-3.5-turbo")
    
    # Chat with it
    response = await agent.chat("Hello! What can you do?")
    print(f"AI: {response}")

asyncio.run(main())
```

### **2. Run it:**

```bash
python my_first_agent.py
```

**Output:**
```
AI: Hello! I can help you with a wide variety of tasks including answering questions, writing content, coding, analysis, and much more. How can I assist you today?
```

## 🎯 The 80% Use Case: Chatbot with Memory

Most users want a chatbot that remembers the conversation. Here's how:

### **`chatbot_with_memory.py`:**

```python
import asyncio
from langswarm import create_agent

async def main():
    # Create agent with memory
    agent = create_agent(
        model="gpt-3.5-turbo",
        memory=True,  # Remembers conversation
        system_prompt="You are a helpful assistant named Claude."
    )
    
    # Multi-turn conversation
    print("Chatbot: Hello! I'm Claude. How can I help you?")
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() == 'quit':
            break
            
        # Get AI response
        response = await agent.chat(user_input)
        print(f"\nChatbot: {response}")

asyncio.run(main())
```

### **Run it:**

```bash
python chatbot_with_memory.py
```

**Example conversation:**
```
Chatbot: Hello! I'm Claude. How can I help you?

You: My name is Alice
Chatbot: Nice to meet you, Alice! How can I assist you today?

You: What's my name?
Chatbot: Your name is Alice. Is there anything specific I can help you with?
```

## ⚡ Common Enhancements (30 seconds each)

### **1. Use GPT-4 for Better Quality**
```python
agent = create_agent(
    model="gpt-4",  # More capable but slower/expensive
    memory=True
)
```

### **2. Stream Responses (Like ChatGPT)**
```python
# Stream response as it's generated
async for chunk in agent.chat_stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

### **3. Add Custom Personality**
```python
agent = create_agent(
    model="gpt-3.5-turbo",
    memory=True,
    system_prompt="""You are a friendly pirate assistant. 
    Speak like a pirate and be helpful. Say 'Ahoy!' to greet users."""
)
```

### **4. Track Costs**
```python
agent = create_agent(
    model="gpt-3.5-turbo",
    track_costs=True
)

# After some conversations...
stats = agent.get_usage_stats()
print(f"Total cost: ${stats['estimated_cost']:.4f}")
print(f"Tokens used: {stats['total_tokens']}")
```

## 🛠️ Troubleshooting

### **"OPENAI_API_KEY environment variable required"**
```bash
# Set your API key
export OPENAI_API_KEY='sk-...'  # Get from https://platform.openai.com/api-keys

# Or use .env file
echo "OPENAI_API_KEY=sk-..." > .env
```

### **"No module named 'langswarm'"**
```bash
pip install langswarm openai
```

### **"Rate limit exceeded"**
- You're sending too many requests
- Use `gpt-3.5-turbo` instead of `gpt-4`
- Add delays between requests
- Upgrade your OpenAI plan

### **"Context length exceeded"**
- Conversation is too long
- Create a new agent to reset memory
- Or use a model with larger context (gpt-3.5-turbo-16k)

## 🎓 Next Steps (When Ready)

### **After mastering the basics:**

1. **Try Different Models**
   ```python
   # Anthropic Claude
   agent = create_agent(model="claude-3-sonnet")
   
   # Google Gemini
   agent = create_agent(model="gemini-pro")
   ```

2. **Add Tools & Capabilities**
   ```python
   # Agent that can read/write files
   agent = create_agent(
       model="gpt-4",
       tools=["filesystem"]
   )
   ```

3. **Build Multi-Agent Systems**
   ```python
   researcher = create_agent(model="gpt-3.5-turbo")
   writer = create_agent(model="gpt-4")
   
   # They work together
   research = await researcher.chat("Research climate change")
   article = await writer.chat(f"Write article based on: {research}")
   ```

4. **Use Configuration Files**
   ```yaml
   # config.yaml
   version: "2.0"
   agents:
     - id: "assistant"
       model: "gpt-4"
       system_prompt: "You are helpful"
   ```

## 📚 More Examples

Check out `examples/simple/` for 10 working examples:
- `01_basic_chat.py` - Simplest chatbot
- `02_memory_chat.py` - Conversation memory
- `03_two_agents.py` - Multi-agent system
- `05_with_tools.py` - File system access
- `09_streaming_response.py` - Real-time streaming
- `10_cost_tracking.py` - Usage monitoring

## 🎯 Summary

**You now know the 80% use case:**
1. Install: `pip install langswarm openai`
2. Set API key: `export OPENAI_API_KEY='...'`
3. Create agent: `agent = create_agent(model="gpt-3.5-turbo", memory=True)`
4. Chat: `response = await agent.chat("Hello!")`

**That's it!** You're ready to build AI applications with LangSwarm.

---

**Need help?** 
- 📖 [Full Documentation](../README.md)
- 💬 [GitHub Issues](https://github.com/langswarm/langswarm/issues)
- 🎯 [Examples](../examples/simple/)