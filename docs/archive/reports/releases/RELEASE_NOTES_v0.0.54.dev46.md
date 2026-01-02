# Release Notes: v0.0.54.dev46

**Release Date**: 2025-11-11  
**Type**: Development Release  
**Status**: Production Ready

## 🎉 Highlights

### V1 Bug Fixes (Critical)
Fixed two critical bugs affecting LangSwarm V1 users:

1. **LangChain API Compatibility** ✅
   - Fixed `AttributeError: 'ChatOpenAI' object has no attribute 'run'`
   - Now works with LangChain 0.1.0 through 0.3.x+
   - Automatic `.run()` → `.invoke()` compatibility

2. **UTF-8 Encoding** ✅
   - Fixed Swedish character corruption (ö→f6, ä→e4, å→e5)
   - Proper UTF-8 decoding for all international text
   - Auto-repair of hex corruption patterns

### V2 Features (New)
Complete hierarchical planning system with retrospective validation:

- ✅ Multi-agent orchestration with reactive control
- ✅ Async retrospective validation (low latency + high quality)
- ✅ Automatic rollback/replay on validation failures
- ✅ Lineage tracking and impact analysis
- ✅ Promotion gates and compensation actions

## 📦 What's Included

### For V1 Users
- **Monkey Patch**: `langswarm_v1_monkey_patch.py` (standalone fix)
- **Documentation**: 
  - `README_V1_USERS.md` - Quick start guide
  - `V1_MONKEY_PATCH_README.md` - Detailed usage
  - `V1_JSON_PARSER_BUG_FIX.md` - Technical details
  - `V1_ENCODING_FIX.md` - UTF-8 fix deep dive
  - `V1_FINAL_SOLUTION.md` - Solution overview

### For V2 Users
- **Planning System**: `langswarm/core/planning/` (10 new modules)
- **Examples**: `examples/planning/` (6 comprehensive examples)
- **Documentation**:
  - `HIERARCHICAL_PLANNING_COMPLETE.md`
  - `RETROSPECTIVE_VALIDATION_COMPLETE.md`

### Both
- **Version**: Updated to 0.0.54.dev46
- **README**: Complete rewrite focusing on multi-agent orchestration

## 🚀 Installation

### Upgrade Existing Install
```bash
pip install --upgrade langswarm>=0.0.54.dev46
```

### Fresh Install
```bash
pip install langswarm==0.0.54.dev46
```

## 📖 Usage

### V1 (with fixes)
```python
# Apply monkey patch
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()

# Use V1 normally
from archived.v1.core.config import LangSwarmConfigLoader, WorkflowExecutor

loader = LangSwarmConfigLoader('config.yaml')
workflows, agents, brokers, tools, metadata = loader.load()
executor = WorkflowExecutor(workflows, agents)

# Now works with modern LangChain and Swedish characters!
result = executor.run_workflow('main', {'input': 'Vad är naprapati?'})
```

### V2 (new)
```python
from langswarm.core.planning import Coordinator, TaskBrief

brief = TaskBrief(
    objective="Process expense reports",
    inputs={"data": "expenses.csv"},
    constraints={"cost_usd": 5.0, "latency_sec": 120}
)

coordinator = Coordinator()
result = await coordinator.execute_task(brief)
```

## 🐛 Bug Fixes

### V1 Fixes
1. **LangChain compatibility** ([#BUG-001])
   - `AgentWrapper._call_agent()` now tries `.invoke()` first, falls back to `.run()`
   - Works with all LangChain versions 0.1.0+

2. **UTF-8 encoding** ([#BUG-002])
   - `AgentWrapper._parse_response()` properly decodes bytes as UTF-8
   - Auto-detects and repairs hex corruption patterns
   - Supports all international characters

### Implementation
- Non-invasive monkey patch (doesn't modify archived code)
- Applied at runtime via `langswarm_v1_monkey_patch.apply()`
- Idempotent (safe to apply multiple times)
- Zero performance impact

## ✨ New Features

### Hierarchical Planning System
- **TaskBrief**: High-level task definition
- **ActionContract**: Detailed step specifications
- **Plan/PlanPatch**: Versioned plan evolution
- **Observation**: Standardized execution results
- **Decision**: Policy-driven control flow
- **Controller**: Continue/retry/alternate/replan/escalate logic

### Retrospective Validation
- **Fast-path**: Lightweight inline validation
- **Slow-path**: Async heavy validation
- **Speculative continuation**: Proceed while validating
- **Auto-rollback**: Invalid checkpoints trigger replay
- **Lineage tracking**: Content-addressed artifacts
- **Impact analysis**: Compute affected downstream steps
- **Compensation**: Undo side effects on rollback
- **Promotion gates**: Block critical steps until validated

### Components
1. **Planner** (`planner.py`) - Generate plans from TaskBriefs
2. **Executor** (`executor.py`) - Run steps, return Observations
3. **Controller** (`controller.py`) - Decision logic with policies
4. **Verifier** (`verifier.py`) - Test conditions and drift
5. **PlanPatcher** (`patcher.py`) - Apply patches, version history
6. **ContractValidator** (`contracts.py`) - Enforce contracts
7. **EscalationRouter** (`escalation.py`) - S1-S4 severity handling
8. **Coordinator** (`coordinator.py`) - Main control loop
9. **LineageGraph** (`lineage.py`) - Track artifact dependencies
10. **RetrospectRunner** (`retrospect.py`) - Async validation
11. **ReplayManager** (`replay.py`) - Invalidation & replay
12. **PlanningYAMLParser** (`schema.py`) - YAML config parsing

### Examples
1. `01_simple_sequential.py` - Basic planning
2. `02_with_retrospects.py` - Retrospective validation
3. `03_with_gates_and_retrospects.py` - Gates + retrospects
4. `04_expense_summary_complete.py` - Full workflow
5. `05_data_pipeline_with_compensation.py` - ETL with side effects
6. `06_advanced_lineage.py` - Complex dependencies

## 📝 Documentation

### New Files
- `README.md` - Complete rewrite
- `README_V1_USERS.md` - V1 quick start
- `V1_MONKEY_PATCH_README.md` - Patch usage guide
- `V1_JSON_PARSER_BUG_FIX.md` - Bug technical details
- `V1_ENCODING_FIX.md` - UTF-8 fix deep dive
- `V1_FINAL_SOLUTION.md` - Solution overview
- `V1_MIGRATION_GUIDE.md` - Migration steps
- `HIERARCHICAL_PLANNING_COMPLETE.md` - Planning system summary
- `RETROSPECTIVE_VALIDATION_COMPLETE.md` - Retrospects summary
- `examples/planning/README.md` - Examples guide

### Updated Files
- `pyproject.toml` - Version bump to 0.0.54.dev46

## 🔧 Technical Details

### Architecture
- V1: Located in `archived/v1/` (unchanged)
- V2: Located in `langswarm/core/` (new planning system)
- Monkey Patch: Standalone `langswarm_v1_monkey_patch.py`

### Compatibility
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **LangChain**: 0.1.0 through 0.3.x+
- **V1**: Fully backward compatible with monkey patch
- **V2**: New API, no breaking changes to existing V2 code

### Dependencies
No new dependencies added for V1 fixes.

V2 planning system uses only existing LangSwarm dependencies.

## ⚠️ Known Issues

### V1 Integration
- `langswarm.v1.*` package exists but has import issues
- Legacy absolute imports need refactoring
- **Workaround**: Use standalone monkey patch with `archived.v1.*`
- **Status**: Deferred to future release

## 🔮 What's Next

### v0.0.55 (Future)
- Full V1 refactoring for `langswarm.v1.*` integration
- Or V1 deprecation in favor of V2
- Additional planning system features
- More examples and templates

## 💬 Feedback

Found a bug? Have a feature request?
- **GitHub Issues**: Tag with `[V1]` or `[V2]`
- **Documentation**: See README.md
- **Support**: alexander.ekdahl@gmail.com

## 🙏 Acknowledgments

Thanks to all users who reported the V1 bugs, especially those working with Swedish and international text!

---

## Migration Guide

### From v0.0.54.dev45 or earlier

#### V1 Users
```python
# Before (broken)
from archived.v1.core.config import LangSwarmConfigLoader
loader = LangSwarmConfigLoader('config.yaml')
# ❌ Error: 'ChatOpenAI' object has no attribute 'run'

# After (working)
import langswarm_v1_monkey_patch
langswarm_v1_monkey_patch.apply()
from archived.v1.core.config import LangSwarmConfigLoader
loader = LangSwarmConfigLoader('config.yaml')
# ✅ Works perfectly!
```

#### V2 Users
No changes needed - fully backward compatible.

---

**Full Changelog**: v0.0.54.dev45...v0.0.54.dev46  
**Contributors**: @aekdahl  
**License**: MIT

