# 📚 LangSwarm Configuration Templates

**Ready-to-use Python templates for common use cases**

Pre-built configurations showing best practices for different scenarios. Each template is a complete, working Python script you can copy and customize.

## 🚀 Quick Start

```bash
# Copy a template
cp templates/chatbot.py my_chatbot.py

# Customize it for your needs
# Then run it
python my_chatbot.py
```

## 📝 Available Templates

### **1. `minimal.py`** (15 lines)
The absolute minimum to get started. Perfect for testing.

```python
from langswarm import create_agent

agent = create_agent(model="gpt-3.5-turbo")
response = await agent.chat("Hello!")
```

**Use when:** Just exploring LangSwarm

---

### **2. `chatbot.py`** (25 lines)
Simple conversational chatbot with personality and memory.

**Features:**
- Custom system prompt for personality
- Automatic conversation memory
- Simple, clean code

**Use when:** Building a conversational AI assistant

---

### **3. `code-assistant.py`** (30 lines)
AI pair programmer with file system access.

**Features:**
- GPT-4 for better code generation
- File system tools for reading/writing code
- Memory for context across conversation

**Use when:** Building a coding assistant or automation tool

---

### **4. `content-pipeline.py`** (45 lines)
Three-stage content creation workflow.

**Features:**
- Research → Write → Edit pipeline
- Specialized agents for each stage
- Workflow orchestration

**Use when:** Automating content creation at scale

---

### **5. `web-search.py`** (30 lines)
Research assistant with real-time web search.

**Features:**
- Web search tool integration
- Citation-focused responses
- Current information retrieval

**Use when:** Building research or fact-checking tools

---

### **6. `multi-provider.py`** (50 lines)
Using multiple AI providers for different tasks.

**Features:**
- OpenAI GPT-4 for analysis
- Anthropic Claude for creativity
- Google Gemini for multimodal tasks
- Builder pattern for advanced configuration

**Use when:** Leveraging strengths of different AI models

---

### **7. `customer-support.py`** (70 lines)
Multi-agent customer support with intelligent routing.

**Features:**
- Inquiry classification
- Specialized support agents
- Intelligent routing logic
- Tool access for technical support

**Use when:** Building customer service automation

---

## 🛠️ Customization Guide

### **Changing Models**

```python
# Budget option
agent = create_agent(model="gpt-3.5-turbo")

# Best quality
agent = create_agent(model="gpt-4")

# Latest model
agent = create_agent(model="gpt-4-turbo")

# Use Anthropic Claude
agent = await AgentBuilder().anthropic().model("claude-3-5-sonnet-20241022").build()
```

### **Adding Memory**

```python
# Simple in-memory (default)
agent = create_agent(model="gpt-4", memory=True)

# Persistent SQLite storage
from langswarm.core.memory import create_memory_manager

memory = create_memory_manager(backend="sqlite", db_path="./conversations.db")
agent = create_agent(model="gpt-4", memory=True, memory_manager=memory)
```

### **Adding Tools**

```python
# Single tool
agent = create_agent(model="gpt-4", tools=["filesystem"])

# Multiple tools
agent = create_agent(
    model="gpt-4",
    tools=["filesystem", "web_search", "github"]
)
```

### **Advanced Configuration with Builder Pattern**

```python
from langswarm.core.agents import AgentBuilder

agent = await (
    AgentBuilder()
    .name("advanced-agent")
    .openai()
    .model("gpt-4")
    .system_prompt("You are a helpful assistant")
    .tools(["filesystem", "web_search"])
    .memory_enabled(True)
    .streaming(True)
    .temperature(0.7)
    .max_tokens(4000)
    .timeout(60)
    .build()
)
```

### **Creating Workflows**

```python
from langswarm import create_agent
from langswarm.core.agents import register_agent
from langswarm.core.workflows import create_simple_workflow, get_workflow_engine

# Create agents
agent1 = create_agent(name="agent1", model="gpt-4", system_prompt="Research topics")
agent2 = create_agent(name="agent2", model="gpt-4", system_prompt="Write content")

# Register for orchestration
register_agent(agent1)
register_agent(agent2)

# Create workflow
workflow = create_simple_workflow(
    workflow_id="pipeline",
    name="Research and Write",
    agent_chain=["agent1", "agent2"]
)

# Execute
engine = get_workflow_engine()
result = await engine.execute_workflow(
    workflow=workflow,
    input_data={"input": "Write about AI"}
)
```

## 📖 From Template to Production

### **1. Start with a template**
```bash
cp templates/chatbot.py my_project.py
```

### **2. Customize the basics**
- Change system prompts for your use case
- Adjust models for cost/quality tradeoff
- Add tools as needed

### **3. Add production features**
```python
# Persistent memory
memory = create_memory_manager(backend="sqlite", db_path="./db/conversations.db")

# Observability
from langswarm.observability import enable_instrumentation
enable_instrumentation(service_name="my-app", exporter="jaeger")

# Error handling
try:
    response = await agent.chat(user_input)
except Exception as e:
    logger.error(f"Error: {e}")
    response = "I encountered an error. Please try again."
```

### **4. Scale up**
- Add more specialized agents
- Create complex workflows
- Integrate with your systems (databases, APIs, etc.)
- Deploy to cloud platforms

## 💡 Best Practices

1. **Start simple** - Use minimal.py first to verify everything works
2. **Use type hints** - Makes code more maintainable
3. **Handle errors** - Add try/catch blocks for production
4. **Use environment variables** - Keep API keys out of code
5. **Add logging** - Track what's happening in your agents
6. **Test locally** - In-memory storage perfect for development
7. **Version control** - Track your code changes with git

## 🤔 Which Template Should I Use?

- **Just exploring?** → `minimal.py`
- **Building a chatbot?** → `chatbot.py`
- **Need customer service?** → `customer-support.py`
- **Writing code?** → `code-assistant.py`
- **Creating content?** → `content-pipeline.py`
- **Need web data?** → `web-search.py`
- **Using multiple AIs?** → `multi-provider.py`

## 🔧 Environment Setup

All templates require these environment variables:

```bash
# Required for OpenAI
export OPENAI_API_KEY="sk-..."

# Optional: for other providers
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export COHERE_API_KEY="..."
```

Or create a `.env` file:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## 📚 Next Steps

After running a template:

1. **Modify the system prompts** - Customize agent behavior
2. **Add more agents** - Create specialized roles
3. **Integrate tools** - Connect to databases, APIs, file systems
4. **Build workflows** - Chain agents together
5. **Deploy** - Move to production with proper error handling

---

**Remember:** These templates are starting points. Mix and match features to build exactly what you need. LangSwarm's code-first approach gives you complete flexibility!
