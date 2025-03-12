from types import SimpleNamespace

components = SimpleNamespace(
    instructions = """Usage Instructions:
    
    - query: Execute the consensus workflow with the given query.
     - Parameters:
       - `query` (str): The query.
       
    - help: Get help on how to use the tool.
    """,
    examples="""Example:
- To read a file if the tool name is `consensus_tool`:

START>>>
{
  "calls": [
    {
      "type": "tool", 
      "method": "execute",
      "instance_name": "consensus_tool",
      "action": "query",
      "parameters": {"query": "What is pi?"}
    }
  ]
}
<<<END
"""
)

ToolSettings = SimpleNamespace(
    instructions=f"{components.instructions}\n\n{components.examples}"
)