# Code-Documentation Migration Process

**Coordinated migration process ensuring code and documentation move together**

## 🎯 Overview

This process ensures that as we complete V2 code migration tasks, the corresponding documentation is moved, updated, and validated to match the new implementation. This maintains synchronization between what the code does and what the documentation promises.

---

## 🔄 Migration Coordination Principles

### 1. **Code-First Migration**
- Documentation moves **only after** code migration is complete
- No documentation promises features that don't exist in V2 yet
- Documentation reflects actual V2 implementation, not V1 legacy

### 2. **Bidirectional Validation**
- **Code → Docs**: Docs must support all implemented features
- **Docs → Code**: All documented features must be implemented
- No orphaned documentation or undocumented features

### 3. **Incremental Movement**
- Move documentation in chunks that correspond to completed V2 tasks
- Each moved section is immediately validated against V2 code
- Maintain working state at all times

---

## 📋 Migration Process Workflow

### Phase 1: Pre-Migration Assessment
**Timing**: Before starting each V2 implementation task

#### 1.1 Identify Documentation Dependencies
```bash
# For each V2 task, identify affected documentation
Task: Error System Consolidation (Task 01)
Documentation Impact:
├── user-guides/troubleshooting/     # Error handling guides
├── developer-guides/debugging/     # Debug documentation  
├── api-reference/core/errors/      # Error API docs
└── examples/error-handling/        # Error examples
```

#### 1.2 Create Documentation Migration Plan
- **Current Files**: List all affected documentation files
- **Target Location**: Map to V2 docs structure
- **Content Changes**: Identify what needs updating for V2
- **Validation Tests**: Define how to verify docs match code

#### 1.3 Mark Documentation as "Migration Pending"
```markdown
> ⚠️ **V2 Migration Notice**: This documentation is being updated for LangSwarm V2. 
> Current information may not reflect V2 implementation. 
> Migration Status: Pending Task 01 completion.
```

### Phase 2: Code Implementation
**Timing**: During V2 task implementation

#### 2.1 Track Documentation Requirements
As you implement V2 code:
- **Note New APIs**: Document any new methods, classes, parameters
- **Track Changes**: Record what's different from V1
- **Identify Examples**: Flag code that needs documentation examples
- **Note Breaking Changes**: Document any changes that affect user code

#### 2.2 Create Documentation Notes
```markdown
# Task 01: Error System - Documentation Requirements

## New Components Implemented
- `langswarm.core.errors.ErrorHierarchy`
- `langswarm.core.errors.StructuredError`
- `langswarm.core.errors.ErrorHandler`

## API Changes from V1
- Error types reduced from 483+ to 47 structured types
- New error format: `{"error_type": "ValidationError", "context": {...}}`
- Centralized error handling in `ErrorHandler.handle()`

## Documentation Needed
- User guide for new error format
- Developer guide for error handling patterns
- API reference for error classes
- Migration guide from V1 error patterns
- Examples of error handling in workflows

## Breaking Changes
- Old error response format no longer supported
- Custom error classes must inherit from `StructuredError`
```

### Phase 3: Documentation Migration
**Timing**: After V2 task code is complete and tested

#### 3.1 Move Documentation Files
```bash
# Move files to V2 structure based on completed code
mv docs/debug-*.md docs_v2/developer-guides/debugging/
mv docs/critical-failure-handling.md docs_v2/troubleshooting/error-handling/
```

#### 3.2 Update Content for V2
For each moved file:
1. **Update Code Examples**: Use V2 syntax and APIs
2. **Fix Import Statements**: Update to V2 module paths
3. **Correct Configuration**: Use V2 configuration format
4. **Add Migration Notes**: Include V1→V2 migration info
5. **Update Cross-References**: Fix links to other V2 docs

#### 3.3 Create Missing Documentation
If code implementation revealed missing docs:
```bash
# Create new documentation files
touch docs_v2/api-reference/core/errors/error-hierarchy.md
touch docs_v2/user-guides/troubleshooting/v2-error-handling.md
touch docs_v2/examples/tutorials/error-handling-patterns.md
```

### Phase 4: Validation & Testing
**Timing**: After documentation is moved and updated

#### 4.1 Code-Documentation Sync Check
```python
# Validation script example
def validate_task_01_docs():
    """Validate error system documentation matches implementation"""
    
    # Check API documentation completeness
    error_classes = get_v2_error_classes()
    documented_classes = get_documented_error_classes()
    assert error_classes == documented_classes
    
    # Validate code examples
    examples = extract_code_examples("docs_v2/user-guides/troubleshooting/")
    for example in examples:
        assert example.executes_successfully()
    
    # Check configuration examples
    config_examples = extract_config_examples("docs_v2/examples/")
    for config in config_examples:
        assert config.validates_against_v2_schema()
```

#### 4.2 Documentation Quality Check
- [ ] **Examples Work**: All code examples execute successfully
- [ ] **Links Valid**: All internal links point to correct V2 locations
- [ ] **Imports Correct**: All import statements use V2 modules
- [ ] **Configuration Valid**: All config examples use V2 format
- [ ] **Migration Complete**: V1 references updated to V2

#### 4.3 User Experience Validation
- [ ] **Navigation Works**: Users can find information easily
- [ ] **Examples Clear**: Step-by-step instructions are complete
- [ ] **Troubleshooting Accurate**: Common issues have working solutions
- [ ] **API Reference Complete**: All public APIs are documented

---

## 📅 Task-by-Task Migration Schedule

### Task 01: Error System Consolidation
**Code Status**: 🚧 In Progress  
**Documentation Migration**: 📋 Pending code completion

#### Documentation to Move:
```
Current → V2 Target
docs/debug-*.md → developer-guides/debugging/
docs/critical-failure-handling.md → troubleshooting/error-handling/
STEP_BY_STEP_FAILURE_ANALYSIS.md → troubleshooting/debugging/failure-analysis.md
```

#### New Documentation Required:
- `api-reference/core/errors/` - V2 error API documentation
- `user-guides/troubleshooting/v2-errors.md` - User guide for new error format
- `migration/v1-to-v2/error-migration.md` - Error system migration guide

### Task 02: Middleware Modernization
**Code Status**: 📋 Planned  
**Documentation Migration**: 📋 Planned

#### Documentation to Move:
```
Current → V2 Target
langswarm/core/wrappers/middleware.py docstrings → api-reference/core/middleware/
```

#### New Documentation Required:
- `user-guides/agents/middleware.md` - Middleware configuration guide
- `developer-guides/extending/middleware.md` - Custom middleware development
- `api-reference/core/middleware/` - Middleware API reference

### Task 03: Tool System Unification
**Code Status**: 📋 Planned  
**Documentation Migration**: 📋 Planned

#### Documentation to Move:
```
Current → V2 Target
langswarm/mcp/tools/MCP_TOOL_DEVELOPER_GUIDE.md → developer-guides/extending/tool-development.md
langswarm/mcp/tools/*/readme.md → tools/mcp/{tool-name}/
langswarm/mcp/tools/*/template.md → tools/mcp/{tool-name}/
docs/LOCAL_MCP_GUIDE.md → user-guides/tools/mcp-local.md
docs/REMOTE_MCP_GUIDE.md → user-guides/tools/mcp-remote.md
```

### Task 04: Agent System Simplification
**Code Status**: 📋 Planned  
**Documentation Migration**: 📋 Planned

#### Documentation to Move:
```
Current → V2 Target
docs/simplification/02-zero-config-agents.md → ARCHIVE (feature removed)
docs/guides/RESPONSE_MODES_GUIDE.md → user-guides/agents/response-modes.md
```

#### Documentation to Update:
- Remove all references to zero-config agents and behavior presets
- Update agent configuration guides to reflect manual configuration requirement
- Preserve response modes and structured response documentation

---

## 🔧 Migration Tools & Scripts

### Documentation Validation Script
```python
#!/usr/bin/env python3
"""
Validate documentation-code synchronization for V2 migration tasks
"""

import os
import ast
import yaml
from pathlib import Path

def validate_task_migration(task_number: int):
    """Validate that documentation matches implemented code for a task"""
    
    # Load task configuration
    task_config = load_task_config(task_number)
    
    # Check code implementation status
    code_complete = verify_code_completion(task_config)
    if not code_complete:
        return False, "Code implementation not complete"
    
    # Check documentation migration
    docs_migrated = verify_docs_migration(task_config)
    if not docs_migrated:
        return False, "Documentation not migrated"
    
    # Validate examples
    examples_valid = validate_examples(task_config)
    if not examples_valid:
        return False, "Code examples don't execute"
    
    # Check API coverage
    api_coverage = validate_api_coverage(task_config)
    if not api_coverage:
        return False, "API documentation incomplete"
    
    return True, "Migration validation passed"

def extract_code_examples(docs_path: Path):
    """Extract and validate all code examples in documentation"""
    examples = []
    for md_file in docs_path.rglob("*.md"):
        examples.extend(extract_code_blocks(md_file))
    return examples

def validate_v2_imports(code_example: str):
    """Ensure code example uses V2 imports"""
    tree = ast.parse(code_example)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("langswarm") and not alias.name.startswith("langswarm.v2"):
                    return False, f"V1 import found: {alias.name}"
    return True, "All imports are V2"
```

### Documentation Link Validator
```python
def validate_internal_links(docs_root: Path):
    """Validate all internal documentation links"""
    broken_links = []
    
    for md_file in docs_root.rglob("*.md"):
        links = extract_markdown_links(md_file)
        for link in links:
            if link.is_internal():
                target = resolve_link_target(link, md_file)
                if not target.exists():
                    broken_links.append((md_file, link, target))
    
    return broken_links

def fix_broken_links(broken_links):
    """Auto-fix common broken link patterns"""
    fixes = {
        r'docs/(.+)\.md': r'..\/..\/\1.md',  # Fix old docs/ references
        r'langswarm\.(.+)': r'langswarm.\1',  # Fix V1 module references
    }
    
    for file_path, link, target in broken_links:
        for pattern, replacement in fixes.items():
            if re.match(pattern, link.target):
                new_target = re.sub(pattern, replacement, link.target)
                replace_link_in_file(file_path, link.target, new_target)
```

---

## 📊 Migration Status Tracking

### Task Migration Dashboard
```markdown
## V2 Code-Documentation Migration Status

| Task | Code Status | Docs Moved | Examples Valid | API Coverage | Complete |
|------|-------------|------------|----------------|--------------|----------|
| 01 - Error System | 🚧 In Progress | ❌ Pending | ❌ Pending | ❌ Pending | ❌ |
| 02 - Middleware | 📋 Planned | ❌ Pending | ❌ Pending | ❌ Pending | ❌ |
| 03 - Tool System | 📋 Planned | ❌ Pending | ❌ Pending | ❌ Pending | ❌ |
| 04 - Agent System | 📋 Planned | ❌ Pending | ❌ Pending | ❌ Pending | ❌ |
| 05 - Configuration | 📋 Planned | ❌ Pending | ❌ Pending | ❌ Pending | ❌ |
| 06 - Session Mgmt | 📋 Planned | ❌ Pending | ❌ Pending | ❌ Pending | ❌ |
| 07 - Dependencies | 📋 Planned | ❌ Pending | ❌ Pending | ❌ Pending | ❌ |
| 08 - Testing | 📋 Planned | ❌ Pending | ❌ Pending | ❌ Pending | ❌ |
```

### Quality Gates
Each task must pass all quality gates before being marked complete:

1. **✅ Code Implementation**: All V2 code working and tested
2. **✅ Documentation Migration**: All related docs moved to V2 structure
3. **✅ Example Validation**: All code examples execute successfully
4. **✅ API Coverage**: All public APIs documented
5. **✅ Link Validation**: All internal links work correctly
6. **✅ User Testing**: Documentation tested with target users

---

## 🚀 Getting Started

### For Each V2 Task:

1. **Before Implementation**:
   ```bash
   # Identify documentation impact
   python scripts/analyze_docs_impact.py --task 01
   
   # Create migration plan
   python scripts/create_migration_plan.py --task 01
   ```

2. **During Implementation**:
   ```bash
   # Track documentation requirements
   echo "New API: ErrorHierarchy.get_error_type()" >> task_01_docs_requirements.md
   ```

3. **After Code Completion**:
   ```bash
   # Migrate documentation
   python scripts/migrate_docs.py --task 01
   
   # Validate migration
   python scripts/validate_migration.py --task 01
   ```

4. **Mark Task Complete**:
   ```bash
   # Final validation
   python scripts/final_validation.py --task 01
   
   # Update migration status
   python scripts/update_status.py --task 01 --status complete
   ```

---

**This process ensures that LangSwarm V2 documentation accurately reflects the implemented code and provides users with reliable, working examples and guides.**
