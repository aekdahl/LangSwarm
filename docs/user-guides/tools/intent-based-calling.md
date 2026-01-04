# 🧠 Intent-Based Calling (Hybrid MCP)

LangSwarm implements a unique **Hybrid MCP Schema** that allows tools to be used in two ways simultaneously:

1.  **Standard MCP**: Direct method calls (compatible with Claude, Cursor, VS Code).
2.  **Intent-Based**: Natural language requests that the tool intelligently resolves (LangSwarm's "Secret Sauce").

## The Hybrid Schema

Every LangSwarm MCP tool automatically supports this unified schema:

```json
{
  "oneOf": [
    {
      "description": "Standard MCP Direct Call",
      "properties": {
        "method": { "type": "string" },
        "params": { "type": "object" }
      },
      "required": ["method", "params"]
    },
    {
      "description": "Intelligent Intent Call (LangSwarm)",
      "properties": {
        "intent": { "type": "string", "description": "What you want to achieve" },
        "context": { "type": "string", "description": "Supporting background info" }
      },
      "required": ["intent"]
    }
  ]
}
```

## Usage Modes

### 1. The "Intelligent" Way (LangSwarm Agents)
Agents can simply express *what* they want, without knowing the tool's internal methods or parameters. The tool itself figures out the best way to fulfill the request.

```json
{
  "intent": "Find trending tech news from the last 24 hours related to AI",
  "context": "Focus on product launches"
}
```

**Why use this?**
*   **Zero-Shot Tool Use**: Agents don't need to learn complex APIs.
*   **Resilience**: If the tool's internal API changes, the agent doesn't break; the tool's intent resolver handles the mapping.
*   **Complex Chains**: One intent might trigger a multi-step workflow inside the tool.

### 2. The "Standard" Way (Claude / External Clients)
Users or strict logic can call specific methods directly, just like a normal function call.

```json
{
  "method": "search_news",
  "params": {
    "query": "AI product launches",
    "time_range": "24h",
    "category": "tech"
  }
}
```

**Why use this?**
*   **Precision**: When you know exactly what you want.
*   **Compatibility**: Works with any standard MCP client (e.g., Cursor, Claude Desktop) that doesn't "speak" LangSwarm conventions.

## Developing Hybrid Tools

To create a tool that supports both, just implement the `StandardMCPToolServer` mixin or use the `GlobalMCPToolRegistry`. The framework handles the routing automatically.

If a tool receives an `intent`, it looks for a registered `_handle_intent_call` handler. If it receives a `method`, it routes to that specific Python method.

## ✍️ Best Practices for Tool Templates

To make the "Intent-Based" mode work reliably, your `template.md` must be remarkably clean.

### 1. The `## Instructions` Section
This is the **only** part the LLM sees. Keep it concise.
*   **DO** describe *what* the tool does and *when* to use it.
*   **DO** list available high-level operations.
*   **DO NOT** dump implementation details or internal method names.
*   **DO NOT** put huge JSON schemas here (the system handles that).

### 2. Example Structure
```markdown
## Instructions

Use this tool to search the company knowledge base. It understands semantic meaning.

**When to use:** Answering questions about policies, products, or procedures.

**Primary Intent:**
"Find information about X", "Search for Y"

**Tips:**
- Be specific with your intent.
- Include context like "for enterprise customers".
```

### 3. Separation of Concerns
Place all developer documentation (protocol specs, setup guides) **outside** the `## Instructions` section so it doesn't pollute the context window.
