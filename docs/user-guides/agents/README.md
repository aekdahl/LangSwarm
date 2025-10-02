# LangSwarm V2 Agent User Guide

**Learn how to create and use agents in the LangSwarm V2 system**

## 🎯 Overview

LangSwarm V2 completely redesigns the agent experience with a simple, fluent builder pattern that replaces the complex AgentWrapper. Create powerful agents with just a few lines of code while leveraging provider-specific features and production-ready capabilities.

---

## 🚀 Quick Start

### **Create Your First Agent**

```python
from langswarm.core.agents import AgentBuilder

# Create a simple OpenAI agent
agent = AgentBuilder().openai().model("gpt-4o").build()

# Start chatting
response = await agent.chat("Hello! What can you help me with?")
print(response)
```

### **Create Different Provider Agents**

```python
# OpenAI agent (GPT models)
openai_agent = AgentBuilder().openai().model("gpt-4o").build()

# Anthropic agent (Claude models)
anthropic_agent = AgentBuilder().anthropic().model("claude-3-opus").build()

# Google Gemini agent
gemini_agent = AgentBuilder().gemini().model("gemini-pro").build()
```

---

## 🎛️ Agent Configuration

### **Basic Configuration**

```python
# Configure model behavior
agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .temperature(0.7)          # Creativity level (0.0-2.0)
    .max_tokens(1500)          # Response length limit
    .system_prompt("You are a helpful coding assistant")
    .build())
```

### **Advanced Configuration**

```python
# Full configuration example
agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .temperature(0.7)
    .max_tokens(2000)
    .top_p(0.9)               # Nucleus sampling
    .frequency_penalty(0.1)    # Reduce repetition
    .system_prompt("You are an expert Python developer")
    .tools(["filesystem", "web_search", "calculator"])
    .memory_enabled(True)
    .session_id("user_123")
    .cost_tracking(True)
    .build())
```

---

## 💬 Using Agents

### **Basic Chat**

```python
# Simple conversation
response = await agent.chat("Explain machine learning in simple terms")
print(response)

# With context
response = await agent.chat(
    "How would I implement this in Python?",
    context="We're discussing neural networks"
)
```

### **Streaming Responses**

```python
# Real-time streaming for long responses
print("Agent: ", end="", flush=True)
async for chunk in agent.chat_stream("Write a detailed explanation of quantum computing"):
    print(chunk, end="", flush=True)
print()  # New line when done
```

### **Chat with Tools**

```python
# Agent can use tools to help with tasks
response = await agent.chat(
    "Read the file config.py and explain what it does",
    tools_enabled=True
)
print(response)
```

---

## 🛠️ Tool Integration

### **Enable Tools**

```python
# Create agent with specific tools
agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .tools(["filesystem", "web_search", "calculator"])
    .tool_choice("auto")      # Let agent decide when to use tools
    .build())
```

### **Available Tools**

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| `filesystem` | File operations | "Read the README file" |
| `web_search` | Internet search | "Look up the latest Python version" |
| `calculator` | Math calculations | "Calculate compound interest" |
| `code_interpreter` | Code execution | "Run this Python script" |
| `database` | Database queries | "Query the users table" |

### **Tool Usage Examples**

```python
# File operations
response = await agent.chat("List all Python files in the current directory")

# Web search
response = await agent.chat("What are the latest AI developments this week?")

# Calculations
response = await agent.chat("If I invest $1000 at 5% annual interest for 10 years, what will it be worth?")
```

---

## 🧠 Memory Configuration

### **Enable Memory**

```python
# Simple memory setup
agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .memory_enabled(True)
    .session_id("user_123")   # Unique session identifier
    .build())
```

### **Advanced Memory Setup**

```python
# Custom memory configuration
agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .memory_enabled(True)
    .memory_backend("chromadb")    # Storage backend
    .memory_limit(1000)           # Max memories to keep
    .session_id("user_123")
    .user_id("john_doe")
    .build())
```

### **Memory Backends**

| Backend | Description | Best For |
|---------|-------------|----------|
| `sqlite` | Local file storage | Development, small projects |
| `chromadb` | Vector database | Semantic search, RAG |
| `redis` | In-memory cache | High-performance applications |
| `bigquery` | Cloud analytics | Large-scale analytics |

---

## 🔍 Provider-Specific Features

### **OpenAI Features**

```python
openai_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .vision_enabled(True)         # Enable image understanding
    .function_calling(True)       # Enable tool calling
    .response_format("json")      # Structured responses
    .build())

# Use vision capabilities
response = await openai_agent.chat(
    "What do you see in this image?",
    image_url="https://example.com/image.jpg"
)
```

### **Anthropic Features**

```python
anthropic_agent = (AgentBuilder()
    .anthropic()
    .model("claude-3-opus")
    .max_tokens(4000)            # Large responses
    .safety_level("medium")      # Safety settings
    .reasoning_mode(True)        # Enhanced reasoning
    .build())

# Long-form analysis
response = await anthropic_agent.chat(
    "Analyze this 50-page document and provide key insights",
    document_content=long_document
)
```

### **Gemini Features**

```python
gemini_agent = (AgentBuilder()
    .gemini()
    .model("gemini-pro")
    .multimodal(True)           # Text, image, video
    .safety_settings("high")    # Safety controls
    .google_search(True)        # Built-in search
    .build())

# Multimodal interaction
response = await gemini_agent.chat(
    "Describe this video and suggest improvements",
    video_url="https://example.com/video.mp4"
)
```

---

## 📊 Monitoring and Health

### **Health Checks**

```python
# Check agent health
health = await agent.health_check()
print(f"Status: {health['status']}")           # online/offline/degraded
print(f"Latency: {health['latency_ms']}ms")
print(f"Error Rate: {health['error_rate']}%")

# Check if agent is ready
if health['status'] == 'online':
    response = await agent.chat("Hello!")
else:
    print("Agent is not available")
```

### **Capabilities Discovery**

```python
# Get agent capabilities
capabilities = await agent.get_capabilities()
print(f"Max Tokens: {capabilities['max_tokens']}")
print(f"Supports Streaming: {capabilities['streaming']}")
print(f"Supports Tools: {capabilities['function_calling']}")
print(f"Supports Vision: {capabilities.get('vision', False)}")
```

---

## 💰 Cost Management

### **Enable Cost Tracking**

```python
# Track usage and costs
agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .cost_tracking(True)
    .cost_limit_daily(10.00)      # $10 daily limit
    .cost_alert_threshold(0.80)   # Alert at 80%
    .build())
```

### **Monitor Usage**

```python
# Get usage statistics
stats = await agent.get_usage_stats()
print(f"Total Requests: {stats['total_requests']}")
print(f"Total Cost: ${stats['total_cost']:.4f}")
print(f"Average Cost per Request: ${stats['avg_cost_per_request']:.4f}")

# Check cost limits
cost_status = await agent.get_cost_status()
if cost_status['approaching_limit']:
    print(f"Warning: {cost_status['usage_percentage']:.1f}% of daily limit used")
```

---

## 🔧 Error Handling

### **Basic Error Handling**

```python
try:
    response = await agent.chat("Hello!")
    print(response)
except Exception as e:
    print(f"Agent error: {e}")
    
    # Check agent health if error occurs
    health = await agent.health_check()
    if health['status'] != 'online':
        print("Agent is experiencing issues")
```

### **Retry Configuration**

```python
# Configure retry behavior
agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .retry_config(
        max_retries=3,
        retry_delay=1.0,
        exponential_backoff=True
    )
    .timeout(30)                # Request timeout
    .build())
```

---

## 🚀 Advanced Usage

### **Multi-Agent Setup**

```python
# Create specialized agents for different tasks
research_agent = (AgentBuilder()
    .anthropic()
    .model("claude-3-opus")
    .system_prompt("You are a research specialist")
    .tools(["web_search", "database"])
    .build())

coding_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .system_prompt("You are a coding expert")
    .tools(["filesystem", "code_interpreter"])
    .build())

# Use agents for specific tasks
research = await research_agent.chat("Research the latest AI developments")
code = await coding_agent.chat("Write a Python function to sort a list")
```

### **Agent Collaboration**

```python
# Agents working together
problem = "Build a web scraper for e-commerce sites"

# Research agent gathers information
research = await research_agent.chat(f"Research best practices for: {problem}")

# Coding agent implements solution
solution = await coding_agent.chat(
    f"Based on this research, implement the solution: {research}\n\nProblem: {problem}"
)
```

---

## 🧪 Testing

### **Mock Agents for Testing**

```python
from langswarm.core.agents.mock_provider import MockProvider

# Create mock agent for testing
mock_agent = (AgentBuilder()
    .mock()
    .model("mock-gpt-4")
    .mock_responses([
        "Hello! I'm a mock agent.",
        "This is response #2",
        "Testing complete!"
    ])
    .build())

# Use like a real agent
response = await mock_agent.chat("Test message")
print(response)  # "Hello! I'm a mock agent."
```

---

## 📚 Best Practices

### **Agent Creation**
- Use descriptive system prompts
- Enable appropriate tools for the task
- Set reasonable token limits
- Enable cost tracking in production

### **Error Handling**
- Always handle agent errors gracefully
- Implement health checks for production
- Configure appropriate retry behavior
- Monitor cost limits to avoid overruns

### **Performance**
- Use streaming for long responses
- Enable memory for context retention
- Cache responses when appropriate
- Monitor latency and error rates

### **Security**
- Set appropriate safety levels
- Validate user inputs
- Monitor for harmful outputs
- Use least-privilege tool access

---

**LangSwarm V2 agents provide a powerful, intuitive way to build AI applications with native provider features, production-ready monitoring, and flexible configuration options.**