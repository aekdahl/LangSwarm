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
    
    @property
    def tasks(self) -> Dict[str, Dict[str, Any]]:
        """Public access to registered tasks"""
        return self._tasks

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
                # Validate input with enhanced error reporting
                try:
                    validated_input = input_model(**params)
                except Exception as validation_error:
                    error_msg = f"🚨 PARAMETER VALIDATION FAILED in {self.name}.{task_name}: {str(validation_error)}"
                    print(error_msg)  # IMMEDIATE CONSOLE ALERT
                    # LOG AS ERROR (use module logger if instance logger not available)
                    import logging
                    logger = getattr(self, 'logger', logging.getLogger(__name__))
                    logger.error(error_msg)
                    
                    # Report to central error monitoring
                    try:
                        from langswarm.core.debug.error_monitor import report_tool_validation_error
                        report_tool_validation_error(self.name, task_name, str(validation_error), params)
                    except ImportError:
                        pass  # Error monitor not available
                    
                    raise validation_error  # Re-raise for normal error handling
                
                # Call handler (handle both sync and async)
                import asyncio
                import inspect
                
                if inspect.iscoroutinefunction(handler):
                    # Handler is async - run in a new thread with its own event loop
                    import threading
                    import concurrent.futures
                    
                    result_container = [None]
                    exception_container = [None]
                    
                    def run_async_handler():
                        try:
                            # Create a new event loop for this thread
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                result_container[0] = new_loop.run_until_complete(
                                    handler(**validated_input.dict())
                                )
                            finally:
                                new_loop.close()
                        except Exception as e:
                            exception_container[0] = e
                    
                    # Run in a separate thread with timeout
                    thread = threading.Thread(target=run_async_handler)
                    thread.start()
                    thread.join(timeout=10)  # 10 second timeout
                    
                    if thread.is_alive():
                        raise TimeoutError("Handler execution timed out after 10 seconds")
                    
                    if exception_container[0]:
                        raise exception_container[0]
                    
                    result = result_container[0]
                else:
                    # Handler is sync
                    result = handler(**validated_input.dict())
                
                # Validate output
                if isinstance(result, output_model):
                    # Result is already the correct output model
                    return result.dict()
                elif isinstance(result, dict):
                    # Result is a dict, validate it
                    validated_output = output_model(**result)
                    return validated_output.dict()
                else:
                    # Unexpected result type
                    raise ValueError(f"Handler returned unexpected type: {type(result)}, expected {output_model} or dict")
                
            except Exception as e:
                # Enhanced error reporting with immediate surfacing
                error_type = type(e).__name__
                error_msg = f"🚨 MCP TOOL EXECUTION FAILED: {self.name}.{task_name} - {error_type}: {str(e)}"
                print(error_msg)  # IMMEDIATE CONSOLE ALERT
                # LOG AS ERROR (use module logger if instance logger not available)
                import logging
                logger = getattr(self, 'logger', logging.getLogger(__name__))
                logger.error(error_msg)
                
                # Return structured error response
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": error_type,
                    "tool": self.name,
                    "task": task_name,
                    "critical": True  # Flag this as a critical error
                }

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
