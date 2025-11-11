# langswarm/mcp/server_base.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Callable, Dict, Any, Type, Optional, List
import threading
import asyncio
import inspect

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
    
    # ===============================
    # STANDARD MCP PROTOCOL METHODS
    # ===============================
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Standard MCP method: List all available tools"""
        tools = []
        for task_name, task_info in self._tasks.items():
            schema = {}
            if task_info.get("input_model"):
                try:
                    schema = task_info["input_model"].model_json_schema()
                except:
                    schema = {"type": "object", "properties": {}}
            
            tools.append({
                "name": task_name,
                "description": task_info.get("description", f"{task_name} operation"),
                "inputSchema": schema
            })
        
        return tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Standard MCP method: Execute a tool"""
        if name not in self._tasks:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Tool '{name}' not found. Available tools: {list(self._tasks.keys())}"}]
            }
        
        try:
            task = self._tasks[name]
            handler = task["handler"]
            
            # Convert arguments to input model if available
            if task.get("input_model"):
                try:
                    input_obj = task["input_model"](**arguments)
                    if inspect.iscoroutinefunction(handler):
                        result = await handler(input_obj)
                    else:
                        result = handler(input_obj)
                except Exception as e:
                    return {
                        "isError": True,
                        "content": [{"type": "text", "text": f"Input validation error: {str(e)}"}]
                    }
            else:
                # Direct call with arguments
                if inspect.iscoroutinefunction(handler):
                    result = await handler(arguments)
                else:
                    result = handler(arguments)
            
            # Format result
            if hasattr(result, 'model_dump'):
                result_data = result.model_dump()
            elif isinstance(result, dict):
                result_data = result
            else:
                result_data = {"result": str(result)}
            
            return {
                "content": [{"type": "text", "text": str(result_data)}]
            }
            
        except Exception as e:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Execution error: {str(e)}"}]
            }

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
        print(f"🔍 MCP Server '{self.name}' call_task: {task_name} with params: {list(params.keys()) if params else 'None'}")
        
        if task_name not in self._tasks:
            print(f"❌ Task '{task_name}' not found in {self.name}. Available: {list(self._tasks.keys())}")
            # Return a simple error that agents can handle
            return {
                "success": False,
                "error": f"Method '{task_name}' is not available",
                "available_methods": list(self._tasks.keys()),
                "tool_name": self.name
            }
        
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
                        from langswarm.v1.core.debug.error_monitor import report_tool_validation_error
                        report_tool_validation_error(self.name, task_name, str(validation_error), params)
                    except ImportError:
                        pass  # Error monitor not available
                    
                    # Enhanced parameter error response with actionable feedback
                    error_response = self._generate_parameter_error_response(
                        task_name, validation_error, params, input_model
                    )
                    return error_response
                
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
    
    def _generate_parameter_error_response(self, task_name, validation_error, params, input_model):
        """
        Generate an enhanced error response with actionable feedback for parameter validation failures.
        This helps agents understand what went wrong and how to fix it.
        """
        import logging
        logger = getattr(self, 'logger', logging.getLogger(__name__))
        
        # Extract field information from the validation error
        error_details = self._parse_validation_error(validation_error)
        
        # Generate helpful suggestions based on the tool's template
        suggestions = self._generate_parameter_suggestions(task_name, error_details, input_model)
        
        # Log the validation error with actionable information
        logger.warning(f"Parameter validation failed for {self.name}.{task_name}: {error_details['summary']}")
        logger.info(f"Providing actionable feedback to agent: {suggestions['guidance']}")
        
        # Return comprehensive error response that agents can act upon
        return {
            "success": False,
            "error": error_details['summary'],
            "error_type": "parameter_validation_error",
            "tool_name": self.name,
            "method": task_name,
            "validation_details": error_details,
            "actionable_feedback": suggestions,
            "retry_enabled": True,  # Indicate that the agent should retry with corrections
            "guidance": suggestions['guidance']
        }
    
    def _parse_validation_error(self, validation_error):
        """Parse Pydantic validation error into structured information"""
        try:
            if hasattr(validation_error, 'errors'):
                # Pydantic v2 style
                errors = validation_error.errors()
            else:
                # Pydantic v1 or other validation errors
                errors = [{"loc": ["unknown"], "msg": str(validation_error), "type": "validation_error"}]
            
            # Extract the most relevant error information
            primary_error = errors[0] if errors else {}
            field_name = primary_error.get('loc', ['unknown'])[0] if primary_error.get('loc') else 'unknown'
            error_message = primary_error.get('msg', str(validation_error))
            error_type = primary_error.get('type', 'validation_error')
            
            return {
                "summary": f"Invalid parameter '{field_name}': {error_message}",
                "field": field_name,
                "message": error_message,
                "type": error_type,
                "all_errors": errors
            }
        except Exception:
            # Fallback for unexpected error formats
            return {
                "summary": f"Parameter validation failed: {str(validation_error)}",
                "field": "unknown",
                "message": str(validation_error),
                "type": "validation_error",
                "all_errors": []
            }
    
    def _generate_parameter_suggestions(self, task_name, error_details, input_model):
        """Generate helpful suggestions for fixing parameter errors"""
        field_name = error_details['field']
        error_type = error_details['type']
        
        # Get field information from the Pydantic model
        model_fields = getattr(input_model, 'model_fields', {}) or getattr(input_model, '__fields__', {})
        
        # Generate specific suggestions based on error type and field
        suggestions = {
            "guidance": f"Parameter validation failed for '{field_name}'. Please check the parameter format and try again.",
            "example": {},
            "required_fields": [],
            "optional_fields": []
        }
        
        # Extract field requirements from the model
        for field, field_info in model_fields.items():
            if hasattr(field_info, 'is_required') and field_info.is_required():
                suggestions["required_fields"].append(field)
            else:
                suggestions["optional_fields"].append(field)
        
        # Provide specific guidance based on common error patterns
        if error_type == 'missing':
            suggestions["guidance"] = f"Required parameter '{field_name}' is missing. Please include this parameter in your request."
            if task_name == 'similarity_search' and field_name == 'query':
                suggestions["example"] = {"query": "your search text here", "limit": 5}
                suggestions["guidance"] += f" Example: {suggestions['example']}"
        elif error_type == 'type_error':
            suggestions["guidance"] = f"Parameter '{field_name}' has the wrong type. {error_details['message']}"
        elif 'value_error' in error_type:
            suggestions["guidance"] = f"Parameter '{field_name}' has an invalid value. {error_details['message']}"
        
        # Add tool-specific guidance
        if hasattr(self, '_get_tool_specific_guidance'):
            tool_guidance = self._get_tool_specific_guidance(task_name, error_details)
            if tool_guidance:
                suggestions["guidance"] = tool_guidance
        
        return suggestions
