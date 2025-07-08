# Smart Tool Auto-Discovery

**Priority 3** | **Status: ✅ Completed** | **Part of LangSwarm Simplification Project**

## Overview

Smart Tool Auto-Discovery eliminates the need for manual tool registration and configuration. LangSwarm now automatically detects available tools based on your environment, provides simplified configuration syntax, and intelligently configures tools with sensible defaults.

## Key Features

### 🔍 Environment-Based Detection
- **Automatic credential detection**: Finds `GITHUB_TOKEN`, `AWS_ACCESS_KEY_ID`, etc.
- **Dependency scanning**: Checks for required Python packages
- **Custom tool discovery**: Scans `./tools/` directory for custom tools
- **Smart recommendations**: Suggests setup steps for missing tools

### ⚡ Simplified Tool Syntax
```yaml
# Before: Full configuration required
tools:
  - id: filesystem
    type: mcpfilesystem
    description: "Local filesystem access"
    local_mode: true
    pattern: "direct"
    methods:
      - read_file: "Read file contents"
      - list_directory: "List directory contents"

# After: Just specify the tool name!
agents:
  - id: my_agent
    behavior: coding
    tools: [filesystem, github]  # ✨ Magic!
```

### 🤖 Zero-Config Integration
- **No tools.yaml required**: Auto-discovers when configuration is missing
- **Behavior-based suggestions**: `coding` behavior → `[filesystem, github]`
- **Intelligent defaults**: Automatically configures `local_mode`, `pattern`, `methods`

## Usage Examples

### Basic Auto-Discovery

```python
from langswarm.core.detection import auto_discover_tools, detect_available_tools

# Discover all available tools
tools = auto_discover_tools()
print(f"Found {len(tools)} tools")

# Discover specific tools
coding_tools = auto_discover_tools(["filesystem", "github"])

# Get environment detection results
results = detect_available_tools()
print(f"Available: {results['environment_summary']['total_available']} tools")
```

### Simplified Configuration

```yaml
# langswarm.yaml - Ultra-simple configuration
version: "1.0"
agents:
  - id: coding_assistant
    behavior: coding
    tools: [filesystem, github]  # Expands automatically!
  
  - id: researcher  
    behavior: research
    # No tools specified - will auto-discover based on behavior!
```

### Zero-Config Agent Creation

```python
from langswarm.core.factory.agents import AgentFactory

# Create agent with auto-discovered tools
agent = AgentFactory.create_simple(
    name="smart_assistant",
    behavior="coding"
    # No tools specified - auto-discovers filesystem, github if available
)
```

## Tool Presets

Built-in tool presets with smart defaults:

| Tool | Environment Detection | Pattern | Dependencies |
|------|---------------------|---------|--------------|
| **filesystem** | Always available | `direct` | None |
| **github** | `GITHUB_TOKEN` or `GITHUB_PAT` | `intent` | `requests`, `pygithub` |
| **dynamic_forms** | Always available | `direct` | None |
| **aws** | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | `intent` | `boto3`, `botocore` |
| **gcp** | `GOOGLE_APPLICATION_CREDENTIALS` | `intent` | `google-cloud-core` |
| **docker** | `DOCKER_HOST` (optional) | `intent` | `docker` |

## Environment Detection

The system automatically detects:

### ✅ Available Tools
```bash
🔍 Detecting environment for Smart Tool Auto-Discovery...
   ✅ filesystem: Available
   ✅ dynamic_forms: Available
   ✅ github: Available
   ❌ aws: Missing AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
   ❌ gcp: Missing google-cloud-core
```

### 💡 Setup Recommendations
```bash
💡 Setup Recommendations:
   • To enable aws: Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY | Install: pip install boto3 botocore
   • To enable gcp: Set environment variables: GOOGLE_APPLICATION_CREDENTIALS | Install: pip install google-cloud-core google-auth
```

## Custom Tool Support

### Creating Custom Tools

1. **Create tools directory**:
   ```bash
   mkdir ./tools
   ```

2. **Add custom tool**:
   ```python
   # ./tools/my_tool.py
   class MyCustomTool:
       def __init__(self):
           self.id = "my_custom_tool"
           self.type = "custom"
           self.description = "My custom functionality"
       
       def run(self, params):
           return "Custom tool response"
   ```

3. **Auto-discovery finds it**:
   ```python
   tools = auto_discover_tools()
   # Includes your custom tool automatically!
   ```

## Behavior-Based Tool Suggestions

Different behaviors get different tool recommendations:

```python
from langswarm.core.config import LangSwarmConfigLoader

loader = LangSwarmConfigLoader()

# Get tool suggestions for different behaviors
coding_tools = loader.suggest_tools_for_behavior("coding")
# Returns: ["filesystem", "github"]

research_tools = loader.suggest_tools_for_behavior("research") 
# Returns: ["filesystem", "github"]

support_tools = loader.suggest_tools_for_behavior("support")
# Returns: ["dynamic_forms"]
```

## Migration Guide

### From Manual Tool Configuration

**Before (Manual)**:
```yaml
# tools.yaml
tools:
  - id: filesystem
    type: mcpfilesystem
    description: "Filesystem access"
    local_mode: true
    pattern: "direct"
    methods:
      - read_file: "Read file contents"
      - list_directory: "List directory contents"

# agents.yaml  
agents:
  - id: my_agent
    tools: [filesystem]
```

**After (Auto-Discovery)**:
```yaml
# langswarm.yaml
version: "1.0"
agents:
  - id: my_agent
    behavior: coding
    tools: [filesystem]  # Auto-expands to full configuration!
```

### From Zero Tools to Auto-Discovery

**Before**:
```yaml
agents:
  - id: basic_agent
    model: gpt-4o
    # No tools - limited functionality
```

**After**:
```yaml
agents:
  - id: smart_agent
    behavior: coding
    # No tools specified - auto-discovers based on behavior and environment!
```

## API Reference

### Core Functions

#### `auto_discover_tools(requested_tools=None)`
Auto-discover and configure tools based on environment.

**Parameters:**
- `requested_tools` (List[str], optional): Specific tools to discover. If None, discovers all available.

**Returns:**
- `List[Dict[str, Any]]`: Tool configurations ready for use

#### `detect_available_tools()`
Detect what tools are available in the current environment.

**Returns:**
- `Dict[str, Any]`: Detection results with available tools, missing credentials, and recommendations

#### `get_tool_recommendations(use_case)`
Get tool recommendations based on use case description.

**Parameters:**
- `use_case` (str): Description of what you want to accomplish

**Returns:**
- `List[str]`: Recommended tool IDs

### Configuration Methods

#### `LangSwarmConfigLoader.get_available_tools_info()`
Get information about available tools for user guidance.

#### `LangSwarmConfigLoader.suggest_tools_for_behavior(behavior)`
Suggest tools based on agent behavior.

## Advanced Features

### Environment-Specific Configuration

Tools automatically adapt to your environment:

```python
# If GITHUB_TOKEN is set
github_config = {
    "id": "github",
    "type": "mcpgithubtool", 
    "local_mode": True,
    "pattern": "intent",
    "base_url": "https://api.github.com",
    "timeout": 30
}

# If AWS credentials are available
aws_config = {
    "id": "aws",
    "type": "mcpaws",
    "local_mode": True,
    "pattern": "intent", 
    "region": "us-east-1"
}
```

### Tool Status Validation

```python
from langswarm.core.detection import EnvironmentDetector

detector = EnvironmentDetector()

# Check specific tool availability
preset = detector.get_tool_preset("github")
status = detector._check_tool_availability(preset)

if status["available"]:
    print("GitHub tool ready to use!")
else:
    print(f"Missing: {status['missing_env_vars'] + status['missing_dependencies']}")
```

## Best Practices

### 1. **Use Behavior-Driven Configuration**
```yaml
# Good: Behavior drives tool selection
agents:
  - id: coding_assistant
    behavior: coding  # Auto-suggests filesystem, github
```

### 2. **Environment-First Approach** 
```bash
# Set up environment first
export GITHUB_TOKEN=your_token_here
export AWS_ACCESS_KEY_ID=your_key_here

# Then let LangSwarm auto-discover
```

### 3. **Mix Auto-Discovery with Explicit Tools**
```yaml
agents:
  - id: hybrid_agent
    behavior: coding
    tools: [filesystem, github, my_custom_tool]  # Mix built-in + custom
```

### 4. **Check Available Tools**
```python
# Always good to check what's available
from langswarm.core.detection import detect_available_tools

results = detect_available_tools()
print("Available tools:", [t["id"] for t in results["available_tools"]])
```

## Troubleshooting

### Common Issues

#### ❌ "Tool 'X' not available: Missing Y"
**Solution**: Install missing dependencies or set environment variables
```bash
# For GitHub
export GITHUB_TOKEN=your_token

# For AWS  
pip install boto3 botocore
export AWS_ACCESS_KEY_ID=your_key
```

#### ❌ "Unknown tool preset: 'my_tool'"
**Solution**: Tool name not recognized. Check available presets:
```python
from langswarm.core.detection import detect_available_tools
results = detect_available_tools()
available = [t["id"] for t in results["available_tools"]]
print("Available tools:", available)
```

#### ❌ "Zero-config functionality not available"
**Solution**: Install required dependencies:
```bash
pip install psutil requests
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now auto-discovery will show detailed information
from langswarm.core.detection import auto_discover_tools
tools = auto_discover_tools()
```

## Examples

See `demos/demo_smart_tool_auto_discovery.py` for comprehensive examples of all features.

## Related Features

- **[Zero-Config Agents](02-zero-config-agents.md)**: Simplified agent creation
- **[Single Configuration File](01-single-configuration-file.md)**: Unified configuration
- **[Intent-Based Tool Calling](../INTENT_BASED_TOOL_CALLING.md)**: Natural language tool usage

---

**Next Priority**: [Advanced Agent Behaviors](04-advanced-agent-behaviors.md) 