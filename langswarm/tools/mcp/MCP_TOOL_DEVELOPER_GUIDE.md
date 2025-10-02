# 🛠️ LangSwarm MCP Tool Developer Guide

**Version**: 2024.1  
**Last Updated**: December 2024  
**Purpose**: Definitive guide for building consistent, standards-compliant MCP tools in LangSwarm

---

## 📋 Table of Contents

1. [Critical Findings & Inconsistencies](#critical-findings--inconsistencies)
2. [Standards & Requirements](#standards--requirements)
3. [Directory Structure](#directory-structure)
4. [Core Implementation Patterns](#core-implementation-patterns)
5. [Workflow Standards](#workflow-standards)
6. [Agent Configuration](#agent-configuration)
7. [Documentation Requirements](#documentation-requirements)
8. [Common Pitfalls & Solutions](#common-pitfalls--solutions)
9. [Migration Guide](#migration-guide)
10. [Development Checklist](#development-checklist)

---

## 🚨 Critical Findings & Inconsistencies

### Major Issues Found in Current Codebase

#### 1. **Inconsistent Workflow Function Calls** ⚠️

**Found Two Different Patterns:**

❌ **BROKEN Pattern (filesystem tool):**
```yaml
- id: call_tool
  function: mcp_call                    # ❌ Short form (inconsistent)
  args:
    tool_id: ${selected_function}       # ❌ Wrong parameter (should be mcp_url)
    input: ${tool_input}                # ❌ Wrong parameter (should be payload)
  output_key: tool_output               # ❌ Deprecated format
```

✅ **CORRECT Pattern (mcpgithubtool):**
```yaml
- id: call_tool
  function: langswarm.core.utils.workflows.functions.mcp_call  # ✅ Full path
  args:
    mcp_url: "stdio://github_mcp"       # ✅ Correct parameter
    payload: ${context.step_outputs.build_input}  # ✅ Correct parameter
  output:
    to: summarize                       # ✅ Modern format
```

#### 2. **Model Inconsistencies** ⚠️

**Found Mixed Model Usage:**
- ✅ **sql_database**: Uses `gpt-4o` (correct)
- ✅ **gcp_environment**: Uses `gpt-4o` (correct)  
- ⚠️ **daytona_environment**: Uses `gpt-4` (acceptable but not optimal)
- ⚠️ **bigquery_vector_search**: Uses `gpt-4` (acceptable but not optimal)

#### 3. **Output Format Inconsistencies** ⚠️

**Three Different Output Formats Found:**
- ❌ `output_key: step_name` (deprecated, found in filesystem)
- ✅ `output: to: step_name` (correct modern format)
- ⚠️ Mixed usage across tools

#### 4. **Documentation File Naming** ⚠️

**Inconsistent Documentation Files:**
- ✅ Most tools: `readme.md` (lowercase)
- ❌ Some tools: `README.md` (uppercase) 
- ❌ **mcpgithubtool**: Missing `readme.md` entirely

#### 5. **Missing Features** ⚠️

**Tools Missing Standard Components:**
- **mcpgithubtool**: No `readme.md` documentation
- **daytona_self_hosted**: No `agents.yaml` or `workflows.yaml`
- **remote**: No `agents.yaml`, `workflows.yaml`, `template.md`, or `readme.md`

---

## ✅ Standards & Requirements

### Mandatory Standards (Non-Negotiable)

#### Class Implementation
```python
class ToolNameMCPTool(BaseTool):
    """REQUIRED: Class name MUST end with 'MCPTool'"""
    
    # REQUIRED: Must have Pydantic bypass
    _bypass_pydantic = True
    
    def __init__(self, tool_id: str = "tool_name", **kwargs):
        super().__init__(tool_id=tool_id, **kwargs)
    
    def run(self, input_data: dict) -> dict:
        """REQUIRED: Main execution method"""
        pass
```

### 2. Agent Configuration (`agents.yaml`)

Before implementing workflows, define your agents. Agent configuration is foundational since workflows reference these agents.

#### ✅ Standard Agent Structure
```yaml
agents:
  # Required: Input processing agent
  input_normalizer:
    description: "Normalizes user input for consistent processing"
    model: "gpt-4o"
    instructions: |
      You normalize user input for {tool_name} operations.
      Handle both user_input and user_query parameters for backwards compatibility.
    response_mode: "conversational"

  # Required: Main execution agent  
  tool_executor:
    description: "Main execution agent for {tool_name}"
    model: "gpt-4o"
    instructions: |
      You execute {tool_name} operations with proper validation.
      Return valid JSON for the {tool_name} tool.
    tools:
      - {tool_name}
    response_mode: "conversational"

  # Required: Output formatting agent
  response_formatter:
    description: "Formats results for user presentation"
    model: "gpt-4o"
    instructions: |
      Format {tool_name} results clearly for users.
    response_mode: "conversational"
```

#### Agent Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `description` | string | ✅ Yes | Brief description of agent's role |
| `model` | string | ✅ Yes | LLM model (minimum `gpt-4o`) |
| `instructions` | string | ✅ Yes | Detailed system prompt for the agent |
| `tools` | array | ⚠️ Conditional | List of tools agent can use (for execution agents) |
| `response_mode` | string | ✅ Yes | How agent responds (see table below) |
| `memory` | object | ❌ No | Memory configuration (optional) |
| `config` | object | ❌ No | Agent-specific configuration (optional) |

#### Response Mode Options

| Mode | Description | When to Use |
|------|-------------|-------------|
| `"conversational"` | Natural language responses | Most agents (default) |
| `"structured"` | JSON/structured output only | Data processing agents |
| `"silent"` | Minimal output | Background processing agents |

#### Model Requirements
```yaml
agents:
  agent_name:
    model: "gpt-4o"  # REQUIRED: Minimum model standard
```

**⚠️ Critical**: Never use models below `gpt-4o` for production tools. Lower models lack the reliability and capability needed for consistent tool execution.

### 3. Workflow Definition (`workflows.yaml`)

After defining agents, create workflows that orchestrate them. Start with the workflow structure before defining individual steps.

#### ✅ Standard Workflow Structure
```yaml
workflows:
  main_workflow: "primary_workflow_id"  # REQUIRED: Points to the default workflow
  
  - id: primary_workflow_id
    description: "Primary workflow for {tool_name} operations"
    steps:
      # Define individual steps here
```

**Critical Structure Requirements:**
- `main_workflow:` must be the first item under `workflows:`
- **IMPORTANT**: Each tool should have exactly ONE workflow (the main_workflow)
- Use steps, conditions, and routing within the single workflow for different operations
- Multiple workflows should only be used in extremely rare circumstances
- This keeps tools simple, maintainable, and predictable

> 📚 **For detailed conditional routing documentation, see**: `docs/workflow-conditional-routing.md`

#### ✅ Single Workflow Design Patterns

Instead of creating multiple workflows, use these patterns within your main workflow:

**1. Output Conditional Routing (Recommended)**
```yaml
- id: classify_intent
  agent: intent_classifier
  input: "Classify user request: ${user_input}"
  output:
    to:
      - condition:
          if: "${context.step_outputs.classify_intent.type} == 'search'"
          then: handle_search
          else: handle_other

- id: handle_search
  tool: search_tool
  input: "Search query: ${user_input}"
  output:
    to: user

- id: handle_other
  agent: general_handler
  input: "Process request: ${user_input}"
  output:
    to: user
```

**2. Switch/Case Routing**
```yaml
- id: categorize_request
  agent: categorizer
  input: "${user_input}"
  output:
    to:
      - condition:
          switch: "${context.step_outputs.categorize_request.category}"
          cases:
            search: search_workflow
            create: create_workflow
            update: update_workflow
          default: general_workflow
```

**3. Step-Level Conditions (Advanced)**
```yaml
- id: optional_step
  condition: "${context.step_outputs.classify_intent.type} == 'advanced_operation'"
  agent: specialized_agent
  input: "Process advanced request: ${user_input}"
  output:
    to: next_step
```

**3. Dynamic Parameter Building**
```yaml
- id: build_parameters
  agent: parameter_builder
  input: |
    Operation: ${context.step_outputs.classify_intent}
    User request: ${user_input}
    
    Build appropriate parameters for the ${context.step_outputs.classify_intent} operation.
```

### 4. Workflow Step Types

When defining workflow steps, understand the different types available:

#### Agent Steps (Most Common)
```yaml
- id: step_name                    # Unique identifier for the step
  agent: agent_name                # Reference to agent in agents.yaml
  input: |                         # Input to the agent
    User request: ${user_input}
  output:                          # Where to send the output
    to: next_step_id              # ID of the next step (or "user")
```

#### MCP Tool Call Steps (Correct Syntax)
```yaml
# ✅ CORRECT: Use full function path for MCP tool calls
- id: step_name
  function: langswarm.core.utils.workflows.functions.mcp_call
  args:
    mcp_url: "local://tool_name"  # REQUIRED: MCP URL
    payload: ${context.step_outputs.previous_step}  # REQUIRED: Payload
  output:
    to: next_step  # REQUIRED: Output routing
```

#### ❌ INVALID: Direct Tool References
```yaml
# ❌ WRONG: This syntax is NOT supported
- id: step_name
  tool: tool_name  # This is invalid!
  input: "${context.step_outputs.previous_step}"
```

#### General Function Call Standard

All workflow function calls follow this basic pattern:

```yaml
- id: step_name
  function: module.path.to.function  # Full function path
  args:                              # Function-specific arguments
    param1: value1
    param2: value2
  output:
    to: next_step
```

#### Function Call Types

##### 1. MCP Tool Calls (Most Common)
Used to call MCP tools with proper isolation and parameter handling:

```yaml
- id: call_mcp_tool
  function: langswarm.core.utils.workflows.functions.mcp_call
  args:
    mcp_url: "local://tool_name"    # Tool execution context
    payload: ${context.step_outputs.previous_step}  # Tool parameters
  output:
    to: next_step
```

##### 2. Utility Function Calls
Used for data processing, validation, or other utilities:

```yaml
- id: process_data
  function: langswarm.core.utils.workflows.functions.external_function
  args:
    module_path: "/path/to/utility.py"
    func_name: "process_data"
    args: [${context.step_outputs.raw_data}]
  output:
    to: next_step
```

##### 3. Health Check Calls
Used for system monitoring and validation:

```yaml
- id: check_service
  function: langswarm.core.utils.workflows.functions.health_check
  args:
    url: "http://service-endpoint"
    timeout: 5
  output:
    to: next_step
```

#### MCP URL Patterns Explained

The `mcp_url` parameter determines how and where the MCP tool executes:

| Pattern | Description | Use Case | Performance |
|---------|-------------|----------|-------------|
| `local://tool_name` | In-process execution | Development, simple tools | ⚡ Fastest (0ms overhead) |
| `stdio://tool_name` | Container-based stdio | Isolated execution, production | 🐢 Slower (container startup) |
| `http://service_url` | Remote HTTP service | Distributed systems | 🌐 Network dependent |
| `ws://service_url` | WebSocket connection | Real-time communication | 🔄 Persistent connection |

**Local Mode Execution Flow:**
```
Workflow Step → Local Registry → Direct Function Call → Immediate Response
```

**Container Mode Execution Flow:**
```
Workflow Step → Docker Container → Stdio Communication → Response Processing
```

**HTTP Mode Execution Flow:**
```
Workflow Step → HTTP Request → Remote Service → HTTP Response → Processing
```



---

## 📁 Directory Structure

### Required Files Structure

```
langswarm/mcp/tools/{tool_name}/
├── __init__.py                 # ✅ REQUIRED - Tool package initialization
├── main.py                     # ✅ REQUIRED - Core tool implementation  
├── agents.yaml                 # ✅ REQUIRED - Agent definitions
├── workflows.yaml              # ✅ REQUIRED - Workflow definitions
├── readme.md                   # ✅ REQUIRED - User documentation (lowercase!)
├── template.md                 # ✅ REQUIRED - LLM system instructions
└── examples/                   # ⚠️ OPTIONAL - Usage examples
    └── example_config.yaml
```

### Conditional Files (Case-by-Case)

| File | When Required | Example Tools |
|------|---------------|---------------|
| `_util_modules.py` | Complex tools needing shared utilities | `bigquery_vector_search/_bigquery_utils.py` |
| `docker-compose.yml` | Tools requiring containerization | `workflow_executor/`, `daytona_self_hosted/` |
| `Dockerfile` | Tools with custom container needs | `daytona_self_hosted/` |
| `requirements.txt` | Tools with unique dependencies | `daytona_self_hosted/` |
| `UPDATE_SUMMARY.md` | Tools with significant recent changes | `tasklist/` |

---

## 🗂️ Core Implementation Patterns

### 1. Tool Class Standards

#### ✅ Standard Implementation
```python
from langswarm.synapse.tools.base import BaseTool
from langswarm.tools.mcp._error_standards import create_error_response, ErrorTypes
from datetime import datetime

class ExampleMCPTool(BaseTool):
    """
    NAMING CONVENTION: {ToolName}MCPTool
    Examples: BigQueryVectorSearchMCPTool, SQLDatabaseMCPTool
    """
    
    # CRITICAL: Always include this for workflow compatibility
    _bypass_pydantic = True
    
    def __init__(self, tool_id: str = "example_tool", **kwargs):
        super().__init__(tool_id=tool_id, **kwargs)
        # Tool-specific initialization
    
    def run(self, input_data: dict) -> dict:
        """
        REQUIRED: Main execution method
        
        Args:
            input_data: User parameters as dictionary
            
        Returns:
            dict: Standardized response format
        """
        try:
            # 1. Parameter validation
            if not self._validate_input(input_data):
                return create_error_response(
                    error_message="Invalid input parameters",
                    error_type=ErrorTypes.PARAMETER_VALIDATION,
                    tool_name=self.tool_id
                )
            
            # 2. Core tool logic
            result = self._execute_operation(input_data)
            
            # 3. Success response
            return {
                "success": True,
                "result": result,
                "metadata": {
                    "tool_id": self.tool_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            return create_error_response(
                error_message=str(e),
                error_type=ErrorTypes.EXECUTION_ERROR,
                tool_name=self.tool_id
            )
    
    def _validate_input(self, input_data: dict) -> bool:
        """Validate input parameters"""
        return True
    
    def _execute_operation(self, input_data: dict):
        """Execute core tool operation"""
        pass
```

### 2. Error Handling Standards

#### Use Standardized Error System
```python
from langswarm.tools.mcp._error_standards import (
    create_error_response, 
    create_parameter_error,
    create_authentication_error,
    create_connection_error,
    ErrorTypes
)

# Parameter validation error
return create_parameter_error(
    parameter_name="required_field",
    expected_value="string",
    provided_value=input_data.get("required_field"),
    tool_name=self.tool_id
)

# Authentication error
return create_authentication_error(
    missing_credential="API_KEY",
    tool_name=self.tool_id
)

# Connection error
return create_connection_error(
    service_name="External API",
    details="Service returned 503",
    tool_name=self.tool_id
)
```

---

## 🔄 Workflow Standards

### Correct Function Call Patterns

#### ✅ Standard MCP Function Call
```yaml
workflows:
  - id: main_workflow
    description: "Primary tool workflow"
    steps:
      - id: normalize_input
        agent: input_normalizer
        input: |
          user_input: ${user_input}
          user_query: ${user_query}
        output:
          to: normalized_request

      - id: execute_tool
        function: langswarm.core.utils.workflows.functions.mcp_call
        args:
          mcp_url: "local://tool_name"  # Choose: local://, stdio://, http://
          payload: ${context.step_outputs.normalize_input}
        output:
          to: tool_result

      - id: format_response
        agent: response_formatter  
        input: |
          Result: ${context.step_outputs.execute_tool}
          Original request: ${context.step_outputs.normalize_input}
        output:
          to: user
```

#### MCP URL Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| `local://tool_name` | In-process execution (fastest) | Development, simple tools |
| `stdio://tool_name` | Container-based execution | Isolated tools, production |
| `http://service_url` | Remote HTTP service | Distributed systems |

#### Internal Function Calls vs MCP Tool Calls

**Important Distinction**: There are two different types of function calls:

##### 1. Internal Tool Functions (Within the Tool)
For functions within your MCP tool (like utility functions, print statements, etc.), you call them directly in Python:

```python
class MyMCPTool(BaseTool):
    def run(self, input_data: dict) -> dict:
        # Direct function call within the tool
        self._log_operation(input_data)  # ✅ Direct call
        result = self._process_data(input_data)  # ✅ Direct call
        return result
    
    def _log_operation(self, data):
        """Internal utility function"""
        print(f"Processing: {data}")  # ✅ Direct print statement
    
    def _process_data(self, data):
        """Internal processing function"""
        return {"processed": data}
```

##### 2. External MCP Tool Calls (From Workflows)
For calling MCP tools from workflows, you use `local://tool_name`:

```yaml
# This calls the MCP tool from a workflow
- id: use_tool
  function: langswarm.core.utils.workflows.functions.mcp_call
  args:
    mcp_url: "local://my_tool"  # ✅ Calls the tool's run() method
    payload: ${context.step_outputs.input_data}
```

**No Endless Loop**: Using `local://tool_name` in a workflow calls the tool's `run()` method once and returns the result. It doesn't create loops because:

1. **Workflow → Tool**: Workflow calls tool via `local://` 
2. **Tool Execution**: Tool runs its `run()` method internally
3. **Result Return**: Tool returns result to workflow
4. **Workflow Continues**: Workflow processes result and moves to next step

The `local://` URL is a **one-way call** from workflow to tool, not a recursive reference.

### Step Reference Standards

#### ✅ Correct Step References
```yaml
# Reference format: ${context.step_outputs.step_id}
input: |
  Previous result: ${context.step_outputs.normalize_input}
  Tool output: ${context.step_outputs.execute_tool}
```

#### ❌ Common Reference Mistakes
```yaml
# DON'T: Reference output names instead of step IDs
input: ${context.step_outputs.normalized_request}  # ❌ Wrong

# DON'T: Use old variable patterns  
input: ${normalized_input}  # ❌ Deprecated

# DON'T: Mix reference styles
input: ${previous_output}   # ❌ Inconsistent
```

### Output Format Standards

#### ✅ Modern Output Format
```yaml
output:
  to: next_step_id  # References the ID of the next step
```

#### ❌ Deprecated Formats
```yaml
output_key: step_name    # ❌ Old format - don't use
output: step_name        # ❌ Incomplete format
```

#### Output Format Clarification

**Important**: `output_key` is deprecated but still functional in some legacy workflows. However, it's inconsistent and should be avoided.

##### ❌ Legacy Format (Deprecated)
```yaml
output_key: result_name  # ❌ Sets output to a key but inconsistent routing
```

#### Complex Routing Scenarios

**Advanced Use Case**: In some complex workflows, you might need `output_key` for specific parameter extraction, but this is rare and should be avoided when possible.

##### ❌ Complex Routing (Discouraged)
```yaml
- id: extract_specific_data
  agent: data_extractor
  input: ${complex_input}
  output_key: extracted_field  # ❌ Only use if absolutely necessary
```

##### ✅ Better Approach (Recommended)
```yaml
- id: extract_specific_data
  agent: data_extractor
  input: ${complex_input}
  output:
    to: process_extracted_data

- id: process_extracted_data
  agent: field_processor
  input: |
    Extracted data: ${context.step_outputs.extract_specific_data}
    Please process the specific field needed.
  output:
    to: next_step
```

**Best Practice**: Use explicit step routing with descriptive agent instructions instead of relying on `output_key` for complex parameter extraction. This makes workflows more maintainable and debuggable.

##### ✅ Modern Format (Recommended)
```yaml
output:
  to: next_step_id  # ✅ References the ID of the next step OR "user"
```

**Why Modern Format is Better:**
- **Explicit routing**: Clear where output goes next
- **Consistent behavior**: Same pattern across all tools
- **Better debugging**: Easy to trace workflow flow
- **Future-proof**: Supports advanced routing features

**Best Practice**: Always use `output: to: step_id` even when you want to store results to a specific key. The workflow engine handles key management automatically.

---

## 👥 Agent Configuration Standards

### Model Standards

#### ✅ Recommended Models
```yaml
agents:
  primary_agent:
    model: "gpt-4o"           # ✅ PREFERRED - Most capable
    # OR
    model: "gpt-4"            # ✅ ACCEPTABLE - Good performance
    
  # NEVER use these:
  # model: "gpt-3.5-turbo"   # ❌ FORBIDDEN - Unreliable for production
```

### Agent Structure Standards

#### ✅ Standard Agent Configuration
```yaml
agents:
  input_normalizer:
    description: "Normalizes user input for consistent processing"
    model: "gpt-4o"
    instructions: |
      You normalize user input for {tool_name} operations.
      
      CAPABILITIES:
      - Handle both user_input and user_query parameters
      - Clean and standardize requests
      - Maintain backwards compatibility
      
      INPUT HANDLING:
      - If user_input is provided, use it
      - If user_query is provided and user_input is empty, use user_query
      - Return normalized, clean request text
    
    response_mode: "conversational"

  tool_executor:
    description: "Main execution agent for {tool_name}"
    model: "gpt-4o"
    instructions: |
      You execute {tool_name} operations with proper validation.
      
      SECURITY REQUIREMENTS:
      - Always validate user inputs
      - Respect configuration limits
      - Use parameterized operations when possible
      
      OUTPUT FORMAT:
      Return valid JSON for the {tool_name} tool.
    
    tools:
      - {tool_name}
    
    response_mode: "conversational"

  response_formatter:
    description: "Formats results for user presentation"
    model: "gpt-4o"
    instructions: |
      Format {tool_name} results clearly for users.
      
      - Explain what was accomplished
      - Highlight key findings
      - Suggest follow-up actions when relevant
      - Keep technical details accessible
    
    response_mode: "conversational"
```

The agent configuration parameters table was already added above. Here's the complete reference:

#### Complete Agent Configuration Reference

| Parameter | Type | Required | Description | Examples |
|-----------|------|----------|-------------|----------|
| `description` | string | ✅ Yes | Brief description of agent's role | "Normalizes user input", "Executes tool operations" |
| `model` | string | ✅ Yes | LLM model (minimum `gpt-4o`) | `"gpt-4o"`, `"gpt-4"` |
| `instructions` | string | ✅ Yes | Detailed system prompt for the agent | Multi-line YAML string with role definition |
| `tools` | array | ⚠️ Conditional | List of tools agent can use | `["tool_name"]` (only for execution agents) |
| `response_mode` | string | ✅ Yes | How agent responds (see detailed table below) | `"conversational"`, `"structured"`, `"silent"` |
| `memory` | object | ❌ No | Memory configuration | `{adapter: "langchain", config: {...}}` |
| `config` | object | ❌ No | Agent-specific configuration | Tool-specific settings |

#### Response Mode Detailed Reference

| Mode | Behavior | Output Format | Use Cases | Examples |
|------|----------|---------------|-----------|----------|
| `"conversational"` | Natural language responses with explanations | Human-readable text with context | Most agents, user-facing interactions | Input normalizers, formatters |
| `"structured"` | Strict JSON/structured output only | Machine-readable data structures | Data processing, parameter building | Parameter builders, validators |
| `"silent"` | Minimal output, focus on tool execution | Reduced verbosity, essential info only | Background processing, utilities | System monitors, cleanup agents |
| `"streaming"` | Real-time response streaming | Continuous output flow | Real-time applications | Live data processors |
| `"debug"` | Verbose output with debugging info | Detailed execution logs | Development and troubleshooting | Debug agents, diagnostics |

### Required Agents

Every tool should implement these standard agents:

1. **`input_normalizer`**: Standardizes user input
2. **`tool_executor`**: Main execution logic  
3. **`response_formatter`**: Output formatting

### Agent Naming Conventions

| Agent Type | Naming Pattern | Examples |
|------------|----------------|----------|
| **Input Processing** | `*_normalizer`, `*_parser` | `input_normalizer`, `request_parser` |
| **Execution** | `*_executor`, `*_processor` | `tool_executor`, `query_processor` |
| **Validation** | `*_validator`, `*_checker` | `parameter_validator`, `security_checker` |
| **Output** | `*_formatter`, `*_presenter` | `response_formatter`, `result_presenter` |

---

## 📚 Documentation Requirements

### File Naming Standards

#### ✅ Correct Documentation Files
```
readme.md        # ✅ User documentation (lowercase)
template.md      # ✅ LLM instructions (lowercase)
```

#### ❌ Incorrect Patterns
```
README.md        # ❌ Uppercase - don't use
Template.md      # ❌ Mixed case - don't use
```

### Documentation Structure

#### `readme.md` Requirements
```markdown
# {Tool Name} MCP Tool

Brief description of tool purpose and capabilities.

## Features

- Feature 1: Description
- Feature 2: Description  
- Feature 3: Description

## Configuration

```yaml
tools:
  - id: "tool_id"
    type: "mcp{tool_name}"
    description: "Tool description"
    config:
      parameter1: "value1"
      parameter2: "value2"
```

## Usage Examples

### Basic Usage
[Provide clear example]

### Advanced Usage  
[Provide complex example]

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| param1 | string | Yes | Parameter description |
| param2 | number | No | Parameter description |

## Security Features

- Security feature 1
- Security feature 2

## Error Handling

Common errors and their solutions.

## Troubleshooting

Common issues and fixes.
```

#### `template.md` Requirements
```markdown
# {Tool Name} Tool Instructions

You have access to the {tool_name} tool for [capability description].

## Tool Capabilities

1. **Capability 1**: Detailed description
2. **Capability 2**: Detailed description
3. **Capability 3**: Detailed description

## Usage Patterns

### Direct Tool Calls
For specific operations with known parameters:
```json
{
  "response": "I'll execute that operation.",
  "mcp": {
    "tool": "{tool_name}",
    "method": "operation_name", 
    "params": {"param1": "value1"}
  }
}
```

### Intent-Based Calls
For complex or exploratory requests:
```json
{
  "response": "I'll process that using the {tool_name} workflow.",
  "mcp": {
    "tool": "{tool_name}",
    "intent": "user's natural language request",
    "context": "additional context if needed"
  }
}
```

## Security Guidelines

- Validate all inputs
- Respect configuration limits
- Use appropriate security measures

## Best Practices

1. Use intent-based calls for exploration
2. Use direct calls for specific operations
3. Always explain actions to users
```

---

## 🚨 Common Pitfalls & Solutions

### 1. Workflow Function Call Issues

#### ❌ Problem: Wrong Parameters
```yaml
function: mcp_call
args:
  tool_id: ${tool_name}     # ❌ Wrong parameter
  input: ${user_input}      # ❌ Wrong parameter
```

#### Context-Dependent Parameter Usage

**Important Clarification**: Parameter correctness depends on the function type being called:

##### ✅ Correct for Agent Steps
```yaml
- id: process_request
  agent: input_normalizer
  input: ${user_input}        # ✅ Correct for agent calls
  output:
    to: next_step
```

##### ❌ Incorrect ONLY for MCP Function Calls  
```yaml
- id: call_mcp_tool
  function: langswarm.core.utils.workflows.functions.mcp_call
  args:
    tool_id: ${tool_name}     # ❌ Wrong - should be mcp_url
    input: ${user_input}      # ❌ Wrong - should be payload
```

**Rule**: These parameters (`tool_id`, `input`) are only incorrect when calling MCP functions. They're perfectly valid for agent steps and other function types.


#### ✅ Solution: Correct Parameters
```yaml
function: langswarm.core.utils.workflows.functions.mcp_call
args:
  mcp_url: "local://tool_name"  # ✅ Correct
  payload: ${context.step_outputs.previous_step}  # ✅ Correct
```

### 2. Step Reference Errors

#### ❌ Problem: Referencing Non-Existent Steps
```yaml
input: ${context.step_outputs.missing_step}  # ❌ Step doesn't exist
```

#### ✅ Solution: Reference Actual Step IDs
```yaml
# Workflow has step with id: normalize_input
input: ${context.step_outputs.normalize_input}  # ✅ Correct reference
```

### 3. Output Format Issues

#### ❌ Problem: Using Deprecated Formats
```yaml
output_key: result  # ❌ Deprecated
```

#### ✅ Solution: Use Modern Format
```yaml
output:
  to: next_step  # ✅ Modern format
```

### 4. Missing Pydantic Bypass

#### ❌ Problem: Workflow Validation Errors
```python
class MyTool(BaseTool):
    # Missing _bypass_pydantic
    pass
```

#### ✅ Solution: Add Pydantic Bypass
```python
class MyTool(BaseTool):
    _bypass_pydantic = True  # ✅ Required for workflows
```

---

## 🔄 Migration Guide

### Fixing Broken Workflows

#### Step 1: Update Function Calls
```yaml
# BEFORE (broken)
function: mcp_call
args:
  tool_id: ${function}
  input: ${data}
output_key: result

# AFTER (fixed)
function: langswarm.core.utils.workflows.functions.mcp_call  
args:
  mcp_url: "local://tool_name"
  payload: ${context.step_outputs.previous_step}
output:
  to: next_step
```

#### Step 2: Update Step References
```yaml
# BEFORE (broken)
input: ${previous_output}

# AFTER (fixed)  
input: ${context.step_outputs.step_id}
```

#### Step 3: Update Models
```yaml
# BEFORE (suboptimal)
model: gpt-4

# AFTER (optimal)
model: "gpt-4o"
```

### Standardizing Documentation

#### Step 1: Fix File Names
```bash
# Rename uppercase documentation
mv README.md readme.md
mv Template.md template.md
```

#### Step 2: Add Missing Files
```bash
# Create missing documentation
touch readme.md template.md
```

#### Step 3: Standardize Content
Use the templates provided in the Documentation Requirements section.

---

## ✅ Development Checklist

### Pre-Development Planning
- [ ] Define tool functionality and security requirements
- [ ] Choose tool type (local/remote/stdio)
- [ ] Plan workflow steps and agent interactions
- [ ] Review this guide for standards compliance

### Implementation Phase
- [ ] **Class Implementation**
  - [ ] Class name ends with 'MCPTool'
  - [ ] Inherits from BaseTool
  - [ ] Has `_bypass_pydantic = True`
  - [ ] Implements required `run` method
  - [ ] Uses standardized error responses

- [ ] **Workflow Configuration**
  - [ ] Uses correct function call format
  - [ ] Proper mcp_url and payload parameters
  - [ ] Modern output format (`output: to:`)
  - [ ] Correct step references (`${context.step_outputs.step_id}`)

- [ ] **Agent Configuration**
  - [ ] All agents use `gpt-4o` model
  - [ ] Standard agent naming conventions
  - [ ] Required agents: input_normalizer, tool_executor, response_formatter
  - [ ] Clear, specific instructions

- [ ] **Documentation**
  - [ ] `readme.md` (lowercase) with complete user documentation
  - [ ] `template.md` (lowercase) with LLM instructions
  - [ ] Both files follow standard structure

### Testing Phase
- [ ] Unit tests for core functionality
- [ ] Integration tests with LangSwarm
- [ ] Workflow execution tests
- [ ] Security validation tests
- [ ] Error handling tests

### Quality Assurance
- [ ] **Standards Compliance**
  - [ ] Follows all naming conventions
  - [ ] Uses standardized error responses
  - [ ] Implements proper security measures
  - [ ] No deprecated patterns or formats

- [ ] **Performance Testing**
  - [ ] Tests with various input sizes
  - [ ] Performance benchmarking
  - [ ] Resource usage validation

### Documentation Review
- [ ] User documentation is complete and clear
- [ ] LLM instructions are precise and actionable
- [ ] Code has appropriate comments
- [ ] Examples are tested and working

---

## 🎯 Ambiguous Areas & Case-by-Case Guidelines

### When to Use Different MCP URL Patterns

#### **Local Mode (`local://tool_name`)**
**Use When:**
- Development and testing
- Simple tools without external dependencies
- Maximum performance required
- Tools don't need isolation

**Example Tools:** sql_database, tasklist, dynamic_forms

#### **Stdio Mode (`stdio://tool_name`)**  
**Use When:**
- Production deployment
- Tools need isolation
- External dependencies required
- Security isolation important

**Example Tools:** mcpgithubtool, workflow_executor

#### **HTTP Mode (`http://service_url`)**
**Use When:**
- Distributed systems
- Remote service integration
- Scaling across multiple servers
- External API proxying

### When to Add Utility Modules

#### **Add Utility Module When:**
- Tool has >500 lines of code
- Complex business logic can be extracted
- Multiple similar operations need shared code
- Tool needs specialized helper functions

**Example:** `bigquery_vector_search/_bigquery_utils.py`

#### **Keep in Main File When:**
- Tool is <500 lines
- Logic is straightforward
- No reusable components
- Simple CRUD operations

### When to Add Container Support

#### **Add Docker Support When:**
- Tool has external dependencies
- Requires specific runtime environment
- Needs process isolation
- Has complex setup requirements

**Examples:** `daytona_self_hosted/`, `workflow_executor/`

#### **Skip Containerization When:**
- Tool is pure Python
- No external dependencies
- Simple operations only
- Used in local mode

---

## 📞 Support & Maintenance

### Getting Help
1. **First**: Check this guide thoroughly
2. **Second**: Review working examples (sql_database, tasklist, bigquery_vector_search)
3. **Third**: Test incrementally during development
4. **Last**: Seek assistance with specific issues

### Updating This Guide
This guide should be updated when:
- New patterns emerge
- Standards change
- New tool types are added
- Breaking changes occur

### Tool Maintenance
Regular maintenance tasks:
- Update models to latest versions
- Review and update documentation
- Test with new LangSwarm versions
- Monitor performance and optimize

---

**This guide represents the definitive standards for MCP tool development in LangSwarm. All new tools must follow these patterns exactly, and existing tools should be migrated to compliance.**

---

## 🔍 Appendix: Current Tool Audit Results

### ✅ Compliant Tools
- **sql_database**: Fully compliant with all standards
- **tasklist**: Mostly compliant, modern patterns
- **bigquery_vector_search**: Good structure, minor model updates needed

### ⚠️ Needs Updates  
- **filesystem**: Broken workflow function calls, deprecated output format
- **daytona_environment**: Model updates needed (gpt-4 → gpt-4o)
- **mcpgithubtool**: Missing readme.md documentation

### 🚨 Major Issues
- **daytona_self_hosted**: Missing agents.yaml and workflows.yaml entirely
- **remote**: Missing most standard files (agents, workflows, template, readme)

#### Special Case: Remote Tool

**Important Note**: The `remote` tool is a special universal connector for external MCP services and follows different patterns:

##### Why Remote Tool is Different
- **Universal Connector**: Designed to connect to any external MCP service
- **Dynamic Configuration**: Cannot pre-define agents/workflows since it connects to unknown services
- **Manual Setup Required**: All instructions must be provided manually when configuring agents
- **Proxy Behavior**: Acts as a proxy rather than a standalone tool

##### Remote Tool Usage Pattern
```yaml
# Agent configuration for remote tool
agents:
  remote_connector:
    model: "gpt-4o"
    instructions: |
      You are connecting to a remote MCP service at: {service_url}
      
      Available operations: {operations_list}
      Authentication: {auth_method}
      
      # All instructions must be manually specified here
      # Cannot rely on template.md or pre-defined workflows
    
    tools:
      - remote
```

This is why the `remote` tool legitimately lacks standard files - it's designed to be a universal adapter rather than a specific-purpose tool.

### 📊 Summary Statistics
- **Total Tools Analyzed**: 15
- **Fully Compliant**: 3 (20%)
- **Need Minor Updates**: 8 (53%)
- **Need Major Work**: 4 (27%)

This audit reveals significant inconsistency across the MCP tool ecosystem, highlighting the critical need for this developer guide and systematic updates to existing tools.
