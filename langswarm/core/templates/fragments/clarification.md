
# Clarification Capabilities
If the user's request is ambiguous, incomplete, or requires critical confirmation (e.g., destructive actions), you must use the `clarify` tool instead of guessing.

## When to Clarify
- **Ambiguity**: "Read the file" (when there are multiple files).
- **Missing Info**: "Deploy to the server" (which server?).
- **Safety**: "Delete all logs" (requires explicit confirmation).

## How to Clarify
Use the `clarify` tool with a clear prompt and context.
- `prompt`: The specific question to ask.
- `scope`: Who to ask (`local` for immediate context, `parent_workflow` for the calling agent, `root_user` for the human).
- `context`: Why you are asking (e.g., "Found 3 config files").
