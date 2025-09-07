Here is a comprehensive list of **rules and restrictions** when writing a `workflows.yaml` file for LangSwarm:

---

## ✅ STRUCTURE & HIERARCHY

### 1. **Top-Level Structure**

```yaml
workflows:
  my_workflow_id:
    - id: step_1
      ...
    - id: step_2
      ...
```

* Each workflow has a unique ID under `workflows`.
* Each workflow is a list of **ordered steps**.

---

## ✅ STEP TYPES

A step must include **either**:

* `function` → to run a Python function
* `agent` → to chat with an agent
* `no_mcp` → to let an agent select and call one of multiple tools

A step may **not include more than one** of these execution types.

---

## ✅ COMMON STEP KEYS

### `id` (required)

* Must be unique within the workflow.

### `description` (optional)

* Used for logging/debugging; not required for functionality.

### `async` (optional, workflow-level only)

* `true` or `false`; affects parallelism in execution.

### `output.to` (required unless terminal step)

* Target for the step's result.
* Can be:

  * another step's `id`
  * `"user"` to return result to user
  * an `agent_id` if looping or returning to a specific agent

---

## ✅ FUNCTION STEP RULES

```yaml
- id: some_step
  function: some.module.function_name
  args:
    input1: ${context.something}
    input2: some_static_value
  output:
    to: next_step
```

* `function` must be a fully qualified Python path (unless inline `script` is provided).
* `args` must be key-value pairs.
* Arguments can use variable interpolation with `${...}` syntax.
* You can include an inline `script:` block that defines the function.

#### ➕ Supported types in function `args`:

* Strings, numbers, booleans, lists, and dicts
* LangSwarm variables using `${...}` syntax (see below)

---

## ✅ AGENT STEP RULES

```yaml
- id: ask_agent
  agent: some_agent_id
  input: |
    Hello, summarize this: ${context.step_outputs.previous_step}
  output:
    to: another_step
```

* `agent` must reference an `agent_id` defined in `agents.yaml`.
* `input` must be a string (supports multiline and `${...}` interpolation).
* No `args` section is allowed in agent steps.

---

## ✅ VARIABLE INTERPOLATION (`${...}`)

### ✔ Supported

* Dot-style path: `${context.step_outputs.some_step_id}`
* Nested values: `${context.some_key.sub_key}`
* Indexed access: `${context.some_list[0]}` ✅ *(only for lists/tuples, not dicts)*
* Values from:

  * `context.user_input`
  * `context.excel_path` (or any other injected variable)
  * `context.step_outputs.step_id`

### ❌ Not supported

* Bracket notation for dicts: `${context.step_outputs["some_key"]}` ❌
* Expressions: `${some_value + 1}` ❌
* Function calls: `${len(something)}` ❌
* Logic (e.g., `if`, `else`) ❌

---

## ✅ `no_mcp` STEP RULES

```yaml
- id: flexible_tool_use
  no_mcp:
    tools:
      - clarify
      - my_tool:
          repeatable: true
          retry_limit: 3
          return_to_agent: true
  agent: some_agent_id
  input: Give me a tool output
  output:
    to: fallback
```

* Agent chooses tool to call.
* Each tool must be registered in `tools.yaml`.
* Optional tool-specific configs like `repeatable`, `retry_limit`, `return_to_agent`, `return_to`.

---

## ✅ ADVANCED: INLINE FUNCTION

```yaml
- id: my_math
  function: add_one
  script: |
    def add_one(val, **kwargs):
        return val + 1
  args:
    val: ${context.step_outputs.previous_step}
  output:
    to: next_step
```

* `script` must define a function matching the `function` name.
* LangSwarm will `exec()` the code and call it directly.

---

## ✅ SPECIAL OUTPUT TARGETS

```yaml
output:
  to: user              # Final output returned to user
  to: other_step_id     # Continue to another step
  to: some_agent_id     # Return to a specific agent
```

You can dynamically redirect output in function steps using conditional logic inside the function or post-processing via tool options.

---

## ✅ RETURNED DATA TYPES

By default, results from steps are stored in:

```python
context["step_outputs"]["step_id"]
```

LangSwarm automatically serializes outputs. For DataFrames, return:

```python
return {
  "__type__": "DataFrame",
  "value": df.to_dict(orient="split")
}
```

LangSwarm can restore them back to real DataFrames later in `_resolve_input()`.

---

## 🚫 LIMITATIONS

* Only **one workflow** can run per `run_workflow()` call.
* No native support (yet) for branching logic or conditionals without custom Python.
* Circular dependencies between steps are not supported.
* You cannot pass actual Python objects (e.g., functions, classes) through YAML.

---

## 🧪 DEBUGGING TIPS

* All resolved values are shown in the debug logs.
* Errors in resolving `${...}` show a warning in stdout:
  `⚠️ Failed to resolve: ${...} — KeyError...`
* Use inline `script:` steps for value manipulation instead of YAML math or logic.

---

Would you like a downloadable Markdown or sample YAML template with these rules applied?
