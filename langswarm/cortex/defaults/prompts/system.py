PluginInstructions = """-- Plugins (Advanced Capabilities) --
Plugins provide advanced frameworks, domain logic, or special reasoning.

Request information about a specific plugin, or search for available plugins:
START>>>
{
  "calls": [
    {
      "type": "plugins", # Both plugin and plugins works
      "method": "request",
      "instance_name": "<exact_plugin_name> or <search query>", # E.g “my_plugin_name“ or “Find a plugin for structured reasoning“
      "action": "",
      "parameters": {}
    }
  ]
}
<<<END

Once the correct plugin is identified, execute it using:
START>>>
{
  "calls": [
    {
      "type": "plugin",
      "method": "execute",
      "instance_name": "<plugin_name>",
      "action": "<action_name>",
      "parameters": {params_dictionary}
    }
  ]
}
<<<END
"""
