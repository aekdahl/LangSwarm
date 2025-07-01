# langswarm/mcp/server_base.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Callable, Dict, Any, Type, Optional
import threading

class BaseMCPToolServer:
    def __init__(self, name: str, description: str, local_mode: bool = False):
        self.name = name
        self.description = description
        self.local_mode = local_mode  # 🔧 Add local mode flag
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Register globally for local mode detection
        if local_mode:
            self._register_globally()

    def _register_globally(self):
        """Register this server globally for local mode detection."""
        if not hasattr(BaseMCPToolServer, '_global_registry'):
            BaseMCPToolServer._global_registry = {}
        BaseMCPToolServer._global_registry[self.name] = self

    @classmethod
    def get_local_server(cls, name: str) -> Optional['BaseMCPToolServer']:
        """Get a locally registered server by name."""
        registry = getattr(cls, '_global_registry', {})
        return registry.get(name)

    def add_task(self, name: str, description: str, input_model: Type[BaseModel],
                 output_model: Type[BaseModel], handler: Callable):
        self._tasks[name] = {
            "description": description,
            "input_model": input_model,
            "output_model": output_model,
            "handler": handler
        }

    def get_schema(self) -> Dict[str, Any]:
        """Get the schema for this tool (local mode)."""
        return {
            "tool": self.name,
            "description": self.description,
            "tools": [
                {
                    "name": task_name,
                    "description": meta["description"],
                    "inputSchema": meta["input_model"].schema(),
                    "outputSchema": meta["output_model"].schema()
                }
                for task_name, meta in self._tasks.items()
            ]
        }

    def call_task(self, task_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a task directly (local mode)."""
        if task_name not in self._tasks:
            raise ValueError(f"Task '{task_name}' not found in {self.name}")
        
        meta = self._tasks[task_name]
        handler = meta["handler"]
        input_model = meta["input_model"]
        output_model = meta["output_model"]
        
        with self._lock:
            try:
                # Validate input
                validated_input = input_model(**params)
                
                # Call handler
                result = handler(**validated_input.dict())
                
                # Validate output
                validated_output = output_model(**result)
                return validated_output.dict()
                
            except Exception as e:
                return {"error": str(e)}

    def build_app(self) -> Optional[FastAPI]:
        """Build FastAPI app - skip for local mode."""
        if self.local_mode:
            print(f"🔧 {self.name} running in LOCAL MODE - no HTTP server needed")
            return None
        
        app = FastAPI(title=self.name, description=self.description)

        @app.get("/schema")
        async def schema_root():
            return {
                "tool": self.name,
                "description": self.description,
                "tasks": [
                    {
                        "name": task_name,
                        "description": meta["description"],
                        "path": f"/{task_name}",
                        "schema_path": f"/{task_name}/schema"
                    }
                    for task_name, meta in self._tasks.items()
                ]
            }

        # Dynamic route registration
        for task_name, meta in self._tasks.items():
            input_model = meta["input_model"]
            output_model = meta["output_model"]
            handler = meta["handler"]

            # Create schema endpoint
            def make_schema(meta=meta, task_name=task_name):
                async def schema_endpoint():
                    return {
                        "name": task_name,
                        "description": meta["description"],
                        "input_schema": meta["input_model"].schema(),
                        "output_schema": meta["output_model"].schema()
                    }
                return schema_endpoint

            app.get(f"/{task_name}/schema")(make_schema())

            # Create execution endpoint
            def make_handler(handler=handler, input_model=input_model, output_model=output_model):
                async def endpoint(payload: input_model):
                    with self._lock:
                        try:
                            result = handler(**payload.dict())
                            return output_model(**result)
                        except Exception as e:
                            raise HTTPException(status_code=500, detail=str(e))
                return endpoint

            app.post(f"/{task_name}", response_model=output_model)(make_handler())

        return app
