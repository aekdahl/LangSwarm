# Tool Call Chaining Mechanism in LangSwarm
## How Agents Make Multiple Tool Calls Within a Single Workflow Step

### 🔍 The Question
**"How can the agent achieve this? It must be including some setting so the workflow goes back to the agent's step directly again"**

### 🎯 The Answer
There's **no special setting required**! The mechanism is built into LangSwarm's core agent processing logic. Here's how it works:

---

## 🔗 The Chaining Mechanism

### **Key Code Location:**
`langswarm/core/wrappers/generic.py` lines 976-981

```python
# After tool execution:
final_prompt = f"{user_response}{tool_context}"
final_response = self._call_agent(final_prompt, ...)
final_parsed = self.utils.safe_json_loads(final_response.strip())

# This parsed response can ALSO contain tool calls!
# Which triggers the SAME parsing logic recursively
```

---

## 🔄 Step-by-Step Flow

### **1. Initial Agent Call**
```
User: "Create a report with my tasks"
Agent Response 1: {
  "response": "I'll discover my permissions first",
  "mcp": {
    "tool": "smart_filesystem",
    "method": "get_allowed_paths",
    "params": {}
  }
}
```

### **2. Tool Execution**
```
LangSwarm executes: get_allowed_paths()
Tool Result: {
  "local_filesystem": {
    "read_write_paths": ["~/workspace/"]
  }
}
```

### **3. Agent Continuation ⭐ KEY MECHANISM**
```python
# LangSwarm creates enriched prompt:
final_prompt = "I'll discover my permissions first\n\nTool result: {permissions...}"

# Calls agent AGAIN with this enriched context:
final_response = self._call_agent(final_prompt, ...)
```

**Agent Response 2:**
```json
{
  "response": "Based on my permissions, I'll save to ~/workspace/",
  "mcp": {
    "tool": "smart_filesystem", 
    "method": "write_file",
    "params": {
      "path": "~/workspace/report.json",
      "content": "..."
    }
  }
}
```

### **4. Recursive Parsing**
```
LangSwarm parses Agent Response 2 for MORE tool calls
Finds: write_file tool call → executes it
Creates another final_prompt with write_file result
```

### **5. Termination**
```json
Agent Response 3: {
  "response": "Report created successfully at ~/workspace/report.json!"
}
// No 'mcp' field → chaining stops, final response returned
```

---

## 🎯 Key Insights

### **✅ No Special Configuration Needed**
- Tool chaining is built into the core agent processing loop
- No workflow settings or special flags required
- Works automatically when agents return structured JSON with tool calls

### **✅ Recursive Agent Calls**
- Each tool result triggers a new `_call_agent()` call
- Tool results accumulate in the conversation context
- Agent sees full history of previous tool calls and results

### **✅ Agent-Controlled Termination**
- Agent decides when to stop making tool calls
- Simply return a response without an `mcp` field
- No external loop or timeout needed

### **✅ Context Preservation**
- Full conversation context maintained throughout
- Each call builds on previous tool results
- Intelligent decision-making based on accumulated information

---

## 🔄 Complete Recursive Flow

```
User Input 
    ↓
Agent Call 1 → Tool Call 1 → Tool Result 1
    ↓
Agent Call 2 (with Tool Result 1) → Tool Call 2 → Tool Result 2  
    ↓
Agent Call 3 (with Tool Results 1&2) → Tool Call 3 → Tool Result 3
    ↓
Agent Call 4 (with Tool Results 1&2&3) → Final Response (no tools)
    ↓
Return to User
```

---

## 💡 Why This Works So Well

### **1. Natural Conversation Flow**
- Mimics human conversation: ask → receive → ask → receive
- Agent builds understanding incrementally
- Decisions informed by previous responses

### **2. Error Recovery**
- If a tool call fails, agent can adapt and try alternatives
- Context includes both successes and failures
- Intelligent fallback strategies possible

### **3. Efficient Processing**
- All happens within single workflow step
- No workflow orchestration overhead
- Direct agent-to-tool communication

### **4. Flexible Termination**
- Agent chooses when enough information is gathered
- Can make 1 tool call or 10+ tool calls as needed
- Natural stopping point when task is complete

---

## 🛠️ Technical Implementation

### **Core Processing Loop**
The chaining happens in `chat()` method of `AgentWrapper`:

```python
def chat(self, q=None, ...):
    # Initial agent call
    response = self._call_agent(q, ...)
    parsed_json = self.utils.safe_json_loads(response.strip())
    
    if parsed_json and 'mcp' in parsed_json:
        # Execute tool
        middleware_status, middleware_response = self.to_middleware(parsed_json)
        
        if middleware_status == 201:  # Tool success
            # Create enriched prompt with tool result
            tool_context = f"\n\nTool result: {middleware_response}"
            final_prompt = f"{user_response}{tool_context}"
            
            # 🔄 RECURSIVE CALL - This can trigger more tool calls!
            final_response = self._call_agent(final_prompt, ...)
            
            # Parse again (might contain more tool calls)
            final_parsed = self.utils.safe_json_loads(final_response.strip())
            
            # Return response or continue if more tools found
            return final_parsed.get('response', final_parsed)
```

### **Key Points:**
- No explicit loop required
- Recursion happens naturally through `_call_agent()` calls
- Each call can generate new tool calls
- Process terminates when agent returns non-tool response

---

## 🎉 Example Configurations

### **Simple Chaining Agent**
```yaml
agents:
  - id: chaining_agent
    system_prompt: |
      You can make multiple tool calls by returning JSON with 'mcp' field.
      After each tool result, you can make another tool call or provide final response.
      
      Example:
      1. First call: get_allowed_paths()
      2. Use result to inform: write_file()  
      3. Final response to user
    tools:
      - smart_filesystem
```

### **No Special Workflow Settings Needed**
```yaml
workflows:
  simple_workflow:
    steps:
      - agent: chaining_agent
        input: "${user_input}"
        output:
          to: user
```

**That's it!** The agent will automatically chain tool calls within this single step.

---

## 🚀 Benefits

1. **🔧 Tool-Centric**: Aligns perfectly with MCP/tool architecture
2. **🧠 Intelligent**: Agent makes informed decisions based on tool results  
3. **🔄 Flexible**: Can adapt chain length based on task complexity
4. **⚡ Efficient**: All processing within single workflow step
5. **🛡️ Robust**: Built-in error handling and recovery
6. **📈 Scalable**: Works with any number of tools and complexity levels

---

## 📝 Summary

**Tool call chaining in LangSwarm works through recursive agent calls, not special workflow settings:**

- ✅ Agent makes tool call → Tool executes → Result added to context
- ✅ Agent called again with enriched context → Can make another tool call  
- ✅ Process continues until agent returns final response without tools
- ✅ All happens automatically within single workflow step
- ✅ No configuration needed beyond structured JSON responses

**The "secret" is in the recursive `_call_agent()` calls that naturally enable continuous tool calling within a single workflow execution!** 🎯