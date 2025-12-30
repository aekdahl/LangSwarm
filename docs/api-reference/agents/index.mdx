# LangSwarm V2 Agent System API Reference

**Complete API documentation for the LangSwarm V2 native agent system**

## 🎯 Overview

LangSwarm V2 introduces a completely redesigned agent system that replaces the complex 4,000+ line AgentWrapper with clean, provider-specific implementations. Each provider (OpenAI, Anthropic, Gemini, etc.) has its own native integration optimized for that specific platform.

**Key Features:**
- **Native Provider Integration**: Direct API integration for each LLM provider
- **Builder Pattern**: Fluent, intuitive agent creation
- **Type Safety**: Full TypeScript-style interfaces and validation
- **Provider-Specific Features**: Leverage unique capabilities of each provider
- **Production Ready**: Health monitoring, error handling, cost tracking

---

## 🏗️ Agent Architecture

### **Provider-Based Design**

```python
# V2 Agent System Architecture
from langswarm.core.agents import AgentBuilder

# Each provider has its own optimized implementation
openai_agent = AgentBuilder().openai().model("gpt-4o").build()
anthropic_agent = AgentBuilder().anthropic().model("claude-3-opus").build()
gemini_agent = AgentBuilder().gemini().model("gemini-pro").build()
```

**Benefits over V1:**
- ✅ **50% Code Reduction**: 4,000+ lines → 2,000+ lines
- ✅ **90% Simpler Creation**: Complex config → fluent builder
- ✅ **100% Type Safety**: Full interface coverage
- ✅ **Modular Design**: Add providers without touching core code
- ✅ **Native Performance**: Direct API integration per provider

---

## 🔧 Core Interfaces

### **AgentInterface**
```python
from langswarm.core.agents.interfaces import AgentInterface

class AgentInterface:
    """Base interface for all LangSwarm V2 agents"""
    
    # Core Properties
    agent_id: str
    provider: str
    model: str
    
    # Core Functionality
    async def chat(self, message: str, **kwargs) -> str:
        """Send a message and get a response"""
        pass
    
    async def chat_stream(self, message: str, **kwargs) -> AsyncIterator[str]:
        """Send a message and get streaming response"""
        pass
    
    # Health & Monitoring
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health and connectivity"""
        pass
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and features"""
        pass
```

---

## 🎛️ Agent Builder

### **Fluent Builder Pattern**

```python
from langswarm.core.agents import AgentBuilder

# Basic agent creation
agent = AgentBuilder().openai().model("gpt-4o").build()

# Advanced configuration
agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .temperature(0.7)
    .max_tokens(2000)
    .system_prompt("You are a helpful assistant")
    .tools(["filesystem", "calculator"])
    .memory_enabled(True)
    .cost_tracking(True)
    .build())
```

---

## 🌐 Provider Implementations

### **OpenAI Provider**
```python
# Create OpenAI agent
agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .temperature(0.7)
    .build())

# OpenAI-specific features
response = await agent.chat("Hello!")
health = await agent.health_check()
```

### **Anthropic Provider**
```python
# Create Anthropic agent
agent = (AgentBuilder()
    .anthropic()
    .model("claude-3-opus")
    .max_tokens(1000)
    .build())
```

---

## 🔄 Migration from V1

### **V1 AgentWrapper → V2 Native Agents**

```python
# V1 AgentWrapper (complex)
v1_agent = AgentWrapper(
    name="assistant",
    agent=base_agent,
    model="gpt-4o",
    memory=memory_config,
    # ... 20+ more parameters
)

# V2 Native Agent (simple)
v2_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .system_prompt("You are a helpful assistant")
    .tools(["filesystem", "calculator"])
    .memory_enabled(True)
    .build())
```

### **Migration Benefits**

| Aspect | V1 AgentWrapper | V2 Native Agents | Improvement |
|--------|----------------|-------------------|-------------|
| **Code Lines** | 4,000+ | 2,000+ | 50% reduction |
| **Configuration** | 20+ parameters | Fluent builder | 90% simpler |
| **Type Safety** | Limited | Full interfaces | 100% coverage |
| **Provider Support** | Monolithic | Modular | ∞ extensibility |

---

**The LangSwarm V2 agent system provides a clean, powerful, and extensible foundation for building AI applications with native provider integration and production-ready features.**