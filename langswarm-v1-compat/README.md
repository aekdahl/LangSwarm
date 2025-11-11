# LangSwarm V1 Compatibility Package

[![PyPI version](https://badge.fury.io/py/langswarm-v1-compat.svg)](https://pypi.org/project/langswarm-v1-compat/)
[![Python Versions](https://img.shields.io/pypi/pyversions/langswarm-v1-compat.svg)](https://pypi.org/project/langswarm-v1-compat/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Automatic compatibility patches for **LangSwarm V1** to work with modern dependencies.

## What This Fixes

### 1. LangChain API Compatibility ✅
- Fixes `'ChatOpenAI' object has no attribute 'run'` error
- Works with LangChain 0.1.0 through 0.3.x+
- Uses modern `.invoke()` API with fallback to legacy `.run()`

### 2. UTF-8 Encoding Corruption ✅
- Fixes Swedish characters: `ö → f6`, `ä → e4`, `å → e5`
- Proper UTF-8 decoding for all responses
- Auto-detection and repair of hex corruption
- Works with all international characters (Swedish, German, French, Spanish, etc.)

## Installation

```bash
pip install langswarm-v1-compat
```

## Usage

### Automatic (Recommended)

Just import the package - patches auto-apply!

```python
import langswarm_v1_compat

# That's it! Now use LangSwarm V1 normally
from archived.v1.core.config import LangSwarmConfigLoader

loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
# ... rest of your V1 code
```

### Manual

```python
import langswarm_v1_compat

# Explicitly apply patches
langswarm_v1_compat.apply()

# Then use LangSwarm V1
from archived.v1.core.config import LangSwarmConfigLoader
# ... rest of your code
```

### Disable Auto-Apply

If you want to control when patches are applied:

```bash
# Set environment variable
export LANGSWARM_V1_COMPAT_DISABLE_AUTO_APPLY=true
```

```python
import langswarm_v1_compat

# Patches won't auto-apply
# Call explicitly when ready
langswarm_v1_compat.apply()
```

## Requirements

- Python 3.8+
- LangSwarm V1 (archived in your project)
- Works with any LangChain version

## What Gets Fixed

### Before

```python
# Error with modern LangChain
Error: 'ChatOpenAI' object has no attribute 'run'

# Corrupted Swedish text
"Naprapati e4r en terapi ff6r sme4rta"
```

### After

```python
# Works perfectly
✅ No errors

# Correct Swedish text
"Naprapati är en terapi för smärta"
```

## Features

✅ **Non-Invasive** - No changes to archived V1 code  
✅ **Auto-Apply** - Works on import (can be disabled)  
✅ **Safe** - Can be called multiple times  
✅ **Compatible** - Works with all LangChain versions  
✅ **International** - Fixes UTF-8 for all languages  
✅ **Production-Ready** - Tested and stable  

## How It Works

The package applies runtime patches to `AgentWrapper` in LangSwarm V1:

1. **`_call_agent()`** - Uses `.invoke()` (modern) with `.run()` fallback (legacy)
2. **`_parse_response()`** - Proper UTF-8 decoding + hex corruption repair

No changes to your V1 codebase required!

## Supported Languages

- ✅ Swedish (å, ä, ö)
- ✅ German (ü, ö, ä, ß)
- ✅ French (é, è, ê, à, ç)
- ✅ Spanish (ñ, á, í, ó, ú)
- ✅ All UTF-8 characters

## Examples

### Swedish Text (Before & After)

```python
import langswarm_v1_compat  # Auto-applies patches

from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

result = executor.run_workflow(
    workflow_id='main_workflow',
    context={'user_input': 'Vad är naprapati?'}
)

print(result)
# ✅ Output: "Naprapati är en form av terapi för smärta..."
# ❌ Without patch: "Naprapati e4r en form av terapi ff6r sme4rta..."
```

### JSON Parsing (Before & After)

```python
import langswarm_v1_compat

from archived.v1.core.registry.agents import AgentRegistry

# ls_json_parser now works with modern LangChain
agent = AgentRegistry.get("ls_json_parser")
response = agent.chat(
    q="Extract JSON: {'name': 'Jöns', 'city': 'Göteborg'}",
    reset=True
)

print(response)
# ✅ Works correctly
# ❌ Without patch: AttributeError: 'ChatOpenAI' object has no attribute 'run'
```

## Troubleshooting

### Patches Not Working?

Make sure you import `langswarm_v1_compat` **before** importing LangSwarm V1:

```python
# ✅ CORRECT ORDER
import langswarm_v1_compat
from archived.v1.core.config import LangSwarmConfigLoader

# ❌ WRONG ORDER
from archived.v1.core.config import LangSwarmConfigLoader  # Too early
import langswarm_v1_compat  # Too late
```

### Check If Patches Are Applied

```python
import langswarm_v1_compat

if langswarm_v1_compat.is_applied():
    print("✅ Patches applied successfully")
else:
    print("❌ Patches not applied")
    langswarm_v1_compat.apply()
```

## Development

```bash
# Clone the repo
git clone https://github.com/yourusername/LangSwarm
cd LangSwarm/langswarm-v1-compat

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black langswarm_v1_compat/
```

## License

MIT License - see LICENSE file for details

## Support

- 📧 Email: support@langswarm.ai
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/LangSwarm/issues)
- 📖 Docs: [Documentation](https://langswarm.readthedocs.io)

## Related Packages

- [`langswarm`](https://pypi.org/project/langswarm/) - Main LangSwarm package (V2)
- [`langchain`](https://pypi.org/project/langchain/) - LangChain framework

## Changelog

### 1.0.0 (2025-11-10)
- ✅ Initial release
- ✅ LangChain API compatibility fix
- ✅ UTF-8 encoding corruption fix
- ✅ Auto-apply on import
- ✅ Support for all UTF-8 languages

---

**Made with ❤️ by the LangSwarm Team**

