# LangSwarm Usage Guide for LLMs

## Why LLMs Have Difficulty Using LangSwarm

After thorough analysis, I've identified the key issues that make LangSwarm challenging for LLMs to use effectively:

### 1. **Complex Import Paths**
- **Issue**: Deep nested imports like `langswarm.core.agents.providers.openai`
- **Impact**: LLMs struggle with remembering and correctly typing long import paths
- **Solution**: Use simple top-level imports

### 2. **Multiple Ways to Do the Same Thing**
- **Issue**: 4+ different methods to create agents:
  - `create_openai_agent()`
  - `AgentBuilder().openai().build()`
  - `OpenAIProvider + AgentConfiguration`
  - YAML configuration loading
- **Impact**: Choice paralysis and inconsistent usage patterns
- **Solution**: Standardize on one primary method

### 3. **Configuration Complexity**
- **Issue**: 
  - AgentConfig has 18+ parameters
  - Example YAML config is 110+ lines
  - Environment variable validation is strict
- **Impact**: LLMs get overwhelmed by options and fail on validation
- **Solution**: Use minimal configurations with smart defaults

### 4. **Dependency Management Issues**
- **Issue**: Missing optional dependencies cause silent failures or confusing errors
- **Impact**: LLMs can't easily diagnose what's missing
- **Solution**: Clear error messages and dependency checking

### 5. **Strict Environment Variable Validation**
- **Issue**: Configuration loading fails if environment variables aren't set
- **Impact**: LLMs can't test configurations without full setup
- **Solution**: Provide fallback modes or better error handling

## Recommended Simple Setup for LLMs

### Step 1: Prerequisites
```bash
# Install LangSwarm
pip install langswarm

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"
```

### Step 2: Simple Agent Creation (Recommended Method)
```python
import asyncio
from langswarm.core.agents import create_openai_agent

async def main():
    # Create agent with minimal configuration
    agent = create_openai_agent(
        model="gpt-3.5-turbo",  # Cost-effective for testing
        api_key="your-openai-api-key"  # Or use environment variable
    )
    
    # Use the agent
    response = await agent.chat("Hello! How are you?")
    print(response.content)

# Run the example
asyncio.run(main())
```

### Step 3: Builder Pattern (For More Control)
```python
from langswarm.core.agents import AgentBuilder

# More advanced configuration
agent = (AgentBuilder()
         .openai()  # Uses OPENAI_API_KEY environment variable
         .model("gpt-3.5-turbo")
         .system_prompt("You are a helpful assistant")
         .temperature(0.7)
         .build())

response = await agent.chat("What can you help me with?")
```

### Step 4: Programmatic Configuration (Avoid YAML)
```python
from langswarm.core.config import LangSwarmConfig
from langswarm.core.config.schema import AgentConfig, MemoryConfig, ProviderType

# Create configuration in code instead of YAML
config = LangSwarmConfig(
    version="2.0",
    name="Simple Setup",
    agents=[
        AgentConfig(
            id="assistant",
            provider=ProviderType.OPENAI,
            model="gpt-3.5-turbo",
            system_prompt="You are a helpful assistant."
        )
    ],
    memory=MemoryConfig(
        backend="sqlite",  # No external dependencies
        config={"db_path": "langswarm.db"}
    )
)
```

## What Works Well

✅ **Core functionality is solid**
- Basic imports work reliably
- Agent creation and chat functionality works
- Builder pattern is intuitive
- Programmatic configuration is flexible

✅ **Good architecture**
- Clean interfaces and abstractions
- Provider-specific implementations
- Modular design

## Key Recommendations for LLM Usage

### 1. **Use Simple Entry Points**
```python
# ✅ GOOD - Simple and clear
from langswarm.core.agents import create_openai_agent

# ❌ AVOID - Too complex
from langswarm.core.agents.providers.openai import OpenAIProvider
```

### 2. **Avoid YAML Configuration Initially**
```python
# ✅ GOOD - Programmatic configuration
config = LangSwarmConfig(...)

# ❌ AVOID - YAML files (initially)
config = load_config("complex_config.yaml")
```

### 3. **Use Smart Defaults**
```python
# ✅ GOOD - Minimal required parameters
agent = create_openai_agent(model="gpt-3.5-turbo")

# ❌ AVOID - Too many parameters
agent = AgentConfiguration(
    provider=ProviderType.OPENAI,
    model="gpt-3.5-turbo", 
    api_key=api_key,
    base_url=None,
    system_prompt=None,
    max_tokens=None,
    temperature=0.7,
    timeout=30,
    # ... 10+ more parameters
)
```

### 4. **Handle Dependencies Gracefully**
```python
# ✅ GOOD - Check prerequisites first
def check_prerequisites():
    try:
        import langswarm
        import openai
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False

if check_prerequisites():
    # Proceed with LangSwarm usage
    pass
```

## Complete Working Example

Here's a complete, minimal example that LLMs can use reliably:

```python
#!/usr/bin/env python3
"""
Minimal LangSwarm Example for LLMs
"""
import asyncio
import os

async def simple_langswarm_example():
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    try:
        # Import and create agent
        from langswarm.core.agents import create_openai_agent
        
        agent = create_openai_agent(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Use the agent
        response = await agent.chat("Hello! Please introduce yourself briefly.")
        print(f"Agent: {response.content}")
        
        print("✅ LangSwarm is working correctly!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(simple_langswarm_example())
```

## Troubleshooting Common Issues

### Issue: Import Errors
```python
# If you get import errors, check:
import sys
print("Python version:", sys.version)

try:
    import langswarm
    print("✅ LangSwarm available")
except ImportError:
    print("❌ Install with: pip install langswarm")
```

### Issue: API Key Problems
```python
import os

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Set API key with: export OPENAI_API_KEY='your-key'")
else:
    print("✅ API key found")
```

### Issue: Configuration Loading Fails
```python
# Instead of YAML, use programmatic configuration:
from langswarm.core.config import LangSwarmConfig
from langswarm.core.config.schema import AgentConfig, ProviderType

config = LangSwarmConfig(
    version="2.0",
    agents=[AgentConfig(
        id="assistant",
        provider=ProviderType.OPENAI,
        model="gpt-3.5-turbo"
    )]
)
```

## Summary

LangSwarm is a powerful framework, but its complexity can overwhelm LLMs. The key to successful LLM usage is:

1. **Start simple** - Use `create_openai_agent()`
2. **Avoid YAML initially** - Use programmatic configuration
3. **Use minimal parameters** - Rely on smart defaults
4. **Check prerequisites** - Validate dependencies and API keys
5. **Handle errors gracefully** - Provide clear error messages

By following these guidelines, LLMs can successfully use LangSwarm for building multi-agent AI systems.
