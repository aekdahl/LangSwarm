# langswarm/mcp/server_base.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Callable, Dict, Any, Type
import threading

class BaseMCPToolServer:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def add_task(self, name: str, description: str, input_model: Type[BaseModel],
                 output_model: Type[BaseModel], handler: Callable):
        self._tasks[name] = {
            "description": description,
            "input_model": input_model,
            "output_model": output_model,
            "handler": handler
        }

    def build_app(self) -> FastAPI:
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
