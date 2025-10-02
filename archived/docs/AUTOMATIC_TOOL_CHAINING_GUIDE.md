# 🔗 Automatic Tool Chaining in LangSwarm

**Make your agents incredibly smart with zero configuration** - LangSwarm agents automatically chain tool calls to gather complete information and provide comprehensive answers.

---

## 🎯 **What is Automatic Tool Chaining?**

When you call `agent.chat("question")`, your agent can automatically:
- Make **multiple tool calls** in sequence
- **Build context** from each tool result
- **Make intelligent decisions** about what information to gather next
- **Provide comprehensive answers** based on all collected data

**All automatically - no workflow configuration required!**

---

## ⚡️ **Quick Example**

```python
from langswarm.core.config import LangSwarmConfigLoader

# Simple setup
loader = LangSwarmConfigLoader('langswarm.yaml')
workflows, agents, *_ = loader.load()
chatbot = agents["my_agent"]

# One simple call - but multiple tools executed behind the scenes!
response = chatbot.chat("What is our company's latest product pricing?")
```

**What happens behind the scenes:**
1. 🔍 Agent searches knowledge base for "product pricing"
2. 📊 Agent searches for "latest pricing updates" 
3. 💰 Agent searches for "current pricing tiers"
4. ✅ Agent combines all results into comprehensive answer

**User sees:** Complete, accurate pricing information  
**Agent did:** 3 separate tool calls automatically

---

## 🔄 **How It Works - The Magic Mechanism**

### **Step 1: Initial Agent Response**
```json
{
  "response": "I'll search our knowledge base for the latest pricing information",
  "mcp": {
    "tool": "knowledge_search",
    "method": "search",
    "params": {"query": "product pricing 2024"}
  }
}
```

### **Step 2: Tool Execution**
```
🔧 Tool executes: knowledge_search("product pricing 2024")
📋 Results: [{"title": "Basic Pricing", "content": "Basic plan: $10/month..."}, ...]
```

### **Step 3: Context Enrichment** ⭐ **KEY STEP**
LangSwarm automatically creates enriched prompt:
```
"I'll search our knowledge base for the latest pricing information

Tool result: [Basic plan: $10/month, Pro plan: $25/month, but missing Enterprise pricing...]"
```

### **Step 4: Agent Makes ANOTHER Tool Call**
```json
{
  "response": "I found basic pricing but need Enterprise pricing details",
  "mcp": {
    "tool": "knowledge_search", 
    "method": "search",
    "params": {"query": "Enterprise pricing tier 2024"}
  }
}
```

### **Step 5: Recursive Chaining**
This process **repeats automatically** until the agent has all needed information!

### **Step 6: Final Response**
```json
{
  "response": "Here's our complete pricing structure: Basic ($10/month), Pro ($25/month), Enterprise ($100/month) with custom features..."
}
```
*No `mcp` field = chaining stops*

---

## 🎯 **Real-World Examples**

### **Example 1: Customer Support Agent**

**User Question:** *"Why is my website slow?"*

**Agent's Automatic Tool Chain:**
```
1. 🔍 search_logs("website performance issues")
2. 📊 check_metrics("server response times") 
3. 🔧 analyze_config("optimization settings")
4. ✅ Comprehensive diagnosis with specific recommendations
```

**User Sees:** *"Your website is slow due to unoptimized images (3.2MB average) and missing CDN. Here's how to fix it..."*

### **Example 2: Sales Assistant**

**User Question:** *"What's our best package for a small restaurant?"*

**Agent's Automatic Tool Chain:**
```
1. 🔍 search_products("restaurant packages")
2. 💰 get_pricing("small business tiers")
3. 📋 check_features("restaurant-specific tools")
4. ✅ Tailored recommendation with pricing
```

**User Sees:** *"For small restaurants, I recommend our 'Hospitality Pro' package ($45/month) which includes POS integration, inventory tracking, and customer management..."*

### **Example 3: Technical Research Agent**

**User Question:** *"How do I implement OAuth in our React app?"*

**Agent's Automatic Tool Chain:**
```
1. 🔍 search_docs("React OAuth implementation")
2. 📝 get_examples("OAuth code samples")
3. 🔧 check_dependencies("required packages")
4. ✅ Complete implementation guide
```

---

## 🛠️ **Configuration for Tool Chaining**

### **Minimal Configuration**
```yaml
version: "1.0"
project_name: "smart-agent"

agents:
  - id: "smart_assistant"
    model: "gpt-4o"
    system_prompt: |
      You are a helpful assistant. When users ask questions, search your 
      knowledge base to provide accurate information. Make multiple searches 
      if needed to gather complete information.
    tools:
      - "knowledge_search"

tools:
  - id: "knowledge_search"
    type: "mcpbigquery_vector_search"
    description: "Search company knowledge base"
    config:
      project_id: "your-project"
      dataset_id: "knowledge_base"
      table_name: "embeddings"
```

**That's it!** No complex workflows, brokers, or orchestration needed.

### **Usage Code**
```python
from langswarm.core.config import LangSwarmConfigLoader

# Load configuration
loader = LangSwarmConfigLoader('langswarm.yaml')
workflows, agents, *_ = loader.load()

# Get your agent
assistant = agents["smart_assistant"]

# Ask complex questions - agent will chain tools automatically!
response = assistant.chat("How do I optimize our database performance?")
print(response)  # Comprehensive answer from multiple tool calls
```

---

## 🧠 **Intelligent Decision Making**

### **Context Preservation**
Each tool call builds on previous results:
```
Tool Call 1: "basic database info" 
    ↓
Tool Call 2: "performance metrics" (knows about database from Call 1)
    ↓  
Tool Call 3: "optimization strategies" (knows metrics from Call 2)
```

### **Adaptive Behavior**
Agents make smart decisions:
- **🎯 Goal-oriented**: Stop when enough information gathered
- **🔄 Iterative**: Refine search based on results
- **🛡️ Error recovery**: Try alternative tools if one fails
- **⚡ Efficient**: Don't repeat unnecessary searches

### **Natural Termination**
Chaining stops when agent returns response without tool calls:
```json
{
  "response": "Based on my research, here's your complete answer..."
  // No "mcp" field = done!
}
```

---

## 📊 **Benefits vs Traditional Approaches**

| **Approach** | **Setup** | **Flexibility** | **Intelligence** | **Maintenance** |
|--------------|-----------|-----------------|------------------|-----------------|
| **Manual Tool Calling** | Complex | Limited | Manual | High |
| **Predefined Workflows** | Medium | Medium | Scripted | Medium |
| **🔗 Automatic Chaining** | **Minimal** | **Maximum** | **AI-Driven** | **Zero** |

### **Traditional Workflow (Complex)**
```yaml
workflows:
  - id: "research_workflow"
    steps:
      - id: "search1"
        tool: "search"
        params: {"query": "topic1"}
      - id: "search2" 
        tool: "search"
        params: {"query": "{{ search1.related_topic }}"}
      - id: "analyze"
        tool: "analyze"
        params: {"data": "{{ search1.results }}, {{ search2.results }}"}
```

### **Automatic Chaining (Simple)**
```python
# Just ask! Agent figures out the tool chain automatically
response = agent.chat("Research this topic comprehensively")
```

---

## 🎛️ **Advanced Configuration**

### **Response Modes**

#### **Integrated Mode (Default)**
```yaml
agents:
  - id: "assistant"
    response_mode: "integrated"  # Wait for all tools, return final answer
```

**Behavior:** User sees complete answer after all tool calls finish

#### **Streaming Mode**
```yaml
agents:
  - id: "assistant" 
    response_mode: "streaming"  # Show progress as tools execute
```

**Behavior:** User sees agent thinking process and tool results

### **System Prompt Optimization**
```yaml
system_prompt: |
  You are an expert research assistant. When users ask questions:
  
  1. **Search comprehensively** - use multiple searches to gather complete information
  2. **Build context** - each search should build on previous results  
  3. **Be thorough** - don't stop until you have complete information
  4. **Synthesize** - combine all findings into a comprehensive answer
  
  Available tools: knowledge_search, file_search, api_lookup
  Use as many as needed to provide complete, accurate answers.
```

### **Tool-Specific Instructions**
```yaml
tools:
  - id: "knowledge_search"
    description: "Search company knowledge base"
    instruction: |
      Use this for: company policies, product info, internal docs.
      Try multiple search terms if first search doesn't have complete info.
  
  - id: "web_search" 
    description: "Search public web"
    instruction: |
      Use this for: current events, external research, industry trends.
      Good for fact-checking and getting latest information.
```

---

## 🚀 **Getting Started**

### **1. Create Your Config**
```yaml
version: "1.0"
agents:
  - id: "research_agent"
    model: "gpt-4o"
    system_prompt: "You are a research assistant. Use multiple searches to provide comprehensive answers."
    tools: ["search", "docs", "files"]

tools:
  - id: "search"
    type: "mcpbigquery_vector_search"
    description: "Search knowledge base"
```

### **2. Load and Use**
```python
from langswarm.core.config import LangSwarmConfigLoader

loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, *_ = loader.load()
agent = agents["research_agent"]

# Ask anything - automatic tool chaining handles the complexity!
response = agent.chat("Explain our complete product offering")
```

### **3. Watch the Magic** ✨
Your agent will automatically:
- Search for product information
- Look up pricing details  
- Find feature comparisons
- Gather customer testimonials
- Synthesize everything into comprehensive answer

**All from one simple `chat()` call!**

---

## 🔧 **Troubleshooting**

### **Tools Not Chaining?**

**Check System Prompt:**
```yaml
# ❌ Vague
system_prompt: "You are helpful"

# ✅ Specific about tool usage
system_prompt: "You are helpful. Use multiple searches to gather complete information before answering."
```

**Check Tool Instructions:**
```yaml
tools:
  - id: "search"
    # ❌ No instruction
    description: "Search tool"
    
    # ✅ Clear instruction 
    description: "Search knowledge base"
    instruction: "Use this to find comprehensive information. Make multiple searches with different terms if needed."
```

### **Chaining Stopping Too Early?**

**Enhance System Prompt:**
```yaml
system_prompt: |
  Be thorough in your research. Continue searching until you have:
  - Complete factual information
  - Multiple perspectives 
  - Recent updates
  - Practical examples
  
  Don't stop after just one search - be comprehensive!
```

### **Too Many Tool Calls?**

**Add Efficiency Guidelines:**
```yaml
system_prompt: |
  You are efficient but thorough. Make tool calls strategically:
  - Start with broad searches
  - Refine based on results
  - Stop when you have sufficient information
  - Maximum 3-4 tool calls per question
```

---

## 🎉 **Conclusion**

**Automatic Tool Chaining makes every agent a research expert!**

- ✅ **Zero configuration** - works out of the box
- ✅ **Maximum intelligence** - AI decides the tool chain  
- ✅ **Perfect results** - comprehensive answers every time
- ✅ **Simple usage** - just call `agent.chat()`

**Transform any simple question into comprehensive research with automatic tool chaining!** 🚀

---

## 📚 **Related Documentation**

- [Getting Started Guide](docs/getting-started.md) - Basic LangSwarm setup
- [Tool Configuration](docs/tool-configuration.md) - Setting up tools
- [System Prompts](docs/system-prompts.md) - Optimizing agent behavior
- [Response Modes](docs/guides/RESPONSE_MODES_GUIDE.md) - Streaming vs Integrated
