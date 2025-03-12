from types import SimpleNamespace

components = SimpleNamespace(
    instructions = """Usage Instructions:
    
- Actions and Parameters:
    - `create_task`: Create a new task.
      - Parameters:
        - `description` (str): The text describing what needs to be done.
        - `priority` (int): The priority of the task (lower numbers indicate higher priority).
        - `notes` (str | optional): A new note if you want to add something.
        
    - `update_task`: Update the status or the description of the task.
      - Parameters:
        - `task_id` (str): The identifier of the task to update.
        - `description` (str | optional): A new description if you want to change it.
        - `completed` (bool | optional): Set to true or false to mark a task as finished or not.
        - `priority` (int | optional): Update the task's priority.
        - `notes` (str | optional): A new note if you want to change it.

    - `delete_task`: Delete a task.
      - Parameters:
        - `task_id` (str): The identifier of the task to delete.

    - `list_tasks`: List all tasks.
      - No parameters required
      
    - help: Get help on how to use the tool.""",
    
    examples="""Example:
- To create a new task if the tool name is `task_list`:

START>>>
{
  "calls": [
    {
      "type": "tool", 
      "method": "execute",
      "instance_name": "task_list",
      "action": "create_task",
      "parameters": {"description": "Add docstring to function xyz", "priority": 1}
    }
  ]
}
<<<END
"""
)

ToolSettings = SimpleNamespace(
    instructions=f"{components.instructions}\n\n{components.examples}"
)
