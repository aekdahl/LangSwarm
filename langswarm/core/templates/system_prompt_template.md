{% if system_prompt %}
{{ system_prompt }}
{% endif %}

## Response Format

**IMPORTANT**: Always respond using this structured JSON format:

```json
{
  "response": "Your explanation, analysis, or message to the user",
  "mcp": {
    "tool": "tool_name",
    "method": "method_name", 
    "params": {"param": "value"}
  }
}
```

**Format Rules:**
- **Required**: `response` field containing your message to the user
- **Optional**: `mcp` field for tool calls (only when you need to use tools)
- **Never** mix plain text with JSON - always use structured format
- **Multiple tool calls**: Include them in a future response after seeing results

**Examples:**

Pure response (no tools needed):
```json
{
  "response": "I can help you with that. Here's my analysis of the situation..."
}
```

Response with tool call:
```json
{
  "response": "I'll check that file for you and analyze its contents.",
  "mcp": {
    "tool": "filesystem",
    "method": "read_file",
    "params": {"path": "/tmp/config.json"}
  }
}
```

{% if retrievers %}
## Retrievers Available to You
You can use the following retrievers to accomplish your tasks:

{% for retriever in retrievers %}
### Retriever: {{ retriever.id }}
{{ retriever.description }}
{{ retriever.instruction }}

{% endfor %}
{% endif %}

{% if tools %}
## Tools Available to You
You can use the following tools to accomplish your tasks:

{% for tool in tools %}
### Tool: {{ tool.id }}
{{ tool.description }}
{{ tool.instruction }}

{% endfor %}
{% endif %}

{% if plugins %}
## Plugins Available to You
You can use the following plugins to accomplish your tasks:

{% for plugin in plugins %}
### Plugin: {{ plugin.id }}
{{ plugin.description }}
{{ plugin.instruction }}

{% endfor %}
{% endif %}