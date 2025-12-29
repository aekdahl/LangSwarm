# Troubleshooting: Tool Calls Still Not Working in Streaming

If you're still experiencing issues with tool calls in streaming mode after the fix, follow these steps to diagnose the problem.

## Quick Diagnostic Steps

### Step 1: Enable DEBUG Logging

In your code, enable DEBUG level logging:

```python
import logging

# Set root logger to DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

# Or set specific loggers
logging.getLogger('langswarm.core.agents.base').setLevel(logging.DEBUG)
logging.getLogger('langswarm.core.agents.providers.openai').setLevel(logging.DEBUG)
```

### Step 2: Check What the Logs Say

After enabling DEBUG logging, look for these specific messages in your streaming output:

```
Stream complete - checking for tool calls: last_chunk=True, has_message=True, has_tool_calls=???, tools_enabled=???
```

**Possible scenarios:**

1. **`has_tool_calls=False`** → LLM didn't request any tool calls
   - The query might not need tools
   - Tool definitions might not match the query
   - Try a more explicit query

2. **`tools_enabled=False`** → Tools not enabled in agent config
   - Configuration issue during agent creation
   - See Step 3 below

3. **`has_message=False`** → Final chunk has no message
   - Streaming issue with provider
   - Check OpenAI provider logs

4. **`last_chunk=False`** → No chunks received
   - Streaming not working at all
   - Check API key and connectivity

### Step 3: Verify Agent Configuration

Add this after creating your agent:

```python
agent = await create_openai_agent(
    name="your_agent",
    model="gpt-4o",
    streaming=True,
    tools=["bigquery_vector_search"]  # Your tools
)

# ADD THIS VERIFICATION
print(f"DEBUG Agent Config:")
print(f"  - Streaming enabled: {agent._configuration.streaming_enabled}")
print(f"  - Tools enabled: {agent._configuration.tools_enabled}")
print(f"  - Available tools: {agent._configuration.available_tools}")
print(f"  - Max tool iterations: {agent._configuration.max_tool_iterations}")

# If tools_enabled is False, there's a problem!
if not agent._configuration.tools_enabled:
    print("❌ PROBLEM: Tools are NOT enabled!")
    print("   This means OpenAI will not be told about your tools")
```

### Step 4: Check Tool Registry

Verify your tools are actually registered:

```python
from langswarm.tools.registry import ToolRegistry

registry = ToolRegistry()
tool_ids = list(registry._tools.keys())

print(f"Tools in registry: {tool_ids}")

# Check if your specific tool exists
your_tool = "bigquery_vector_search"
if your_tool in tool_ids:
    print(f"✅ {your_tool} is registered")
    tool = registry.get_tool(your_tool)
    print(f"   Tool object: {tool}")
else:
    print(f"❌ {your_tool} is NOT registered!")
    print(f"   Available: {tool_ids}")
```

### Step 5: Test with a Simple Calculator Tool

If you have complex custom tools, test with a simple built-in tool first:

```python
# Create a simple test agent
test_agent = await create_openai_agent(
    name="test",
    model="gpt-4o",
    system_prompt="You are a helpful assistant. Use tools when appropriate.",
    streaming=True,
    tools=["calculator"]  # Or whatever simple tool you have
)

# Test with a query that DEFINITELY needs the tool
async for chunk in test_agent.stream_chat("What is 12345 * 67890?"):
    if chunk.success and chunk.content:
        print(chunk.content, end="", flush=True)
    
    # Check for tool calls
    if chunk.message and hasattr(chunk.message, 'tool_calls'):
        if chunk.message.tool_calls:
            print(f"\n[Tool call detected: {len(chunk.message.tool_calls)}]")
```

## Common Issues and Solutions

### Issue 1: Tools Not Sent to OpenAI

**Symptoms:**
- `tools_enabled=False` in config
- No tool calls ever detected

**Solution:**
```python
# Make sure you pass tools as a kwarg, not after the agent is created
agent = await create_openai_agent(
    name="agent",
    model="gpt-4o",
    streaming=True,
    tools=["your_tool"]  # ← Pass HERE
)

# DON'T do this after creation (won't work for kwargs-based factory)
# agent.tools = ["your_tool"]  # ❌ Wrong!
```

### Issue 2: Tool Not in Registry

**Symptoms:**
- Agent creation fails with "Tool not found in registry"
- Or tools_enabled=False

**Solution:**
```python
from langswarm.tools.registry import ToolRegistry

# Make sure tools are registered BEFORE creating agent
registry = ToolRegistry()
registry.auto_populate_with_mcp_tools()  # For MCP tools

# Or register manually
# registry.register_tool("my_tool", my_tool_instance)

# THEN create agent
agent = await create_openai_agent(...)
```

### Issue 3: LLM Not Calling Tools

**Symptoms:**
- Config looks correct
- Logs show `has_tool_calls=False`
- But you expect tool calls

**Possible Causes:**
1. **Query is too vague** - Make it more explicit
   ```python
   # Vague: "Tell me about Python"
   # Better: "Search the database for Python documentation"
   ```

2. **Tool description doesn't match query** - Check tool metadata
   ```python
   tool = registry.get_tool("your_tool")
   print(f"Tool description: {tool.metadata.description}")
   # Does this match your query?
   ```

3. **System prompt doesn't encourage tool use**
   ```python
   system_prompt = (
       "You are a helpful assistant with access to tools. "
       "When the user asks for information, USE YOUR TOOLS to search for it. "
       "Do not make up information - always use the tools provided."
   )
   ```

### Issue 4: Tools Detected But Not Executed

**Symptoms:**
- Logs show `has_tool_calls=True`
- But then nothing happens
- No "Executing tools..." message

**This is the original bug!** If you see this:
1. Make sure you have the latest fix from `STREAMING_TOOL_CALL_FIX.md`
2. Check that the file was actually modified (not just marked as modified)
3. Restart your Python process to reload the module

### Issue 5: Tool Execution Fails

**Symptoms:**
- See "Executing tools..." in logs
- But get an error during execution

**Solution:**
- Check the `_handle_tool_calls` logs for error messages
- Verify tool has proper execute() method
- Check tool parameters are correct

## Run the Diagnostic Script

We've provided a diagnostic script to help identify issues:

```bash
# Make sure OPENAI_API_KEY is set
export OPENAI_API_KEY='your-key-here'

# Run the diagnostic
python diagnose_streaming_tools.py
```

This will check:
1. Tool registry status
2. Agent configuration
3. OpenAI API parameters
4. Actual streaming behavior

## Test Scripts Available

1. **`test_simple_streaming_tool.py`** - Simple test with actual OpenAI
2. **`diagnose_streaming_tools.py`** - Comprehensive diagnostics
3. **`test_streaming_tool_fix.py`** - Original fix verification

## Still Not Working?

If you've tried all the above and it's still not working, provide these details:

1. **DEBUG logs** from a streaming call
2. **Agent configuration** (print all config values)
3. **Tool registry contents** (list of tool IDs)
4. **Specific error messages** if any
5. **Your agent creation code** (exact code you're using)

## Quick Reference: What Should Work

This is a working example that SHOULD work after the fix:

```python
import asyncio
import logging
from langswarm.core.agents import create_openai_agent
from langswarm.tools.registry import ToolRegistry

# Enable logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Ensure tools are registered
    registry = ToolRegistry()
    registry.auto_populate_with_mcp_tools()
    
    # Create agent with streaming AND tools
    agent = await create_openai_agent(
        name="test_agent",
        model="gpt-4o",
        system_prompt="You are a helpful assistant. Use tools when needed.",
        streaming=True,
        tools=["bigquery_vector_search"]  # Your tool name
    )
    
    # Verify config
    assert agent._configuration.streaming_enabled, "Streaming not enabled!"
    assert agent._configuration.tools_enabled, "Tools not enabled!"
    assert len(agent._configuration.available_tools) > 0, "No tools!"
    
    # Test
    async for chunk in agent.stream_chat("Search for Python docs in database"):
        if chunk.success and chunk.content:
            print(chunk.content, end="", flush=True)
    print()

asyncio.run(main())
```

If this doesn't work, there's a configuration or environment issue.

---

*Last updated: November 21, 2025*

