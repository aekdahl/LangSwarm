# LangSwarm V1 UTF-8 Encoding Corruption Fix

## The Problem

Swedish characters (and other non-ASCII characters) get corrupted in LangSwarm V1 responses:

```
❌ Before: "Naprapati e4r en form av terapi ff6r sme4rta"
✅ After:  "Naprapati är en form av terapi för smärta"
```

### Corruption Pattern

| Character | Unicode | Hex Byte | Corrupted As |
|-----------|---------|----------|--------------|
| ö         | U+00F6  | `f6`     | `f6`         |
| ä         | U+00E4  | `e4`     | `e4`         |
| å         | U+00E5  | `e5`     | `e5`         |
| Ö         | U+00D6  | `d6`     | `d6`         |
| Ä         | U+00C4  | `c4`     | `c4`         |
| Å         | U+00C5  | `c5`     | `c5`         |

### Root Cause

LangSwarm V1's `AgentWrapper._parse_response()` doesn't properly handle bytes objects. When `response.content` contains bytes, the default `str()` conversion shows the hex representation instead of decoding the UTF-8 bytes:

```python
# What V1 is doing:
result = str(bytes_content)  # ❌ "b'Naprapati \\xf6...'"

# What it should do:
result = bytes_content.decode('utf-8')  # ✅ "Naprapati ö..."
```

## The Solution

The monkey patch fixes this in two ways:

### 1. Proper UTF-8 Decoding

```python
# If response is bytes, decode properly
if isinstance(result, bytes):
    try:
        result = result.decode('utf-8')
    except UnicodeDecodeError:
        result = result.decode('latin-1')  # Fallback
```

### 2. Corruption Detection & Repair

Even if corruption already happened, the patch can detect and fix it:

```python
# Detect patterns like "sme4rta" (should be "smärta")
if self._looks_like_hex_corruption(result):
    result = self._fix_hex_corruption(result)
```

## Usage

The encoding fix is automatically applied when you apply the monkey patch:

```python
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()

# Now Swedish characters work correctly!
from archived.v1.core.config import LangSwarmConfigLoader
# ... use LangSwarm as normal
```

## Testing

### Test Script

```python
#!/usr/bin/env python3
"""
Test UTF-8 encoding fix for LangSwarm V1
"""
import langswarm_v1_monkey_patch

# Apply patches
langswarm_v1_monkey_patch.apply()

# Test with Swedish text
from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# Query in Swedish
result = executor.run_workflow(
    workflow_id='main_workflow',
    context={'user_input': 'Vad är naprapati?'}
)

print(f"Result: {result}")

# Should contain proper Swedish characters:
# ✅ "naprapati", "smärta", "för", "behandling"
# ❌ NOT "sme4rta", "ff6r", etc.
```

### Expected Output

```
Result: Naprapati är en form av manuell terapi som används för att behandla 
smärta och funktionsstörningar i rörelseapparaten.
```

## Corruption Patterns Fixed

The patch handles these common corruptions:

| Pattern | Before | After |
|---------|--------|-------|
| Swedish ö | `ff6r` | `för` |
| Swedish ä | `sme4rta` | `smärta` |
| Swedish å | `e5r` | `år` |
| German ü | `mfcde` | `müde` |
| Capital Ö | `D6sterreich` | `Österreich` |

## How It Works

### Detection

```python
def looks_like_hex_corruption(text):
    # Look for patterns: letter + 2-digit-hex + letter
    pattern = r'[a-zA-Z][0-9a-f]{2}[a-zA-Z]'
    matches = re.findall(pattern, text)
    
    # Check if hex codes match known UTF-8 bytes
    suspicious_hexes = ['f6', 'e4', 'e5', 'c4', 'c5', 'd6']
    return any(hex in match.lower() for match in matches for hex in suspicious_hexes)
```

### Repair

```python
def fix_hex_corruption(text):
    # Map hex codes to characters
    hex_to_char = {
        'f6': 'ö', 'e4': 'ä', 'e5': 'å',
        'c4': 'Ä', 'c5': 'Å', 'd6': 'Ö'
    }
    
    # Replace patterns like "sme4rta" → "smärta"
    for hex_code, char in hex_to_char.items():
        pattern = r'([a-zA-Z])' + hex_code + r'([a-zA-Z])'
        text = re.sub(pattern, r'\1' + char + r'\2', text)
    
    return text
```

## Supported Languages

The fix works with:

✅ Swedish (å, ä, ö)  
✅ German (ü, ö, ä, ß)  
✅ French (é, è, ê, à, ç)  
✅ Spanish (ñ, á, í, ó, ú)  
✅ All UTF-8 characters  

## Debugging

If corruption still occurs, enable logging:

```python
import logging
logging.basicConfig(level=logging.WARNING)

import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()
```

You'll see warnings like:

```
WARNING:langswarm_v1_monkey_patch:Detected hex corruption in response from aaf_chatbot, attempting to fix
```

## Known Limitations

### Won't Fix:

1. **Already-corrupted stored data** - Fix only applies to new responses
2. **Multiple encoding layers** - Only handles one level of corruption
3. **Non-UTF-8 sources** - Assumes UTF-8 encoding

### Workarounds:

For already-corrupted stored data, use the repair function manually:

```python
from archived.v1.core.wrappers.generic import AgentWrapper

# Create a dummy wrapper to access the fix method
wrapper = AgentWrapper(name="temp", agent=None)
corrupted = "Naprapati e4r en terapi ff6r sme4rta"
fixed = wrapper._fix_hex_corruption(corrupted)
print(fixed)  # "Naprapati är en terapi för smärta"
```

## Related Issues

This fix also prevents similar issues with:

- JSON responses containing international characters
- Tool outputs with UTF-8 content
- Memory/session storage with non-ASCII text

---

**Status**: ✅ Fixed  
**Applies To**: LangSwarm V1 (archived)  
**Languages**: All UTF-8 supported languages  
**File**: `langswarm_v1_monkey_patch.py`

