## Intent-Based Tool Workflows

**You can use tools in two ways:**

### 1. Direct Tool Calls (when you know exact parameters):
```json
{
  "response": "I'll read that specific file for you.",
  "mcp": {
    "tool": "filesystem",
    "method": "read_file",
    "params": {"path": "/etc/config.json"}
  }
}
```

### 2. Intent-Based Calls (when expressing what you want to accomplish):
```json
{
  "response": "I need to find and read the configuration file to analyze the settings.",
  "mcp": {
    "tool": "filesystem", 
    "intent": "read configuration file",
    "context": "analyze configuration settings for troubleshooting"
  }
}
```

**Intent-Based Benefits:**
- The tool workflow can ask for clarification if needed
- Multiple agents work together to interpret your intent
- Automatic retry and error recovery
- Progressive refinement of unclear requests

**When to use Intent-Based:**
- Complex or multi-step operations
- When you're not sure of exact parameters
- When the tool should handle clarification internally
- For exploratory or analytical tasks 