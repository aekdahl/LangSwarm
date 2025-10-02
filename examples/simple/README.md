# 🚀 Simple LangSwarm Examples

**10 working examples, each 10-20 lines of code that actually work!**

## 📋 Prerequisites

```bash
# Install LangSwarm
pip install langswarm openai

# Set your API key
export OPENAI_API_KEY='your-openai-api-key-here'

# Or create a .env file:
echo "OPENAI_API_KEY=your-key-here" > .env
```

## 🏃 Quick Start

Run any example:
```bash
python 01_basic_chat.py
```

## 📚 Examples

### **01_basic_chat.py** (18 lines)
Simple chatbot conversation
```python
agent = create_agent(model="gpt-3.5-turbo")
response = await agent.chat("Hello!")
```

### **02_memory_chat.py** (20 lines)  
Chatbot that remembers conversation
```python
agent = create_agent(model="gpt-3.5-turbo", memory=True)
```

### **03_two_agents.py** (25 lines)
Two agents working together (researcher + writer)
```python
researcher = create_agent(system_prompt="You research topics")
writer = create_agent(system_prompt="You write articles")
```

### **04_different_models.py** (22 lines)
Using different models for different tasks
```python
quick = create_agent(model="gpt-3.5-turbo")  # Fast
smart = create_agent(model="gpt-4")          # Powerful
```

### **05_with_tools.py** (21 lines)
Agent with file system access
```python
agent = create_agent(tools=["filesystem"])
await agent.chat("Create a file called hello.txt")
```

### **06_workflow.py** (25 lines)
Simple workflow: Research → Analyze → Result
```python
workflow = create_workflow("researcher -> analyzer -> user")
```

### **07_web_search.py** (21 lines)
Agent with web search capability
```python
agent = create_agent(tools=["web_search"])
await agent.chat("What's the latest Python news?")
```

### **08_config_from_file.py** (24 lines)
Load configuration from YAML
```python
config = load_config("simple_config.yaml")
agent = config.get_agent("helper")
```

### **09_streaming_response.py** (19 lines)
Stream responses as they're generated
```python
async for chunk in agent.chat_stream("Write a story"):
    print(chunk, end="")
```

### **10_cost_tracking.py** (22 lines)
Track token usage and costs
```python
agent = create_agent(track_costs=True)
stats = agent.get_usage_stats()
```

## 🎯 Running the Examples

### **Run Individual Examples**
```bash
python 01_basic_chat.py
python 02_memory_chat.py
# ... etc
```

### **Test All Examples**
```bash
# Run all examples to verify they work
for example in *.py; do 
    echo "Testing $example..."
    python "$example"
done
```

### **What Each Example Shows**
- **Basic functionality** - Core agent creation and chat
- **Memory** - Conversation persistence 
- **Multi-agent** - Agents working together
- **Model selection** - Using different AI models
- **Tools** - File system and web search
- **Workflows** - Agent pipelines
- **Configuration** - YAML vs programmatic setup
- **Streaming** - Real-time responses
- **Monitoring** - Cost and usage tracking

## 🔧 Troubleshooting

### **Common Issues**

**Missing API Key**
```
❌ Set OPENAI_API_KEY environment variable
```
Solution: `export OPENAI_API_KEY='your-key'`

**Import Error**
```
ModuleNotFoundError: No module named 'langswarm'
```
Solution: `pip install langswarm openai`

**Tool Not Available**
```
❌ Tool 'filesystem' requires additional dependencies
```
Solution: `pip install langswarm[full]` or install specific tools

### **Getting API Keys**

1. **OpenAI**: https://platform.openai.com/api-keys
2. **Anthropic**: https://console.anthropic.com/api-keys  
3. **Google**: https://makersuite.google.com/app/apikey

### **Dependencies by Example**

| Example | Required | Optional |
|---------|----------|----------|
| 01-04 | `openai` | - |
| 05 | `openai` | filesystem tools |
| 06 | `openai` | - |
| 07 | `openai` | web search tools |
| 08-10 | `openai` | - |

## 💡 Next Steps

1. **Start simple** - Run `01_basic_chat.py` first
2. **Experiment** - Modify the prompts and see what happens
3. **Combine** - Mix features from different examples
4. **Scale up** - Use `templates/` for more complex configurations
5. **Deploy** - Add web APIs, databases, etc.

## 🎉 Success Criteria

If these examples work, LangSwarm is properly installed and you can:
- ✅ Create agents in 2 lines of code
- ✅ Have conversations with memory
- ✅ Use multiple agents together  
- ✅ Add tools and capabilities
- ✅ Track costs and usage
- ✅ Build workflows and pipelines

**These examples prove LangSwarm works simply and reliably!**