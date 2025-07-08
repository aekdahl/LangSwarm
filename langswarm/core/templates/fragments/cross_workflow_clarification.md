## Cross-Workflow Clarification

**When you need clarification from the original calling agent (not just the previous step):**

Use this special clarification format to bubble up requests through the workflow hierarchy:

```json
{
  "response": "I need more information from the original user to proceed.",
  "tool": "clarify",
  "args": {
    "prompt": "Your specific clarification question", 
    "scope": "parent_workflow",
    "context": "Additional context about what you found and what's needed"
  }
}
```

**Clarification Scopes:**
- `"local"` (default): Ask previous step or within current workflow
- `"parent_workflow"`: Bubble up to the calling workflow/agent  
- `"root_user"`: Go all the way back to the original user

**Cross-Workflow Clarification Example:**
```json
{
  "response": "I found multiple configuration options but need to know which environment you're working with.",
  "tool": "clarify",
  "args": {
    "prompt": "Which environment are you deploying to? (staging, production, or development)",
    "scope": "parent_workflow", 
    "context": "Found configs for all 3 environments: staging.yml, prod.yml, dev.yml"
  }
}
```

**When clarifications are resolved:**
- The workflow automatically resumes with the additional context
- Previous step outputs are preserved and available
- You can reference both original intent and clarification response 