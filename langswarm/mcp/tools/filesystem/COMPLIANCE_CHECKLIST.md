# Filesystem Tool - Compliance Checklist

**Status**: 🚨 **CRITICAL FIXES NEEDED**  
**Priority**: HIGH - Broken workflow functionality

## 🚨 Critical Issues

### 1. Broken Workflow Function Calls
- [ ] **URGENT**: Fix `mcp_call` function parameters in `workflows.yaml`
  - Current: `tool_id: ${selected_function}` ❌
  - Fix to: `mcp_url: "local://filesystem"` ✅
  - Current: `input: ${tool_input}` ❌  
  - Fix to: `payload: ${context.step_outputs.prepare_input}` ✅

### 2. Deprecated Output Format
- [ ] Replace `output_key` with modern `output: to:` format
  - Line 46: `output_key: tool_output` ❌
  - Fix to: `output: to: respond` ✅

### 3. Incorrect Function Call Format
- [ ] Update function call to use full path
  - Current: `function: mcp_call` ❌
  - Fix to: `function: langswarm.core.utils.workflows.functions.mcp_call` ✅

## 📝 Required Changes

### workflows.yaml Fixes
```yaml
# CURRENT (Broken)
- id: call_tool
  function: mcp_call
  args:
    tool_id: ${selected_function}
    input: ${tool_input}
  retry: 2
  output_key: tool_output

# FIXED VERSION
- id: call_tool
  function: langswarm.core.utils.workflows.functions.mcp_call
  args:
    mcp_url: "local://filesystem"
    payload: ${context.step_outputs.prepare_input}
  retry: 2
  output:
    to: respond
```

## ✅ Already Compliant

- [x] Has required files: `main.py`, `agents.yaml`, `workflows.yaml`, `readme.md`, `template.md`
- [x] Class name follows convention: `FilesystemMCPTool`
- [x] Has `_bypass_pydantic = True`
- [x] Uses standardized error responses
- [x] Documentation files are lowercase

## ⚠️ Minor Improvements Needed

### 1. Agent Model Updates
- [ ] Consider updating agents from `gpt-4` to `gpt-4o` for optimal performance
- Current models in `agents.yaml` are acceptable but not optimal

### 2. Step Reference Validation
- [ ] Verify all `${context.step_outputs.*}` references point to correct step IDs
- [ ] Ensure step flow is logical and complete

## 🧪 Testing Required

- [ ] Test workflow execution after fixes
- [ ] Verify `local://filesystem` URL works correctly
- [ ] Test error handling scenarios
- [ ] Validate step-to-step data flow

## 📅 Implementation Order

1. **IMMEDIATE**: Fix broken `mcp_call` parameters (Critical)
2. **HIGH**: Update output format to modern standard
3. **MEDIUM**: Update function call to use full path
4. **LOW**: Consider model upgrades to gpt-4o

## 🎯 Success Criteria

- [ ] Workflow executes without errors
- [ ] All steps reference valid previous steps
- [ ] Uses modern workflow patterns
- [ ] Follows developer guide standards
- [ ] Passes integration tests

---

**Estimated Fix Time**: 30 minutes  
**Risk Level**: High (broken functionality)  
**Dependencies**: None - can be fixed independently
