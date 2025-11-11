# LangSwarm V1 Monkey Patch - Quick Start

## The Problem

LangSwarm V1's internal `ls_json_parser` agent fails with modern LangChain (0.3.x+):

```
Error for agent ls_json_parser: 'ChatOpenAI' object has no attribute 'run'
```

## The Solution

Apply this monkey patch **once** at the start of your application:

```python
# your_app.py
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()

# Now use LangSwarm V1 as normal
from archived.v1.core.config import LangSwarmConfigLoader
# ... rest of your code
```

## Installation

The patch file is already in the repo root: `langswarm_v1_monkey_patch.py`

## Usage Example

```python
#!/usr/bin/env python3
"""
Example application using LangSwarm V1 with the compatibility patch
"""
import os
import langswarm_v1_monkey_patch

# STEP 1: Apply patch BEFORE importing LangSwarm V1
print("Applying LangSwarm V1 compatibility patches...")
if langswarm_v1_monkey_patch.apply():
    print("✅ Patches applied successfully\n")
else:
    print("❌ Failed to apply patches")
    exit(1)

# STEP 2: Now import and use LangSwarm V1
from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

def main():
    # Your LangSwarm V1 configuration
    config_path = 'config/langswarm.yaml'
    
    # Load workflows
    loader = LangSwarmConfigLoader(config_path)
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

## What Gets Fixed

### Fix #1: LangChain API Compatibility
✅ Internal `ls_json_parser` agent now works  
✅ JSON response parsing succeeds  
✅ Tool responses with JSON structures handled correctly  
✅ Workflows using BigQuery and other tools execute properly

### Fix #2: UTF-8 Encoding Corruption
✅ Swedish characters (ö, ä, å) no longer corrupted to hex (f6, e4, e5)  
✅ Proper UTF-8 decoding for all responses  
✅ Automatic detection and repair of hex corruption patterns  
✅ Works with all international characters  

## Compatibility

- ✅ LangChain 0.1.0 through 0.3.x+
- ✅ Python 3.8+
- ✅ All LangSwarm V1 features

## No Code Changes Required

The patch works by modifying behavior at runtime. You don't need to:
- ❌ Edit any V1 archived code
- ❌ Fork the repository
- ❌ Rebuild anything
- ❌ Change your workflows

Just import and apply!

## Troubleshooting

### Issue: Patch doesn't apply

Make sure the `archived/v1/` directory exists in your project.

### Issue: Still getting AttributeError

Apply the patch **before** importing any V1 modules:

```python
# WRONG:
from archived.v1... import ...  # ❌ Too early
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()

# RIGHT:
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()  # ✅ First
from archived.v1... import ...     # ✅ Then imports
```

## Testing the Patch

```bash
# Run the patch test
python langswarm_v1_monkey_patch.py
```

Expected output:
```
✅ Patch applied successfully!

Now you can use LangSwarm V1 with modern LangChain.
```

## Documentation

- Full details: `V1_JSON_PARSER_BUG_FIX.md`
- Code: `langswarm_v1_monkey_patch.py`

---

**Status**: ✅ Production Ready  
**Date**: 2025-11-10

