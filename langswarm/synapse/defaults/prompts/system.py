ToolInstructions = """-- Tools (External Actions) --
Tools can perform external actions: editing files, setting reminders, making an API calls, etc.

Request information about a specific tool, or search for available tools:
START>>>
{
  "calls": [
    {
      "type": "tools", # Both tool and tools works
      "method": "request",
      "instance_name": "<exact_tool_name> or <search query>", # E.g “github_tool“ or “Find a tool for file management“
      "action": "",
      "parameters": {}
    }
  ]
}
<<<END

Once the correct tool is identified, execute it using:
START>>>
{
  "calls": [
    {
      "type": "tools", 
      "method": "execute",
      "instance_name": "<tool_name>",
      "action": "<action_name>",
      "parameters": {params_dictionary}
    }
  ]
}
<<<END
"""
