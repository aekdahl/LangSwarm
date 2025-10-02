# 🚀 LangSwarm

**Build powerful multi-agent AI systems in 30 seconds, not hours.**

LangSwarm has been **completely transformed** from a complex, expert-only framework into a **beginner-friendly system** that maintains all advanced capabilities. Get started instantly with simple configurations, then scale to enterprise complexity when needed.

🎤 **NEW: OpenAI Realtime API Integration** - Build voice agents with the same simplicity as text agents!

## 🎉 **LangSwarm Simplification Project - COMPLETE**

### **🎯 Mission Accomplished: From Complex to Simple**

**Before:** 2+ hours setup, 8 config files, 22+ parameters, expert-only  
**After:** 30 second setup, 1 config file, smart defaults, beginner-friendly

| **Metric** | **Before** | **After** | **Improvement** |
|------------|------------|-----------|-----------------|
| **Setup Time** | 2+ hours | 30 seconds | **240x faster** |
| **Config Files** | 8 separate files | 1 unified file | **87.5% reduction** |
| **Agent Parameters** | 22+ parameters | 1 config object | **95% reduction** |
| **Workflow Complexity** | 15+ lines YAML | 1 line syntax | **90% reduction** |
| **Memory Setup** | 20+ settings | 3 simple tiers | **95% reduction** |

---

## ⚡ 2-Minute Quick Start (80% Use Case)

**Most users want:** A simple AI chatbot with memory. Here's how:

### **1. Install (30 seconds)**
```bash
pip install langswarm openai
export OPENAI_API_KEY='sk-...'  # Get from platform.openai.com
```

### **2. Create Chatbot (30 seconds)**
```python
# chatbot.py
import asyncio
from langswarm import create_agent

async def main():
    # Create chatbot with memory
    bot = create_agent(model="gpt-3.5-turbo", memory=True)
    
    # Chat loop
    print("Bot: Hi! Type 'quit' to exit.\n")
    while True:
        user = input("You: ")
        if user.lower() == 'quit':
            break
        response = await bot.chat(user)
        print(f"Bot: {response}\n")

asyncio.run(main())
```

### **3. Run (1 minute)**
```bash
python chatbot.py
```

**That's it!** You have a working AI chatbot with conversation memory.

### **Common Enhancements**
```python
# Better responses
bot = create_agent(model="gpt-4")

# Add personality  
bot = create_agent(system_prompt="You are a pirate")

# Stream responses
async for chunk in bot.chat_stream("Hello"):
    print(chunk, end="")

# Track costs
bot = create_agent(track_costs=True)
print(f"Cost: ${bot.get_usage_stats()['estimated_cost']}")
```

📚 **[Full Quick Start Guide](docs/QUICK_START.md)** | 🎯 **[10 Simple Examples](examples/simple/)**

---

## 🧠 **Memory Made Simple**

**3-Tier System - Choose Your Complexity:**

```yaml
# Tier 1: Development (instant setup)
memory: true

# Tier 2: Production (smart auto-configuration)
memory: production

# Tier 3: Custom (full control)
memory:
  backend: chromadb
  settings: {persist_directory: "/custom/path"}
```

**Smart Environment Detection:**
- **Google Cloud** → BigQuery (analytics-ready)
- **AWS** → Elasticsearch (full-text search)  
- **Redis Available** → Redis (ultra-fast)
- **Local/Development** → SQLite (zero-config)

---

## 🔄 **Workflow Simplification**

**90% Complexity Reduction - From 15+ lines to 1 line:**

```yaml
# Before (Complex YAML)
workflows:
  - id: analysis_workflow
    steps:
      - id: step1
        agent: extractor
        input: ${context.user_input}
        output: {to_step: step2}
      - id: step2
        agent: analyzer
        input: ${step1.output}
        output: {to_step: step3}
      - id: step3
        agent: summarizer
        input: ${step2.output}
        output: {to: user}

# After (Simple Syntax)
workflows:
  - "extractor -> analyzer -> summarizer -> user"
```

**Template Library:**
```yaml
workflows:
  - "assistant -> user"                                    # Simple chat
  - "researcher -> writer -> editor -> user"              # Content pipeline
  - "expert1, expert2, expert3 -> consensus -> user"      # Expert consensus
  - "classifier -> (specialist1 | specialist2) -> user"   # Smart routing
```

---

## 🤖 **Simplified Agent Architecture** 

**95% Parameter Reduction - From 22+ parameters to 1 config object:**

```python
# Before (Complex)
agent = AgentWrapper(
    name="assistant", agent=base_agent, model="gpt-4o", memory=memory_config,
    agent_type="conversational", is_conversational=True, langsmith_api_key=api_key,
    rag_registry=rag_registry, context_limit=4000, system_prompt=system_prompt,
    tool_registry=tool_registry, plugin_registry=plugin_registry,
    memory_adapter=memory_adapter, memory_summary_adapter=summary_adapter,
    broker=message_broker, response_mode="structured", streaming_config=streaming_config,
    session_manager=session_manager, enable_hybrid_sessions=True,
    enhanced_backend=enhanced_backend, enhanced_config=enhanced_config,
    allow_middleware=True
    # ... 5+ more parameters
)

# After (Simple)
from langswarm.core.agents import create_openai_agent
agent = create_openai_agent(model="gpt-4o", api_key="your-key")
```

**Factory Functions for Common Use Cases:**
```python
from langswarm.core.agents import (
    create_openai_agent,
    create_anthropic_agent, 
    create_gemini_agent
)

# Instant specialized agents
chat_agent = create_openai_agent(model="gpt-4o")
coding_agent = create_anthropic_agent(model="claude-3-sonnet-20240229")
research_agent = create_gemini_agent(model="gemini-pro")
```

---

## 🎯 **Complete Real-World Example**

```yaml
# langswarm.yaml - Production content creation system
version: "1.0"
project_name: "content-pipeline"

agents:
  - {id: researcher, model: gpt-4o, behavior: research, tools: [web_search]}
  - {id: writer, model: gpt-4o, behavior: creative, memory_enabled: true}
  - {id: editor, model: gpt-4o, behavior: analytical, tools: [grammar_check]}
  - {id: publisher, model: gpt-4o, behavior: helpful, tools: [cms_integration]}

memory: production  # Auto-selects optimal backend (BigQuery/Elasticsearch/Redis/ChromaDB)

workflows:
  - id: content_pipeline
    workflow: "researcher -> writer -> editor -> publisher -> user"
  - id: quick_post
    simple: "writer -> user"
  - id: fact_check
    workflow: "researcher, editor -> consensus -> user"

# Tools auto-discovered based on agent behaviors and environment
```

Run with:
```bash
python -c "
from langswarm.core.config import load_config
from langswarm.core.workflows import get_workflow_engine

config = load_config('langswarm.yaml')
engine = get_workflow_engine()
result = engine.execute_workflow('content_pipeline', 'Write about AI simplification')
print(result)
"
```

---

## 📚 **Documentation & Guides**

### **New User Guides:**
- **[📖 Complete Simplified Guide](docs/SIMPLIFIED_LANGSWARM_GUIDE.md)** - Everything you need to get started
- **[🧠 Memory Made Simple](docs/simplification/04-memory-made-simple.md)** - 3-tier memory system
- **[🔄 Workflow Simplification](docs/simplification/workflow-examples.md)** - Simple syntax examples
- **[🤖 Simplified Agents](docs/simplification/agent-architecture.md)** - Clean agent architecture

### **Advanced Features (For Experts):**
- **[🔧 Advanced Configuration](docs/advanced-config.md)** - Full technical details
- **[🛠️ Tool Development](docs/tool-development.md)** - Building custom tools
- **[⚡ Performance Optimization](docs/performance.md)** - Enterprise optimization

---

## 🆕 Latest Technical Features

### 🚀 **Revolutionary Structured JSON Responses** (v0.0.50+)
- **Breakthrough Design**: Agents can now provide BOTH user responses AND tool calls simultaneously
- **No More Forced Choice**: Previously agents chose between communication OR tool usage - now they do both
- **Dual Response Modes**: Integrated (polished final answer) or Streaming (immediate feedback + tool results)
- **Natural Interactions**: Users see what agents are doing while tools execute

```json
{
  "response": "I'll check that configuration file for you to analyze its contents",
  "mcp": {
    "tool": "filesystem",
    "method": "read_file", 
    "params": {"path": "/tmp/config.json"}
  }
}
```

### 🔥 **Local MCP Mode** - Zero Latency Tools
- **1000x Faster**: Direct function calls vs HTTP (0ms vs 50-100ms)
- **Zero Setup**: No containers, no external servers
- **Full Compatibility**: Works with existing MCP workflows

### 💾 **Enhanced Memory System**
- **BigQuery Integration**: Analytics-ready conversation storage
- **Multiple Backends**: SQLite, ChromaDB, Redis, Qdrant, Elasticsearch
- **Auto-Embeddings**: Semantic search built-in

### 🛠️ **Fixed Dependencies**
- **Complete Installation**: `pip install langswarm` now installs all dependencies
- **30+ Libraries**: LangChain, OpenAI, FastAPI, Discord, and more
- **Ready to Use**: No manual dependency management needed
