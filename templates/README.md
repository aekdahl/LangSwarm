# 📚 LangSwarm Configuration Templates

Pre-built configurations for common use cases. Copy and customize as needed!

## 🚀 Quick Start

```bash
# Copy a template
cp templates/chatbot.yaml langswarm.yaml

# Run it
python your_app.py
```

## 📝 Available Templates

### **1. `minimal.yaml`** (4 lines)
The absolute minimum configuration. Perfect for testing.
```yaml
version: "2.0"
agents:
  - id: "assistant"
    model: "gpt-3.5-turbo"
```

### **2. `chatbot.yaml`** (9 lines)
Simple conversational chatbot with personality.
- Single agent
- Custom system prompt
- Automatic memory

### **3. `customer-support.yaml`** (28 lines)
Multi-agent customer support with intelligent routing.
- Classifier agent routes inquiries
- Specialized agents for technical and billing
- Conditional workflow routing

### **4. `code-assistant.yaml`** (12 lines)
AI pair programmer with file system access.
- GPT-4 for better code generation
- File system tools included
- Professional coding prompt

### **5. `content-pipeline.yaml`** (17 lines)
Three-stage content creation workflow.
- Research → Write → Edit pipeline
- Different agents for each stage
- Automatic handoff between agents

### **6. `multi-provider.yaml`** (23 lines)
Demonstrates using multiple AI providers.
- OpenAI for analysis
- Anthropic for creativity
- Google for multimodal

### **7. `web-search.yaml`** (13 lines)
Research assistant with web search.
- Web search tool included
- Citation-focused prompt
- Current information retrieval

## 🛠️ Customization Tips

### **Changing Models**
```yaml
# Budget option
model: "gpt-3.5-turbo"

# Best quality
model: "gpt-4"

# Latest model
model: "gpt-4-turbo-preview"
```

### **Adding Memory**
```yaml
# Default (SQLite)
# No config needed!

# Redis (faster)
memory:
  backend: "redis"

# In-memory only
memory:
  backend: "memory"
```

### **Adding Tools**
```yaml
agents:
  - id: "assistant"
    model: "gpt-4"
    tools: ["filesystem", "web_search", "code_executor"]
```

### **Custom Workflows**
```yaml
# Simple linear
workflows:
  - "agent1 -> agent2 -> user"

# Conditional
workflows:
  - "classifier -> (optionA | optionB) -> user"

# Parallel
workflows:
  - "agent1, agent2, agent3 -> aggregator -> user"
```

## 📖 From Template to Production

1. **Start with a template**
   ```bash
   cp templates/chatbot.yaml my-config.yaml
   ```

2. **Customize the basics**
   - Change system prompts
   - Adjust models for cost/quality
   - Add tools as needed

3. **Add production features**
   ```yaml
   # Add when ready
   memory:
     backend: "redis"
   
   security:
     rate_limiting:
       enabled: true
   ```

4. **Scale up**
   - Add more agents
   - Create complex workflows
   - Integrate with your systems

## 💡 Best Practices

1. **Start simple** - Use minimal config first
2. **Test locally** - SQLite memory is perfect for development
3. **Add features gradually** - Don't add everything at once
4. **Use version control** - Track your config changes
5. **Environment variables** - Keep secrets out of configs

## 🤔 Which Template Should I Use?

- **Just exploring?** → `minimal.yaml`
- **Building a chatbot?** → `chatbot.yaml`
- **Need customer service?** → `customer-support.yaml`
- **Writing code?** → `code-assistant.yaml`
- **Creating content?** → `content-pipeline.yaml`
- **Need web data?** → `web-search.yaml`
- **Using multiple AIs?** → `multi-provider.yaml`

Remember: These are starting points! Mix and match features from different templates to build exactly what you need.