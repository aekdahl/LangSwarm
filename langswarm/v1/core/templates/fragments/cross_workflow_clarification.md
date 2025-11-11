## Cross-Workflow Clarification

**IMPORTANT: Always attempt to use available tools first before asking for clarification.**

**Only use clarification when:**
- You have insufficient information AFTER attempting to use tools
- Multiple valid options exist and you need the user to choose
- You encounter an error that requires user guidance to resolve

**When clarification is absolutely necessary, use this format:**

{
  "response": "I attempted to [describe what you tried] but need clarification: [specific question]",
  "tool": "clarify",
  "args": {
    "prompt": "Your specific clarification question", 
    "scope": "parent_workflow",
    "context": "What you attempted and why clarification is needed"
  }
}

**Clarification Scopes:**
- `"local"` (default): Ask previous step or within current workflow
- `"parent_workflow"`: Bubble up to the calling workflow/agent  
- `"root_user"`: Go all the way back to the original user

**Proper Clarification Example (AFTER attempting tools):**
{
  "response": "I searched the available datasets but found three different 'user' tables. Which specific user table should I query: users_prod, users_staging, or users_archive?",
  "tool": "clarify",
  "args": {
    "prompt": "Which user table should I query: users_prod, users_staging, or users_archive?",
    "scope": "parent_workflow", 
    "context": "Found multiple user tables after running list_datasets - need to specify which one to use"
  }
}

**Remember:** 
- Use tools first, clarify second
- Provide specific context about what you tried
- Make clarification questions actionable and specific 