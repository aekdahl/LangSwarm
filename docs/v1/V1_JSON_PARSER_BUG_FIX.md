# LangSwarm V1 Bug Fixes: Monkey Patch Solutions

## Issues Summary

### Bug #1: ls_json_parser AttributeError

**Bug**: LangSwarm V1 internal agent `ls_json_parser` attempts to call `.run()` method on `ChatOpenAI` objects, which don't have this method in modern LangChain (0.3.x+).

**Error**: `'ChatOpenAI' object has no attribute 'run'`

**Impact**: Workflow execution failures when LangSwarm attempts to parse JSON responses from tools or agents.

### Bug #2: UTF-8 Encoding Corruption

**Bug**: Swedish characters (ö, ä, å) and other UTF-8 characters get corrupted to hex patterns (f6, e4, e5).

**Error**: `"Naprapati e4r en terapi ff6r sme4rta"` instead of `"Naprapati är en terapi för smärta"`

**Impact**: All non-ASCII responses are corrupted, affecting international users.

**Version**: LangSwarm V1 (archived, v0.0.54.dev44)

---

## Error Details

### Log Evidence

```
2025-11-10 11:05:02,902 - Query sent to agent ls_json_parser: Provide machine parseable json...
2025-11-10 11:05:02,903 - Error for agent ls_json_parser: 'ChatOpenAI' object has no attribute 'run'
```

### Context

1. **Tool execution succeeds**: BigQuery vector search returns results successfully
2. **Primary agent responds**: Main workflow agent generates response
3. **Error occurs during JSON parsing**: When LangSwarm tries to parse/validate JSON responses
4. **`ls_json_parser` is internal**: This agent is NOT in user `langswarm.yaml` configuration - it's a LangSwarm framework internal

### What Works

- ✅ Tool retrieval (BigQuery vector search)
- ✅ Primary agent (aaf_chatbot) response generation
- ✅ Workflow execution up to JSON parsing step

### What Fails

- ❌ `ls_json_parser` agent execution
- ❌ JSON response validation/parsing by LangSwarm internals

---

## Root Cause Analysis

### The Problem

LangSwarm V1's `AgentWrapper` class uses **LangChain's older Agent interface** that expects a `.run()` method:

**File**: `archived/v1/core/wrappers/generic.py` (lines 528, 584)

```python
# What LangSwarm V1 is doing:
response = self.agent.run(q)  # ❌ ChatOpenAI doesn't have .run()
```

### What Should Happen

LangChain's `ChatOpenAI` class in modern versions (0.3.x+) uses different methods:

```python
# Modern LangChain (0.3.x+) correct usage:
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

chatbot = ChatOpenAI(model="gpt-4o")

# Option 1: Direct invocation
result = chatbot.invoke([HumanMessage(content=query)])

# Option 2: Async invocation
result = await chatbot.ainvoke([HumanMessage(content=query)])

# Option 3: Streaming
for chunk in chatbot.stream([HumanMessage(content=query)]):
    print(chunk.content)
```

### Why This Happens

1. **LangSwarm V1 uses internal agents** for framework operations (like `ls_json_parser`)
2. **These internal agents** were built against older LangChain versions
3. **LangChain deprecated `.run()`** in favor of `.invoke()` and `.ainvoke()`
4. **V1 is archived** and cannot be directly modified

---

## Solution: Monkey Patch

Since LangSwarm V1 is archived code, we provide a **monkey patch** that users can apply.

### Installation

**File**: `langswarm_v1_monkey_patch.py` (provided in repo root)

### Usage

```python
# STEP 1: Apply the patch FIRST (before importing LangSwarm V1)
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()

# STEP 2: Now import and use LangSwarm V1 as normal
from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader('your_config.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# ls_json_parser will now work correctly!
result = executor.run_workflow('your_workflow', your_input)
```

### What the Patch Does

The monkey patch modifies `AgentWrapper._call_agent` to:

1. ✅ Try `.invoke()` first (modern LangChain API)
2. ✅ Fall back to `.run()` if `.invoke()` doesn't exist (older LangChain)
3. ✅ Raise clear error if neither method exists
4. ✅ Maintain backward compatibility

**Code snippet** (from `langswarm_v1_monkey_patch.py`):

```python
# Try modern API first, fall back to legacy
if hasattr(self.agent, "invoke"):
    try:
        from langchain.schema import HumanMessage
    except ImportError:
        from langchain_core.messages import HumanMessage
    response = self.agent.invoke([HumanMessage(content=q)])
elif hasattr(self.agent, "run"):
    response = self.agent.run(q)
else:
    raise AttributeError(
        f"Agent {type(self.agent).__name__} has neither 'run' nor 'invoke' method"
    )
```

---

## Testing

### Test the Patch

```python
# test_v1_patch.py
import langswarm_v1_monkey_patch

# Apply patch
if langswarm_v1_monkey_patch.apply():
    print("✅ Patch applied successfully")
    
    # Test with ls_json_parser
    from archived.v1.core.registry.agents import AgentRegistry
    
    agent = AgentRegistry.get("ls_json_parser")
    if agent:
        response = agent.chat(
            q="Extract JSON: {'key': 'value'}",
            reset=True,
            erase_query=True
        )
        print(f"✅ ls_json_parser works: {response}")
    else:
        print("⚠️  ls_json_parser not available (OPENAI_API_KEY not set?)")
else:
    print("❌ Patch failed to apply")
```

### Run the Test

```bash
python langswarm_v1_monkey_patch.py
```

Expected output:
```
✅ Patch applied successfully!

Now you can use LangSwarm V1 with modern LangChain.
```

---

## Integration Example

### Your Application

```python
# your_app.py
import os
import langswarm_v1_monkey_patch

# Apply patch BEFORE any LangSwarm imports
langswarm_v1_monkey_patch.apply()

# Now use LangSwarm V1
from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

def main():
    # Load your configuration
    loader = LangSwarmConfigLoader('config/langswarm.yaml')
    workflows, agents, brokers, tools, metadata = loader.load()
    
    # Create executor
    executor = WorkflowExecutor(workflows, agents)
    
    # Run workflow (ls_json_parser will work!)
    result = executor.run_workflow(
        workflow_id='main_workflow',
        context={'user_input': 'Your query here'}
    )
    
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

---

## Benefits

- ✅ **Backward Compatible**: Falls back to `.run()` if `.invoke()` doesn't exist
- ✅ **Forward Compatible**: Works with modern LangChain 0.3.x+ versions
- ✅ **Non-Invasive**: Doesn't modify archived V1 code
- ✅ **Graceful Failure**: Raises clear error if neither method exists
- ✅ **No Breaking Changes**: Existing V1 workflows continue to work
- ✅ **Fixes ls_json_parser**: The internal JSON parser agent now works correctly
- ✅ **Fixes UTF-8 Corruption**: Swedish and all international characters work properly
- ✅ **Auto-Repair**: Detects and fixes existing hex corruption patterns

---

## Impact

### What Now Works

**Bug #1 (LangChain API):**
- ✅ `ls_json_parser` internal agent execution
- ✅ JSON response validation/parsing
- ✅ Tool responses with JSON structures
- ✅ Workflows using BigQuery vector search and other tools

**Bug #2 (UTF-8 Encoding):**
- ✅ Swedish characters (ö, ä, å) display correctly
- ✅ All international characters work properly
- ✅ Automatic detection and repair of hex corruption
- ✅ Proper UTF-8 decoding for all responses

### Unchanged Behavior
- ✅ Primary agent response generation
- ✅ Tool execution
- ✅ Workflow orchestration
- ✅ Memory management

---

## Requirements

- Python 3.8+
- LangChain 0.1.0+ (works with any version)
- LangSwarm V1 (archived)

---

## Troubleshooting

### Patch Doesn't Apply

**Error**: `Cannot import AgentWrapper from archived V1 code`

**Solution**: Ensure the `archived/v1/` directory exists in your workspace.

### Still Getting AttributeError

**Error**: `'ChatOpenAI' object has no attribute 'run'` persists

**Solution**: Make sure you call `apply()` BEFORE importing any LangSwarm V1 modules:

```python
# WRONG ORDER:
from archived.v1.core.config import LangSwarmConfigLoader  # ❌ Too early
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()  # ❌ Too late

# CORRECT ORDER:
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()  # ✅ First
from archived.v1.core.config import LangSwarmConfigLoader  # ✅ Then imports
```

### Auto-Apply on Import

If you want the patch to apply automatically when the module is imported:

```python
# In langswarm_v1_monkey_patch.py, change:
AUTO_APPLY_ON_IMPORT = True

# Then just import it:
import langswarm_v1_monkey_patch  # Patch applied automatically
```

---

## Related Documentation

- LangChain Migration Guide: https://python.langchain.com/docs/versions/migrating_chains/
- LangChain 0.3.x API: https://python.langchain.com/docs/versions/v0_3/

---

## Appendix: LangChain API Migration

### Old API (Deprecated in LangChain 0.1.0+)

```python
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool

llm = ChatOpenAI(model="gpt-4")
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")

# OLD WAY:
response = agent.run("What is the capital of France?")  # ❌ Deprecated
```

### New API (LangChain 0.3.x+)

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage

llm = ChatOpenAI(model="gpt-4")

# Direct usage:
response = llm.invoke([HumanMessage(content="What is the capital of France?")])
print(response.content)  # ✅ Modern way

# Agent usage:
prompt = ChatPromptTemplate.from_messages([...])
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

response = agent_executor.invoke({"input": "What is the capital of France?"})
print(response["output"])  # ✅ Modern way
```

---

**Fixed Date**: 2025-11-10  
**Reporter**: Alexander Ekdahl (alex@algorithma.ai)  
**Status**: ✅ RESOLVED (Monkey Patch Available)  
**File**: `langswarm_v1_monkey_patch.py`
