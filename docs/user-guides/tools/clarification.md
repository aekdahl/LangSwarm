# Intent-Based Tool Clarification

The Intent-Based Tool Clarification system empowers LangSwarm agents to handle ambiguity autonomously and safely. Instead of guessing or failing when information is missing, agents can use a structured `clarify` tool to request specific details from their environment, parent workflow, or the human user.

## Overview

Traditional agents often struggle when user requests are ambiguous (e.g., "Delete the file" when there are multiple files). They might guess (dangerous) or fail with a generic text error.

LangSwarm solves this with two key components:
1.  **Modular System Prompts**: Dynamically injected instructions that teach the agent *how* and *when* to clarify.
2.  **Clarification Tool**: A structured mechanism to "escalate" questions up the workflow stack.

## Modular System Prompts

LangSwarm uses a unique "Smart Append" strategy to construct the agent's system prompt. This ensures that even if you bring your own custom prompts (e.g., from **Langfuse** or extensive persona definitions), the agent still receives the necessary technical instructions to use its advanced capabilities.

### How It Works

When an agent initializes:
1.  It checks if you provided a `system_prompt` in the configuration.
2.  **If YES**: It takes your prompt as the base and *appends* the relevant capability fragments (Clarification, Retry, etc.) to the end.
3.  **If NO**: It loads the default LangSwarm `system_prompt_template.md` and appends the fragments.

This guarantees that your agent maintains its specific persona while gaining the "technical manual" for its tools.

**Location**: `langswarm/core/templates/fragments/`

## The Clarification Tool

Agents equipped with tools automatically get access to the `clarify` tool. This tool sends a structured signal that the workflow engine can intercept and route.

### Structure

```json
{
  "tool": "clarify",
  "args": {
    "prompt": "Which specific configuration file do you want me to read?",
    "scope": "local",
    "context": "Found 3 files: dev.yaml, prod.yaml, test.yaml"
  }
}
```

### Scopes

The `scope` argument determines who the question is for:

| Scope | Description | Use Case |
|-------|-------------|----------|
| `local` | Immediate context (default) | Simple ambiguity that might be resolved by checking history or re-reading instructions. |
| `parent_workflow` | The calling agent/workflow | When a sub-agent needs input from the agent that spawned it. |
| `root_user` | The human operator | Critical safety confirmations ("Delete all data?") or missing requirements validation. |

## Usage Examples

### 1. Handling Ambiguity (File System)
**User**: "Read users.json"
**Agent**: (Finds `users.json` in both `/data` and `/backup`)
**Action**:
```json
{
  "tool": "clarify",
  "args": {
    "prompt": "I found 'users.json' in two locations. Which one should I read?",
    "scope": "local",
    "context": "Locations: /data/users.json, /backup/users.json"
  }
}
```

### 2. Safety Confirmation (Escalation)
**User**: "Clean up the database"
**Agent**: (Identifies 5000 records to delete)
**Action**:
```json
{
  "tool": "clarify",
  "args": {
    "prompt": "This will permanently delete 5000 archived records. Please confirm to proceed.",
    "scope": "root_user",
    "context": "Operation: DELETE FROM archive_logs WHERE age > 30 days"
  }
}
```

## Integration with Observability

The "Smart Append" logic ensures that the **final, combined prompt** (User Prompt + Modular Fragments) is what gets logged to your observability platform (like **Langfuse**). This provides full transparency into exactly what instructions the model is following.
