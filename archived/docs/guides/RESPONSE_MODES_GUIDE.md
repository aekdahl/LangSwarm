# LangSwarm Response Modes Guide

## Overview

When an agent provides both a user response AND a tool call in the same JSON structure, LangSwarm now supports two different modes for handling this situation:

```json
{
  "response": "I'll check that configuration file for you",
  "mcp": {
    "tool": "filesystem",
    "method": "read_file",
    "params": {"path": "/tmp/config.json"}
  }
}
```

## Response Modes

### 🔄 Mode 1: `"integrated"` (Default)

**Behavior:** The user response is combined with tool results before being shown to the user.

**Flow:**
1. Agent provides: `{"response": "I'll check that file", "mcp": {...}}`
2. Tool executes: `filesystem.read_file()` 
3. Agent gets context: `"I'll check that file\n\nTool result: {file_contents}"`
4. Agent provides final response incorporating both
5. **User sees:** Final integrated response like *"I checked your configuration file. It contains database settings..."*

**User Experience:**
- ✅ **Concise** - One complete answer
- ✅ **Integrated** - Tool results naturally incorporated 
- ❌ **No visibility** into agent's "thinking process"

**Configuration:**
```yaml
agents:
  - id: my_agent
    response_mode: "integrated"  # Default
```

### 📊 Mode 2: `"streaming"`

**Behavior:** The user sees the immediate response, then tool results separately.

**Flow:**
1. Agent provides: `{"response": "I'll check that file", "mcp": {...}}`
2. **User sees immediately:** *"I'll check that configuration file for you"*
3. Tool executes: `filesystem.read_file()`
4. **User sees follow-up:** *"[Tool executed successfully] {file_contents}"*

**User Experience:**
- ✅ **Conversational** - Like talking to a human
- ✅ **Immediate feedback** - User knows agent is working
- ✅ **Transparent** - Can see what agent is doing
- ❌ **More verbose** - Two separate messages

**Configuration:**
```yaml
agents:
  - id: my_agent
    response_mode: "streaming"
```

## When to Use Each Mode

### Use `"integrated"` when:
- Building **production APIs** where concise responses matter
- **Dashboard/reporting** tools where you want clean outputs
- **Batch processing** where you don't need real-time feedback
- **Integration** with other systems that expect single responses

### Use `"streaming"` when:
- Building **chat interfaces** where conversation flow matters
- **Interactive tools** where users want to see progress
- **Debugging/development** to see what agents are doing
- **User-facing applications** where transparency builds trust

## Technical Implementation

### Agent Response Parsing

```python
if parsed_json and isinstance(parsed_json, dict):
    user_response = parsed_json.get('response', '')
    
    if self.response_mode == "streaming" and user_response:
        # Show immediate response
        print(f"Agent: {user_response}")
        
        # Execute tool
        tool_result = execute_tool(parsed_json['mcp'])
        
        # Show tool results
        return f"{user_response}\n\n[Tool executed]\n{tool_result}"
        
    else:  # integrated mode
        # Execute tool first
        tool_result = execute_tool(parsed_json['mcp'])
        
        # Ask agent to provide final response
        final_response = agent.chat(f"{user_response}\n\nTool result: {tool_result}")
        
        return final_response
```

## Examples

### Integrated Mode Example

**Agent Response:**
```json
{
  "response": "I'll analyze that log file for errors",
  "mcp": {
    "tool": "filesystem",
    "method": "read_file", 
    "params": {"path": "/var/log/app.log"}
  }
}
```

**User Sees:**
```
"I analyzed your log file and found 15 error entries. Most are authentication 
failures from IP 192.168.1.100 occurring between 2PM-3PM today. The errors 
suggest a potential brute force attack. I recommend reviewing your firewall 
settings and blocking that IP range."
```

### Streaming Mode Example

**Agent Response:**
```json
{
  "response": "I'll analyze that log file for errors",
  "mcp": {
    "tool": "filesystem",
    "method": "read_file",
    "params": {"path": "/var/log/app.log"}
  }
}
```

**User Sees (Message 1):**
```
"I'll analyze that log file for errors"
```

**User Sees (Message 2):**
```
"[Tool executed successfully]

Found 15 error entries in /var/log/app.log:
- 12 authentication failures from 192.168.1.100
- 2 database connection timeouts  
- 1 memory allocation error

Most errors occurred between 2PM-3PM today."
```

## Migration Guide

### From Old Format

**Before (problematic):**
```
"Let me check that file {"mcp": {"tool": "filesystem", ...}}"
```
❌ JSON parsing fails, tool call missed

**After (works):**
```json
{
  "response": "Let me check that file",
  "mcp": {"tool": "filesystem", ...}
}
```
✅ Both parsed successfully

### Updating System Prompts

Add response format instructions to your agent system prompts:

```markdown
**CRITICAL: Response Format**
Always respond using this JSON structure:

{
  "response": "Your message to the user",
  "mcp": {
    "tool": "tool_name", 
    "method": "method_name",
    "params": {"param": "value"}
  }
}

Rules:
- Always include "response" field
- Only include "mcp" when using tools
- Never mix plain text with JSON
```

## Best Practices

### System Prompt Design

**Good:**
```json
{
  "response": "I'll check your database connection and run a test query to verify it's working properly.",
  "mcp": {"tool": "database", "method": "test_connection", "params": {}}
}
```

**Poor:**
```json
{
  "response": "Running database test...",
  "mcp": {"tool": "database", "method": "test_connection", "params": {}}  
}
```

### Response Quality

- **Be descriptive** in the response field - explain what you're doing and why
- **Set expectations** - let users know what to expect from the tool call
- **Provide context** - help users understand the next steps

### Error Handling

Both modes handle tool failures gracefully:

**Integrated Mode:** Combines user response with error context
**Streaming Mode:** Shows immediate response + error details separately

## Advanced Usage

### Conditional Response Modes

You can dynamically set response modes based on context:

```python
agent = AgentWrapper(
    name="my_agent",
    response_mode="streaming" if is_interactive else "integrated"
)
```

### Custom Response Processing

Override the chat method for custom behavior:

```python
class CustomAgent(AgentWrapper):
    def chat(self, q=None, **kwargs):
        if self.should_stream_response(q):
            self.response_mode = "streaming"
        return super().chat(q, **kwargs)
```

## Summary

The new structured response format with configurable modes solves the fundamental limitation of having to choose between user communication OR tool usage. Both modes ensure that:

✅ **Tool calls are never missed**  
✅ **Users get appropriate feedback**  
✅ **System behavior is predictable**  
✅ **Integration is seamless**  

Choose the mode that best fits your use case and user experience requirements. 