
import inspect
from typing import Type, Optional, List

from langswarm.memory.adapters.database_adapter import DatabaseAdapter
from ..base import BaseTool
from .config import ToolSettings

class TaskListTool(BaseTool):
    """
    A quick in-memory task list that optionally stores tasks in a vector database.
    """

    def __init__(
        self, 
        identifier, 
        adapter: Optional[Type[DatabaseAdapter]] = None
    ):
        if adapter is not None and not isinstance(adapter, DatabaseAdapter):
            raise TypeError(
                f"Argument 'adapter' must be a subclass of DatabaseAdapter if provided, got {type(adapter).__name__}")

        super().__init__(
            name="TaskListTool",
            description="""Use the TaskListTool to manage tasks. It is useful for breaking down projects into small tasks, tracking progress, or coordinating multiple subtasks in a structured manner.""",
            instruction=ToolSettings.instructions
        )
        
        self.identifier = identifier
        self.brief = (
            f"{identifier} is a task list tool to manage tasks and projects. "
            f"Use the help action to get instructions: execute_tool:{identifier}|help|"+"{}"
        )
        
        self.adapter = adapter  # Optional adapter for storing tasks in a vector database
        self.tasks = {}  # in-memory store, {task_id: {"description": str, "completed": bool, "priority": int, ...}}
        self.next_id = 1
        
        # Load existing tasks from the adapter if available
        if self.adapter:
            self.load_existing_tasks()

    def load_existing_tasks(self):
        """
        Load existing tasks from the adapter using the identifier as the key.
        """
        existing_tasks = self.adapter.query(query=self.identifier)
        for task in existing_tasks:
            self.tasks[task["key"]] = {
                "description": task["text"],
                "completed": task.get("completed", False),
                "priority": task.get("priority", 1), # Default priority if not set
                "notes": task.get("notes", "")
            }
            self.next_id = max(self.next_id, int(task["key"].split("-")[1]) + 1)
    
    def _safe_call(self, func, *args, **kwargs):
        """Safely calls a function and detects incorrect arguments."""
        # ToDo: Now it returns if any argument is invalid, it should only return if
        # required arguments are missing, else we just skip invalid ones.

        func_signature = inspect.signature(func)
        accepted_args = func_signature.parameters.keys()  # Valid argument names

        # Separate valid and invalid arguments
        valid_kwargs = {k: v for k, v in kwargs.items() if k in accepted_args}
        invalid_kwargs = {k: v for k, v in kwargs.items() if k not in accepted_args}

        # If there are invalid arguments, return an error message instead of calling
        if invalid_kwargs:
            return f"Error: Unexpected arguments {list(invalid_kwargs.keys())}. Expected: {list(accepted_args)}"

        # Call the function with only valid arguments
        return func(*args, **valid_kwargs)

    def run(self, payload={}, action="list_tasks"):
        """
        Execute the tool's actions.
        :param payload: str or dict - The input query or tool details.
        :param action: str - The action to perform.
        :return: str or List[str] - The result of the action.
        """
        
        # Map actions to corresponding functions
        action_map = {
            "help": self._help,
            "create_task": self.create_task,
            "update_task": self.update_task,
            "list_tasks": self.list_tasks,
            "delete_task": self.delete_task
        }

        # Execute the corresponding action
        if action in action_map: 
            return self._safe_call(action_map[action], **payload)
        else:
            return (
                f"Unsupported action: {action}. Available actions are:\n\n"
                f"{self.instruction}"
            )

    def create_task(self, description, priority=1):
        """
        Create a new task.
        Returns a dictionary with task_id, description, completed, and priority.
        """
        task_id = f"task-{self.next_id}"
        self.next_id += 1

        task_data = {
            "task_id": task_id,
            "description": description,
            "completed": False,
            "priority": priority,
            "identifier": self.identifier,
            "notes": ""
        }
        self.tasks[task_id] = task_data

        # Store the task in the adapter if provided
        if self.adapter:
            self.adapter.add_documents([{
                "key": task_id,
                "text": description,
                "metadata": {
                    "completed": False,
                    "priority": priority,
                    "identifier": self.identifier,
                    "notes": ""
                }
            }])

        return f"New task created:   {task_data}"

    def update_task(self, task_id, **kwargs):
        """
        Update fields in a task, e.g. 'completed': True or 'description': 'New text'.
        Returns the updated task dict, or None if not found.
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        for key, value in kwargs.items():
            if key in ["description", "completed", "priority", "notes"]:
                task[key] = value

        # Update the task in the adapter if provided
        if self.adapter:
            self.adapter.update({
                "key": task_id,
                "text": task["description"],
                "metadata": {
                    "completed": task["completed"],
                    "priority": task["priority"],
                    "identifier": self.identifier,
                    "notes": ""
                }
            })

        return f"Updated task: {task}"

    def list_tasks(self):
        """
        Return all tasks in memory.
        If using the vector DB, you could query there too for consistency.
        """
        return f"All tasks in list:\n\n {list(self.tasks.values())}"

    def delete_task(self, task_id):
        """
        Delete a task from memory and optionally from the vector DB.
        Returns True if deleted, False if not found.
        """
        # ToDo: Delete task from db as well

        if task_id in self.tasks:
            del self.tasks[task_id]
            return "Task deleted."
        return "The task was not found."
    
    def _help(self):
        return self.instruction
