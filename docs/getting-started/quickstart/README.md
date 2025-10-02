# ⚡ LangSwarm Quickstart

**Get LangSwarm running in 30 seconds with working examples.**

## 🚀 **30-Second Setup**

### **Step 1: Install LangSwarm**
```bash
pip install langswarm
```

### **Step 2: Set Your API Key**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### **Step 3: Create Your First Agent**

**Option A: Configuration File Approach**

Create `langswarm.yaml`:
```yaml
version: "2.0"
agents:
  - id: "assistant"
    name: "My Assistant"
    provider: "openai"
    model: "gpt-4o"
    system_prompt: "You are a helpful AI assistant."

tools: {}
workflows: []
```

Run it:
```python
from langswarm.core.config import load_config

# Load configuration
config = load_config('langswarm.yaml')
print(f'✅ Loaded {len(config.agents)} agents successfully!')

# Get the agent
agent_config = config.get_agent("assistant")
print(f"Agent: {agent_config.name} using {agent_config.provider}")
```

**Option B: Pure Python Approach**

```python
import asyncio
from langswarm.core.agents import create_openai_agent

async def main():
    # Create agent
    agent = create_openai_agent(
        model="gpt-4o",
        api_key="your-openai-api-key"  # or use OPENAI_API_KEY env var
    )
    
    # Chat with agent
    response = await agent.chat("Hello! What can you help me with?")
    print(f"Agent: {response.content}")

# Run the example
asyncio.run(main())
```

## 🎯 **What You Just Built**

Congratulations! You've successfully:
- ✅ **Installed LangSwarm V2**
- ✅ **Created your first AI agent**
- ✅ **Had a conversation with the agent**

## 🔥 **Next Steps**

### **Add Memory (5 minutes)**
```python
from langswarm.core.agents import AgentBuilder

agent = (AgentBuilder()
         .openai()
         .model("gpt-4o")
         .memory_enabled(True)  # Add persistent memory
         .build())

# Now your agent remembers previous conversations!
```

### **Add Tools (10 minutes)**
```yaml
# langswarm.yaml
version: "2.0"
agents:
  - id: "assistant"
    provider: "openai"
    model: "gpt-4o"
    tools: ["filesystem", "web_search"]  # Add tools

tools:
  filesystem:
    type: "mcp"
    local_mode: true
  web_search:
    type: "mcp"
    local_mode: true
```

### **Create Workflows (15 minutes)**
```yaml
# langswarm.yaml
workflows:
  - id: "research_workflow"
    name: "Research and Summarize"
    steps:
      - agent: "researcher"
        tools: ["web_search"]
      - agent: "summarizer"
        input: "${researcher.output}"
```

## 📚 **Learn More**

- **[Installation Guide](../installation/README.md)** - Detailed setup instructions
- **[First Project](../first-project/README.md)** - Build a complete project
- **[Configuration Guide](../../user-guides/configuration/README.md)** - Advanced configuration
- **[Agent Guide](../../user-guides/agents/README.md)** - Creating powerful agents
- **[Tools Guide](../../user-guides/tools/README.md)** - Adding capabilities with tools

## 🆘 **Need Help?**

- **[Troubleshooting](../../troubleshooting/common-issues/README.md)** - Common issues and solutions
- **[FAQ](../../troubleshooting/faq/README.md)** - Frequently asked questions
- **[Community Support](../../community/support/README.md)** - Get help from the community

---

**🎉 Welcome to LangSwarm V2! You're ready to build powerful multi-agent AI systems.**
