# mcp/tools/tasklist/main.py

import os
import json
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.tools.base import BaseTool
from langswarm.tools.mcp.protocol_interface import MCPProtocolMixin

# === Schemas ===
class CreateTaskInput(BaseModel):
    description: str
    priority: int = 1
    notes: str = ""

class CreateTaskOutput(BaseModel):
    task_id: str
    description: str
    completed: bool
    priority: int
    notes: str
    message: str

class UpdateTaskInput(BaseModel):
    task_id: str
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = None
    notes: Optional[str] = None

class UpdateTaskOutput(BaseModel):
    task_id: str
    description: str
    completed: bool
    priority: int
    notes: str
    message: str

class DeleteTaskInput(BaseModel):
    task_id: str

class DeleteTaskOutput(BaseModel):
    task_id: str
    message: str
    success: bool

class ListTasksOutput(BaseModel):
    tasks: List[Dict[str, Any]]
    count: int
    message: str

# === Smart Task Storage ===
class TaskStorage:
    def __init__(self, use_memory_adapter: bool = None, memory_adapter=None):
        """
        Initialize task storage with smart persistence options
        
        Args:
            use_memory_adapter: If True, use LangSwarm memory adapter. If None, auto-detect.
            memory_adapter: Optional memory adapter instance to use
        """
        self.tasks = {}
        self.next_id = 1
        self.memory_adapter = memory_adapter
        
        # Auto-detect memory adapter if not specified
        if use_memory_adapter is None:
            use_memory_adapter = self._should_use_memory_adapter()
        
        self.use_memory_adapter = use_memory_adapter
        
        if self.use_memory_adapter and not self.memory_adapter:
            self.memory_adapter = self._create_default_adapter()
        
        # Load existing tasks
        if self.use_memory_adapter and self.memory_adapter:
            self.load_from_memory()
        else:
            self.load_from_file()
    
    def _should_use_memory_adapter(self) -> bool:
        """Auto-detect if we should use memory adapter based on environment"""
        # Check for common memory environment variables
        memory_indicators = [
            os.getenv("GOOGLE_CLOUD_PROJECT"),  # BigQuery
            os.getenv("REDIS_URL"),             # Redis
            os.getenv("CHROMADB_HOST"),         # ChromaDB
            os.getenv("LANGSWARM_MEMORY", "").lower() in ["true", "production"]
        ]
        return any(memory_indicators)
    
    def _create_default_adapter(self):
        """
        Create default memory adapter.
        
        NOTE: Legacy adapter support has been removed in V2.
        Task persistence currently defaults to file storage.
        Future versions will integrate with langswarm-memory V2.
        """
        return None
    
    def load_from_memory(self):
        """Load tasks from memory adapter"""
        try:
            if not self.memory_adapter:
                return
            
            # Query all tasklist documents
            results = self.memory_adapter.query("tasklist", filters={"type": "task"}, top_k=1000)
            
            for result in results:
                metadata = result.get("metadata", {})
                task_data = json.loads(result.get("text", "{}"))
                
                if "task_id" in task_data:
                    self.tasks[task_data["task_id"]] = task_data
                    
                    # Update next_id to be higher than any existing task
                    task_num = int(task_data["task_id"].split("-")[1])
                    self.next_id = max(self.next_id, task_num + 1)
            
            print(f"✅ Loaded {len(self.tasks)} tasks from memory adapter")
            
        except Exception as e:
            print(f"Warning: Could not load tasks from memory: {e}")
    
    def save_to_memory(self, task_data: Dict[str, Any]):
        """Save a single task to memory adapter"""
        try:
            if not self.memory_adapter:
                return
            
            document = {
                "key": f"task_{task_data['task_id']}",
                "text": json.dumps(task_data),
                "metadata": {
                    "type": "task",
                    "task_id": task_data["task_id"],
                    "completed": task_data.get("completed", False),
                    "priority": task_data.get("priority", 1),
                    "created_at": task_data.get("created_at", ""),
                    "updated_at": task_data.get("updated_at", "")
                }
            }
            
            self.memory_adapter.add_documents([document])
            
        except Exception as e:
            print(f"Warning: Could not save task to memory: {e}")
    
    def delete_from_memory(self, task_id: str):
        """Delete a task from memory adapter"""
        try:
            if not self.memory_adapter:
                return
            
            self.memory_adapter.delete([f"task_{task_id}"])
            
        except Exception as e:
            print(f"Warning: Could not delete task from memory: {e}")
    
    def load_from_file(self):
        """Load tasks from a local JSON file if it exists (fallback)"""
        try:
            if os.path.exists("tasklist_data.json"):
                with open("tasklist_data.json", "r") as f:
                    data = json.load(f)
                    self.tasks = data.get("tasks", {})
                    self.next_id = data.get("next_id", 1)
                print(f"✅ Loaded {len(self.tasks)} tasks from file storage")
        except Exception as e:
            print(f"Warning: Could not load tasks from file: {e}")
    
    def save_to_file(self):
        """Save tasks to a local JSON file (fallback)"""
        try:
            data = {
                "tasks": self.tasks,
                "next_id": self.next_id
            }
            with open("tasklist_data.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save tasks to file: {e}")
    
    def create_task(self, description: str, priority: int = 1, notes: str = "") -> Dict[str, Any]:
        """Create a new task"""
        from datetime import datetime
        
        task_id = f"task-{self.next_id}"
        self.next_id += 1
        
        task_data = {
            "task_id": task_id,
            "description": description,
            "completed": False,
            "priority": priority,
            "notes": notes,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.tasks[task_id] = task_data
        
        # Save to appropriate storage
        if self.use_memory_adapter and self.memory_adapter:
            self.save_to_memory(task_data)
        else:
            self.save_to_file()
            
        return task_data
    
    def update_task(self, task_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update an existing task"""
        from datetime import datetime
        
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        for key, value in updates.items():
            if key in ["description", "completed", "priority", "notes"] and value is not None:
                task[key] = value
        
        # Update timestamp
        task["updated_at"] = datetime.utcnow().isoformat()
        
        # Save to appropriate storage
        if self.use_memory_adapter and self.memory_adapter:
            self.save_to_memory(task)
        else:
            self.save_to_file()
            
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            
            # Delete from appropriate storage
            if self.use_memory_adapter and self.memory_adapter:
                self.delete_from_memory(task_id)
            else:
                self.save_to_file()
                
            return True
        return False
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all tasks, sorted by priority then by task_id"""
        tasks_list = list(self.tasks.values())
        return sorted(tasks_list, key=lambda x: (x["priority"], x["task_id"]))
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task"""
        return self.tasks.get(task_id)

# Global task storage instance with smart persistence
task_storage = TaskStorage()

# === Handlers ===
def create_task(description: str, priority: int = 1, notes: str = ""):
    """Create a new task"""
    task_data = task_storage.create_task(description, priority, notes)
    return {
        **task_data,
        "message": f"Task '{task_data['task_id']}' created successfully"
    }

def update_task(task_id: str, description: str = None, completed: bool = None, 
                priority: int = None, notes: str = None):
    """Update an existing task"""
    updates = {}
    if description is not None:
        updates["description"] = description
    if completed is not None:
        updates["completed"] = completed
    if priority is not None:
        updates["priority"] = priority
    if notes is not None:
        updates["notes"] = notes
    
    updated_task = task_storage.update_task(task_id, **updates)
    if updated_task is None:
        return {
            "task_id": task_id,
            "message": f"Task '{task_id}' not found",
            "success": False
        }
    
    return {
        **updated_task,
        "message": f"Task '{task_id}' updated successfully"
    }

def delete_task(task_id: str):
    """Delete a task"""
    success = task_storage.delete_task(task_id)
    return {
        "task_id": task_id,
        "message": f"Task '{task_id}' {'deleted successfully' if success else 'not found'}",
        "success": success
    }

def list_tasks():
    """List all tasks"""
    tasks = task_storage.list_tasks()
    return {
        "tasks": tasks,
        "count": len(tasks),
        "message": f"Found {len(tasks)} task(s)"
    }

def get_task(task_id: str):
    """Get a specific task"""
    task = task_storage.get_task(task_id)
    if task is None:
        return {
            "task_id": task_id,
            "message": f"Task '{task_id}' not found",
            "success": False
        }
    
    return {
        **task,
        "message": f"Task '{task_id}' retrieved successfully",
        "success": True
    }

# === Build MCP Server ===
server = BaseMCPToolServer(
    name="tasklist",
    description="Task management MCP tool for creating, updating, listing, and deleting tasks with local persistence.",
    local_mode=True  # 🔧 Enable local mode!
)

server.add_task(
    name="create_task",
    description="Create a new task with description, priority, and optional notes.",
    input_model=CreateTaskInput,
    output_model=CreateTaskOutput,
    handler=create_task
)

server.add_task(
    name="update_task", 
    description="Update an existing task's description, completion status, priority, or notes.",
    input_model=UpdateTaskInput,
    output_model=UpdateTaskOutput,
    handler=update_task
)

server.add_task(
    name="delete_task",
    description="Delete a task by its task_id.",
    input_model=DeleteTaskInput,
    output_model=DeleteTaskOutput,
    handler=delete_task
)

server.add_task(
    name="list_tasks",
    description="List all tasks sorted by priority.",
    input_model=None,  # No input required
    output_model=ListTasksOutput,
    handler=list_tasks
)

server.add_task(
    name="get_task",
    description="Get details of a specific task by task_id.",
    input_model=DeleteTaskInput,  # Same schema as delete (just task_id)
    output_model=dict,  # Dynamic output
    handler=get_task
)

# Build app (None if local_mode=True)
app = server.build_app()

# === LangChain-Compatible Tool Class ===
class TasklistMCPTool(MCPProtocolMixin, BaseTool):
    """
    Tasklist MCP tool for task management operations.
    
    Supports both local mode (direct task operations) and remote mode (via MCP).
    Provides smart persistent task storage using LangSwarm memory adapters or JSON file backup.
    
    Storage Options:
    - Auto-detect: Uses LangSwarm memory adapters if environment is configured
    - Memory adapter: BigQuery, Redis, SQLite, ChromaDB based on your memory config
    - File backup: JSON file storage as fallback
    """
    _bypass_pydantic = True  # Bypass Pydantic validation
    
    def __init__(self, identifier: str, name: str = None, local_mode: bool = True, mcp_url: str = None, 
                 use_memory_adapter: bool = None, memory_adapter=None, **kwargs):
        # Set defaults for tasklist MCP tool
        description = kwargs.pop('description', "Task management tool with smart persistence using LangSwarm memory adapters or file storage")
        instruction = kwargs.pop('instruction', "Use this tool to manage tasks with create_task, update_task, delete_task, list_tasks, and get_task operations")
        brief = kwargs.pop('brief', "Smart Tasklist MCP tool")
        
        # Add MCP server reference
        
        # Set MCP tool attributes to bypass Pydantic validation issues
        object.__setattr__(self, '_is_mcp_tool', True)
        object.__setattr__(self, 'local_mode', local_mode)
        object.__setattr__(self, 'use_memory_adapter', use_memory_adapter)
        object.__setattr__(self, 'memory_adapter', memory_adapter)
        
        # Initialize with BaseTool (handles all MCP setup automatically)
        super().__init__(
            name=name or "TasklistMCPTool",
            description=description,
            tool_id=identifier,
            **kwargs
        )
    
    # V2 Direct Method Calls - Expose operations as class methods
    def create_task(self, description: str, priority: int = 1, notes: str = "", **kwargs):
        """Create a new task"""
        return create_task(description=description, priority=priority, notes=notes)
    
    def update_task(self, task_id: str, description: str = None, completed: bool = None, 
                   priority: int = None, notes: str = None, **kwargs):
        """Update an existing task"""
        return update_task(task_id=task_id, description=description, completed=completed,
                          priority=priority, notes=notes)
    
    def delete_task(self, task_id: str, **kwargs):
        """Delete a task"""
        return delete_task(task_id=task_id)
    
    def list_tasks(self, **kwargs):
        """List all tasks"""
        return list_tasks()
    
    def run(self, input_data=None):
        """Execute tasklist MCP methods locally"""
        # Define method handlers for this tool
        method_handlers = {
            "create_task": create_task,
            "update_task": update_task,
            "delete_task": delete_task,
            "list_tasks": list_tasks,
            "get_task": get_task,
        }
        
        # Use BaseTool's common MCP input handler
        try:
            return self._handle_mcp_structured_input(input_data, method_handlers)
        except Exception as e:
            return f"Error: {str(e)}. Available methods: {list(method_handlers.keys())}"

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        print(f"Task storage initialized with {len(task_storage.tasks)} existing tasks")
        # In local mode, server is ready to use - no uvicorn needed
    else:
        # Only run uvicorn server if not in local mode
        uvicorn.run("mcp.tools.tasklist.main:app", host="0.0.0.0", port=4021, reload=True)