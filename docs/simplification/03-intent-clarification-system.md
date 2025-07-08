# 03 - Intent-Based Tool Clarification System

**Status**: ✅ **IMPLEMENTED**  
**Date**: 2024  
**Priority**: High  

## Summary

Enhanced the intent-based tool clarification system with modular system prompt templates and cross-workflow clarification capabilities.

## What Was Implemented

### 1. Modular System Prompt Templates ✅

Created a modular template fragment system that conditionally includes instruction fragments based on agent configuration:

```
langswarm/core/templates/fragments/
├── clarification.md                    # Basic clarification instructions  
├── retry.md                           # Retry behavior instructions
├── intent_workflow.md                 # Intent-based tool calling patterns
└── cross_workflow_clarification.md   # Cross-workflow clarification scopes
```

**Key Features:**
- **Automatic detection**: Fragments included based on agent capabilities 
- **Conditional rendering**: Only include relevant instructions for each agent
- **Maintainable**: Centralized prompt management with modular components

### 2. Cross-Workflow Clarification ✅

Enhanced clarification system with scope-based routing for complex workflow hierarchies:

**Clarification Scopes:**
- `"local"` (default): Ask previous step or within current workflow
- `"parent_workflow"`: Bubble up to the calling workflow/agent  
- `"root_user"`: Go all the way back to the original user

**Example Usage:**
```json
{
  "response": "I need input from the main workflow calling this tool.",
  "tool": "clarify",
  "args": {
    "prompt": "Which environment are you deploying to?",
    "scope": "parent_workflow", 
    "context": "Found configs for staging, prod, and dev environments"
  }
}
```

## Implementation Details

### Files Modified/Created

**Core Framework:**
- `langswarm/core/config.py`: Enhanced `_render_system_prompt()` with modular fragments
- `langswarm/core/config.py`: Added `_handle_cross_workflow_clarification()` method
- `langswarm/core/config.py`: Added `_resume_after_clarification()` method
- `langswarm/core/config.py`: Enhanced clarify tool handling in workflow executor

**Template Fragments:**
- `langswarm/core/templates/fragments/clarification.md`
- `langswarm/core/templates/fragments/retry.md`  
- `langswarm/core/templates/fragments/intent_workflow.md`
- `langswarm/core/templates/fragments/cross_workflow_clarification.md`

**Documentation:**
- `docs/intent-clarification-system.md`: Comprehensive system documentation
- `docs/clarification-enhancement-example.md`: Basic examples and flow

### Integration Points

**Automatic Fragment Inclusion Logic:**
```python
# Include clarification fragment if agent has intent-based tools OR retry capabilities
has_intent_tools = self._agent_has_intent_tools(agent_tools)
has_retry_capability = self._agent_has_retry_capability(agent_tools, agent_config)

if has_intent_tools or has_retry_capability:
    # Include clarification.md fragment
    
if has_retry_capability:
    # Include retry.md fragment
    
if has_intent_tools:
    # Include intent_workflow.md fragment
    
has_cross_workflow_capability = has_intent_tools or self._agent_has_cross_workflow_tools(agent_tools)
if has_cross_workflow_capability:
    # Include cross_workflow_clarification.md fragment
```

**Cross-Workflow Routing:**
```python
def _handle_cross_workflow_clarification(self, step_id: str, prompt: str, context: str, scope: str) -> str:
    if scope == "parent_workflow":
        # Route to parent workflow via special output
        parent_clarification = {"type": "clarification_request", "data": clarification_data}
        self._handle_output(step_id, {"to": "parent_workflow_clarification"}, parent_clarification)
        
    elif scope == "root_user":
        # Route all the way back to the original user
        self._handle_output(step_id, {"to": "user"}, root_clarification)
```

## Benefits Achieved

### ✅ **Architectural Improvements**
- **Modular prompts**: System prompts now scale cleanly with new capabilities
- **Conditional instructions**: Agents only get relevant instructions
- **Maintainable templates**: Centralized fragment management

### ✅ **Enhanced Workflow Communication**  
- **Cross-workflow clarification**: Tool workflows can ask parent workflows for input
- **Root user access**: Deep workflows can reach back to original user
- **Context preservation**: Workflow state maintained during clarification cycles

### ✅ **Backward Compatibility**
- **Existing retry integration**: Works with current `retry: 2-3` configurations
- **Progressive enhancement**: Existing agents get enhanced capabilities automatically
- **No breaking changes**: All existing functionality preserved

### ✅ **Developer Experience**
- **Clear patterns**: Consistent clarification API across all tools
- **Rich examples**: Comprehensive documentation with real-world scenarios  
- **Easy configuration**: Agent capabilities automatically detected

## Usage Examples

### Basic Agent Configuration
```yaml
agents:
  - id: filesystem_agent
    model: gpt-4o
    tools: ["filesystem"]  # Automatically gets intent-based capabilities
    config:
      retry_enabled: true  # Automatically gets retry instructions
```

**Generated System Prompt includes:**
- Base response format instructions
- Clarification capabilities fragment  
- Retry & error recovery fragment
- Intent-based tool workflows fragment
- Cross-workflow clarification fragment

### Progressive Clarification Flow
```
1. User: "read configuration file"
   ↓
2. Tool Agent: "Found 3 config files, which environment?" (parent_workflow scope)
   ↓  
3. Main Agent: "Which environment are you working with?" (to user)
   ↓
4. User: "staging"
   ↓
5. Tool Agent: "Reading config-staging.yml..." (resumes with context)
```

## Impact on LangSwarm

This enhancement significantly improves the conversational capabilities of intent-based tool workflows:

1. **Better User Experience**: Clarifications are routed to the right level (tool → workflow → user)
2. **Smarter Agents**: System prompts are tailored to each agent's actual capabilities  
3. **Robust Workflows**: Failed tool calls can recover through progressive clarification
4. **Maintainable Codebase**: Modular prompt system scales with new features

## Future Enhancements

Potential areas for expansion:
- **Async clarification**: Non-blocking clarification requests
- **Clarification history**: Learning from previous clarification patterns
- **Smart routing**: AI-powered determination of optimal clarification scope
- **UI integration**: Visual clarification flows in web interfaces

## Completion Status

**✅ COMPLETE** - The intent-based tool clarification system is fully implemented and ready for production use. All components integrate seamlessly with the existing LangSwarm architecture while providing powerful new capabilities for complex workflow scenarios. 