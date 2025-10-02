# 🔧 Solution: Enhanced MCP Patterns with YAML Configuration

## The Problem

If you're getting the error:
```
MCP tool filesystem error: Tool 'filesystem' not found in registry
```

The issue is that **your agent doesn't have the tool registered in its tool registry**.

## The Solution

The key insight: **Your agent MUST list the tools it uses in the `tools` field of your `agents.yaml`!**

### ✅ Correct Configuration

#### 1. `tools.yaml` - Define your MCP tools
```yaml
tools:
  - id: filesystem
    type: mcpfilesystem
    description: "Local filesystem MCP tool for reading files and listing directories"
    local_mode: true
    pattern: "direct"
    methods:
      - read_file: "Read file contents"
      - list_directory: "List directory contents"
```

#### 2. `agents.yaml` - **CRITICAL: Include tools list**
```yaml
agents:
  - id: filesystem_agent
    agent_type: openai
    model: gpt-4o-mini
    system_prompt: |
      You are a helpful assistant with access to the local filesystem.
      
      Available tools:
      - filesystem: Local file operations
        Methods: read_file(path), list_directory(path)
      
      Use the direct MCP pattern for filesystem operations:
      {
        "mcp": {
          "tool": "filesystem",
          "method": "read_file",
          "params": {"path": "/path/to/file"}
        }
      }
    tools:
      - filesystem  # ← THIS IS THE KEY! List the tools your agent uses
```

#### 3. `workflows.yaml` - Use the agent
```yaml
workflows:
  simple_filesystem_workflow:
    - id: filesystem_step
      steps:
        - id: agent_call
          agent: filesystem_agent
          input: ${context.user_input}
          output:
            to: user
```

## How It Works

1. **`LangSwarmConfigLoader` loads tools** from `tools.yaml` and creates tool instances
2. **`_assign_registries()` looks for `tools: [filesystem]`** in your agent configuration
3. **Creates a `ToolRegistry`** and registers the specified tools
4. **Passes `tool_registry` to `AgentWrapper`** which makes it available to middleware
5. **Middleware can now find the tool** when you make MCP calls

## Test It

Run the test script to verify everything works:

```bash
python test_filesystem_example.py
```

This will:
- ✅ Load your YAML configuration
- ✅ Verify tools are registered correctly  
- ✅ Test direct MCP patterns
- ✅ Show you exactly what's working

## Key Takeaways

🔑 **The `tools` list in `agents.yaml` is mandatory**
💡 **No manual coding required - pure YAML configuration**
🚀 **Enhanced MCP patterns work seamlessly with existing config system**
⚡ **Local mode provides zero-latency tool calls**

The error occurs because the middleware can't find the tool in the agent's tool registry. By adding `tools: [filesystem]` to your agent configuration, the config loader automatically registers the tool for that agent. 