# LangSwarm V1 to V2 Agent Migration Guide

**Complete guide for migrating from V1's complex AgentWrapper to V2's native provider system**

## 🎯 Overview

LangSwarm V2 completely replaces the complex 4,000+ line AgentWrapper with clean, provider-specific implementations. This guide helps you migrate your agent usage from V1 to V2, taking advantage of the simplified interface and enhanced capabilities.

**Migration Benefits:**
- **50% Code Reduction**: From 4,000+ lines to 2,000+ lines
- **90% Simpler Creation**: Complex configuration to fluent builder
- **100% Type Safety**: Full interface coverage
- **Native Provider Features**: Direct API integration per provider
- **Production Ready**: Health monitoring, cost tracking, error handling

---

## 🔄 Migration Strategy

### **Phase 1: Backward Compatibility (Immediate)**
V2 maintains compatibility adapters for V1 AgentWrapper usage during transition.

```python
# V1 AgentWrapper continues working in V2
from langswarm.core.wrappers import AgentWrapper  # Still works

agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    # ... existing V1 configuration
)
```

### **Phase 2: Enhanced Usage (Gradual)**
Start using V2 features while maintaining V1 patterns.

```python
# Mixed V1/V2 usage
from langswarm.core.agents import AgentBuilder

# Create V2 agent with V1-style error handling
v2_agent = AgentBuilder().openai().model("gpt-4o").build()

# Use with V1 error patterns
try:
    response = await v2_agent.chat("Hello")
except Exception as e:
    handle_v1_error(e)  # Existing error handling
```

### **Phase 3: Full V2 Migration (Recommended)**
Migrate to V2 native agents for optimal experience.

```python
# Pure V2 implementation
from langswarm.core.agents import AgentBuilder

agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .system_prompt("You are a helpful assistant")
    .tools(["filesystem", "calculator"])
    .memory_enabled(True)
    .build())
```

---

## 📊 Migration Comparison

### **V1 AgentWrapper vs V2 Native Agents**

| Aspect | V1 AgentWrapper | V2 Native Agents | Migration Impact |
|--------|----------------|-------------------|------------------|
| **Configuration** | 20+ parameters | Fluent builder | 90% complexity reduction |
| **Code Lines** | 4,000+ lines | 2,000+ lines | 50% code reduction |
| **Provider Support** | Monolithic wrapper | Native providers | Better performance |
| **Type Safety** | Limited | Full interfaces | Better development experience |
| **Testing** | Difficult | Mock providers | 10x easier testing |
| **Error Handling** | Generic | Provider-specific | Better error messages |
| **Performance** | Wrapper overhead | Direct API calls | Faster execution |

---

## 🛠️ Detailed Migration Steps

### **Step 1: Assess Current Usage**

**Find all AgentWrapper instances:**
```bash
# Search for AgentWrapper usage in your codebase
grep -r "AgentWrapper" your_project/
grep -r "from langswarm.core.wrappers" your_project/
```

**Common V1 Patterns:**
```python
# Pattern 1: Basic AgentWrapper
agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    agent_type="conversational"
)

# Pattern 2: Complex configuration
agent = AgentWrapper(
    name="assistant",
    agent=base_agent,
    model="gpt-4o",
    memory=memory_config,
    system_prompt=system_prompt,
    tool_registry=tool_registry,
    response_mode="structured",
    # ... many more parameters
)

# Pattern 3: Memory integration
agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    memory_adapter=memory_adapter,
    memory_summary_adapter=summary_adapter,
    session_manager=session_manager
)
```

### **Step 2: Convert to V2 Builder Pattern**

#### **Basic Migration**

```python
# V1 AgentWrapper (before)
from langswarm.core.wrappers import AgentWrapper

v1_agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    agent_type="conversational"
)

# V2 Native Agent (after)
from langswarm.core.agents import AgentBuilder

v2_agent = (AgentBuilder()
    .openai()  # Provider selection
    .model("gpt-4o")
    .build())
```

#### **Complex Configuration Migration**

```python
# V1 Complex Configuration (before)
from langswarm.core.wrappers import AgentWrapper

v1_agent = AgentWrapper(
    name="coding_assistant",
    agent=base_agent,
    model="gpt-4o",
    memory=memory_config,
    agent_type="conversational",
    system_prompt="You are a coding expert",
    tool_registry=tool_registry,
    response_mode="structured",
    context_limit=4000,
    streaming_config=streaming_config,
    session_manager=session_manager,
    enable_hybrid_sessions=True,
    allow_middleware=True
)

# V2 Simplified Configuration (after)
from langswarm.core.agents import AgentBuilder

v2_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .system_prompt("You are a coding expert")
    .tools(["filesystem", "code_interpreter"])  # Replaces tool_registry
    .memory_enabled(True)                       # Replaces memory config
    .session_id("user_123")                     # Replaces session_manager
    .max_tokens(4000)                          # Replaces context_limit
    .cost_tracking(True)                       # New V2 feature
    .build())
```

#### **Memory System Migration**

```python
# V1 Memory Configuration (before)
memory_config = {
    "adapter": "langchain",
    "backend": "chromadb",
    "config": {
        "persist_directory": "./memory",
        "collection_name": "conversations"
    }
}

v1_agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    memory=memory_config,
    memory_adapter=memory_adapter,
    session_manager=session_manager
)

# V2 Memory Configuration (after)
v2_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .memory_enabled(True)
    .memory_backend("chromadb")
    .session_id("user_123")
    .user_id("john_doe")
    .build())
```

---

## 🔧 Feature Migration

### **Tool Integration**

```python
# V1 Tool Registry (before)
from langswarm.synapse.registry.tools import ToolRegistry

tool_registry = ToolRegistry()
tool_registry.register("filesystem", FileSystemTool())
tool_registry.register("calculator", CalculatorTool())

v1_agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    tool_registry=tool_registry
)

# V2 Tool Integration (after)
v2_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .tools(["filesystem", "calculator"])  # Auto-discovery
    .tool_choice("auto")
    .build())
```

### **Response Modes**

```python
# V1 Response Modes (before)
v1_agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    response_mode="structured"  # or "streaming"
)

# V2 Response Handling (after)
v2_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .build())

# Streaming in V2
async for chunk in v2_agent.chat_stream("Tell me a story"):
    print(chunk, end="", flush=True)

# Structured responses via model parameters
structured_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .response_format("json")
    .build())
```

### **Session Management**

```python
# V1 Session Management (before)
from langswarm.core.session import SessionManager

session_manager = SessionManager(
    backend="sqlite",
    session_id="user_123"
)

v1_agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    session_manager=session_manager,
    enable_hybrid_sessions=True
)

# V2 Session Management (after)
v2_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .session_id("user_123")
    .user_id("john_doe")
    .memory_enabled(True)  # Automatic session persistence
    .build())
```

---

## 🌐 Provider-Specific Migration

### **OpenAI Migration**

```python
# V1 OpenAI Configuration (before)
v1_agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    agent_type="conversational",
    config={
        "openai_api_key": "sk-...",
        "temperature": 0.7,
        "max_tokens": 2000
    }
)

# V2 OpenAI Configuration (after)
v2_agent = (AgentBuilder()
    .openai()
    .model("gpt-4o")
    .temperature(0.7)
    .max_tokens(2000)
    .config({
        "api_key": "sk-...",  # Or use environment variable
        "timeout": 30
    })
    .build())
```

### **Anthropic Migration**

```python
# V1 Anthropic via AgentWrapper (before)
v1_agent = AgentWrapper(
    name="assistant",
    model="claude-3-opus",
    agent_type="conversational",
    config={
        "anthropic_api_key": "sk-ant-...",
        "max_tokens": 4000
    }
)

# V2 Native Anthropic (after)
v2_agent = (AgentBuilder()
    .anthropic()
    .model("claude-3-opus")
    .max_tokens(4000)
    .safety_level("medium")  # Anthropic-specific feature
    .reasoning_mode(True)    # Enhanced reasoning
    .build())
```

---

## 🧪 Testing Migration

### **V1 Testing Pattern**

```python
# V1 Testing (before)
import pytest
from langswarm.core.wrappers import AgentWrapper

class TestAgent:
    def test_agent_creation(self):
        agent = AgentWrapper(
            name="test_agent",
            model="gpt-4o"
        )
        assert agent.name == "test_agent"
        assert agent.model == "gpt-4o"
    
    def test_agent_chat(self):
        agent = AgentWrapper(name="test", model="gpt-4o")
        response = agent.chat("Hello")
        assert isinstance(response, str)
```

### **V2 Testing Pattern**

```python
# V2 Testing (after)
import pytest
from langswarm.core.agents import AgentBuilder

class TestAgent:
    async def test_agent_creation(self):
        agent = (AgentBuilder()
            .openai()
            .model("gpt-4o")
            .build())
        
        assert agent.provider == "openai"
        assert agent.model == "gpt-4o"
        
        # V2 health check
        health = await agent.health_check()
        assert health['status'] == 'online'
    
    async def test_agent_chat(self):
        agent = (AgentBuilder()
            .mock()  # Use mock provider for testing
            .model("mock-gpt-4")
            .mock_responses(["Hello! Mock response."])
            .build())
        
        response = await agent.chat("Hello")
        assert response == "Hello! Mock response."
    
    async def test_agent_capabilities(self):
        agent = (AgentBuilder()
            .openai()
            .model("gpt-4o")
            .build())
        
        capabilities = await agent.get_capabilities()
        assert 'max_tokens' in capabilities
        assert 'streaming' in capabilities
```

---

## 🔄 Compatibility Adapters

### **Automatic V1 Wrapper Compatibility**

```python
# V2 provides automatic compatibility for V1 patterns
from langswarm.adapters import wrap_v1_agent

# Your existing V1 agent
v1_agent = AgentWrapper(
    name="assistant",
    model="gpt-4o",
    memory=memory_config
)

# Automatically wrap for V2 features
v2_wrapped = wrap_v1_agent(v1_agent)

# Now supports V2 features
health = await v2_wrapped.health_check()
capabilities = await v2_wrapped.get_capabilities()
```

### **Gradual Migration Helper**

```python
from langswarm.migration import migrate_agent_config

# Convert V1 config to V2 builder
v1_config = {
    "name": "assistant",
    "model": "gpt-4o",
    "memory": memory_config,
    "tool_registry": tool_registry,
    "system_prompt": "You are helpful"
}

# Get equivalent V2 builder
v2_builder = migrate_agent_config(v1_config)
v2_agent = v2_builder.build()
```

---

## 📋 Migration Checklist

### **Pre-Migration Assessment**
- [ ] Inventory all AgentWrapper instances in codebase
- [ ] Document current configurations and features used
- [ ] Identify custom tools and memory configurations
- [ ] Plan testing strategy for migrated agents

### **Migration Implementation**
- [ ] Convert AgentWrapper to AgentBuilder pattern
- [ ] Update model and provider configurations
- [ ] Migrate tool registrations to V2 tool system
- [ ] Update memory and session configurations
- [ ] Replace response mode configurations

### **Testing and Validation**
- [ ] Test agent creation and basic functionality
- [ ] Verify tool integration works correctly
- [ ] Test memory and session persistence
- [ ] Validate performance improvements
- [ ] Test error handling and health checks

### **Production Deployment**
- [ ] Update environment configurations
- [ ] Monitor agent health and performance
- [ ] Verify cost tracking and limits
- [ ] Test backup and recovery procedures

---

## 🚀 Migration Benefits Validation

### **Performance Improvements**

```python
# Measure performance improvements
import time

# V1 timing
start = time.time()
v1_response = v1_agent.chat("Hello")
v1_time = time.time() - start

# V2 timing
start = time.time()
v2_response = await v2_agent.chat("Hello")
v2_time = time.time() - start

print(f"V1 time: {v1_time:.3f}s")
print(f"V2 time: {v2_time:.3f}s")
print(f"Improvement: {((v1_time - v2_time) / v1_time * 100):.1f}%")
```

### **Feature Comparison**

```python
# V2 features not available in V1
health = await v2_agent.health_check()
capabilities = await v2_agent.get_capabilities()
usage_stats = await v2_agent.get_usage_stats()

print("V2 Exclusive Features:")
print(f"Health Status: {health['status']}")
print(f"Latency: {health['latency_ms']}ms")
print(f"Cost Tracking: ${usage_stats['total_cost']:.4f}")
```

---

## 🎯 Success Metrics

### **Migration Completeness**
- [ ] **100% AgentWrapper Replacement**: All V1 agents migrated to V2
- [ ] **Feature Parity**: All V1 functionality preserved or enhanced
- [ ] **Performance Improvement**: Measurable speed improvements
- [ ] **Code Simplification**: Reduced configuration complexity

### **Enhanced Capabilities**
- [ ] **Native Provider Features**: Leveraging provider-specific capabilities
- [ ] **Health Monitoring**: Production-ready health checks
- [ ] **Cost Tracking**: Usage and cost visibility
- [ ] **Better Error Handling**: Provider-specific error messages

### **Developer Experience**
- [ ] **Simplified Creation**: Fluent builder pattern adoption
- [ ] **Better Testing**: Mock provider usage
- [ ] **Type Safety**: Full interface coverage
- [ ] **Easier Debugging**: Clear error messages and health status

---

**The V2 agent migration transforms complex, monolithic agent creation into a simple, powerful, and maintainable system while preserving all functionality and adding production-ready features.**