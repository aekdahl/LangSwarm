# LangSwarm V1 - Quick Start for Users

## 🎯 Your V1 Code is Broken?

If you're seeing these errors:
```
AttributeError: 'ChatOpenAI' object has no attribute 'run'
```
or Swedish characters corrupted like:
```
"sme4rta" instead of "smärta"
```

**We have a fix!** 🎉

## ✅ Simple 3-Step Fix

### Step 1: Install Latest LangSwarm

```bash
pip install --upgrade langswarm>=0.0.54.dev46
```

### Step 2: Copy the Monkey Patch

Download `langswarm_v1_monkey_patch.py` from the repo root and add it to your project.

### Step 3: Apply at Startup

```python
# At the TOP of your main file
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()

# Then use V1 normally
from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# Now it works! 🎉
result = executor.run_workflow('main_workflow', {'user_input': 'Vad är naprapati?'})
print(result)  # "Naprapati är en terapi för smärta..." ✅
```

## What's Fixed

### 1. LangChain Compatibility ✅
- **Problem**: Modern LangChain (0.3.x+) removed `.run()` method
- **Solution**: Automatically uses `.invoke()` with fallback to `.run()`
- **Works with**: LangChain 0.1.0 through 0.3.x+

### 2. UTF-8 Encoding ✅
- **Problem**: Swedish characters corrupted to hex (`ö` → `f6`, `ä` → `e4`)
- **Solution**: Proper UTF-8 decoding + auto-repair of corruption patterns
- **Works with**: All international characters (Swedish, German, French, etc.)

## Complete Example

```python
# my_app.py

# 1. Apply fixes (do this FIRST)
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()

# 2. Import V1 (as you always did)
from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

# 3. Load your config
loader = LangSwarmConfigLoader('config/langswarm.yaml')
workflows, agents, brokers, tools, metadata = loader.load()

# 4. Run workflows (now works perfectly!)
executor = WorkflowExecutor(workflows, agents)

# Example with Swedish input
result = executor.run_workflow('medical_qa', {
    'question': 'Vad är naprapati och hur hjälper det mot smärta?'
})

print(result)
# Output: "Naprapati är en form av terapi som hjälper mot smärta..." ✅
```

## Where to Get the Patch

### Option 1: Download from Repo
```bash
curl -O https://raw.githubusercontent.com/aekdahl/langswarm/main/langswarm_v1_monkey_patch.py
```

### Option 2: Copy from Package
```python
# After installing langswarm>=0.0.54.dev46
import pkg_resources
patch_path = pkg_resources.resource_filename('langswarm', '../langswarm_v1_monkey_patch.py')
```

### Option 3: Inline (for quick testing)
The full patch code is in `V1_MONKEY_PATCH_README.md` if you want to copy-paste.

## FAQ

### Q: Do I need to change my V1 code?
**A**: No! Just add 2 lines at the top:
```python
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()
```

### Q: Will this break anything?
**A**: No. The patch is:
- ✅ Non-invasive (doesn't modify files)
- ✅ Backward compatible (works with old LangChain too)
- ✅ Safe to apply multiple times

### Q: Can I still use my old LangSwarm version?
**A**: Yes, but you'll need to apply the patch manually. See `V1_MONKEY_PATCH_README.md`

### Q: Should I migrate to V2?
**A**: V2 has many new features, but V1 works great with this patch. Migrate when you're ready!

### Q: Where's the standalone package?
**A**: We created `langswarm-v1-compat` but recommend using the monkey patch for simplicity.

## Troubleshooting

### Still getting .run() errors?

Make sure the patch is applied BEFORE importing V1:
```python
# CORRECT ORDER ✅
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()
from archived.v1.core.config import LangSwarmConfigLoader

# WRONG ORDER ❌
from archived.v1.core.config import LangSwarmConfigLoader  # Too late!
import langswarm_v1_monkey_patch
```

### Swedish characters still corrupted?

Check your terminal encoding:
```bash
# Set UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Need more help?

See detailed docs:
- `V1_MONKEY_PATCH_README.md` - Full usage guide
- `V1_JSON_PARSER_BUG_FIX.md` - Technical details
- `V1_ENCODING_FIX.md` - UTF-8 deep dive

## Migrate to V2 (Optional)

If you want the latest features:

```python
# V2 has modern architecture
from langswarm.core.planning import Coordinator, TaskBrief

brief = TaskBrief(
    objective="Answer medical questions in Swedish",
    inputs={"question": "Vad är naprapati?"},
    constraints={"cost_usd": 1.0, "language": "sv"}
)

coordinator = Coordinator()
result = await coordinator.execute_task(brief)
```

See main `README.md` for V2 guide.

---

## Summary

✅ **Install**: `pip install --upgrade langswarm`  
✅ **Download**: `langswarm_v1_monkey_patch.py`  
✅ **Apply**: Add 2 lines at startup  
✅ **Done**: Your V1 code works perfectly!

**Questions?** Open an issue with `[V1]` in the title.

---

**Version**: 0.0.54.dev46  
**Status**: Production Ready  
**Last Updated**: 2025-11-11

