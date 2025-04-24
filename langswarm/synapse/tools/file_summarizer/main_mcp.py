# tools/file_summarizer_mcp.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Callable, Type
import uvicorn

from tools.file_summarizer import FileSummarizer

# ==== Simulated environment ====
# Replace these with your actual implementations
def get_llm_agent():
    class DummyLLMAgent:
        def run(self, prompt): return f"Summary: {prompt[:50]}..."
    return DummyLLMAgent()

def get_adapter():
    class DummyAdapter:
        def query(self, q): return [{"text": "This is a dummy file content with some details."}]
        def add_metadata(self, file_id, metadata): pass
    return DummyAdapter()
# ==============================

app = FastAPI()
registered_mcp_tools = {}

# ==== Decorator ====
def mcp_tool(name: str, description: str, input_model: Type[BaseModel], output_model: Type[BaseModel]):
    def decorator(func: Callable):
        route_path = f"/{name}"

        # Standard MCP call
        @app.post(route_path, response_model=output_model)
        async def invoke(payload: input_model):
            try:
                result = func(**payload.dict())
                return output_model(**result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Standard MCP schema endpoint
        @app.get(f"{route_path}/schema")
        async def schema():
            return {
                "name": name,
                "description": description,
                "input_schema": input_model.schema(),
                "output_schema": output_model.schema(),
            }

        # Optionally store metadata for discovery
        registered_mcp_tools[name] = {
            "description": description,
            "input_model": input_model,
            "output_model": output_model,
            "entry": func,
        }

        return func
    return decorator

# ==== Schemas ====
class SummarizeInput(BaseModel):
    file_id: str

class SummarizeOutput(BaseModel):
    file_id: str
    summary: str

# ==== MCP Tool Wrapper ====
@mcp_tool(
    name="summarize_file",
    description="Summarizes a file and stores the summary back into the database.",
    input_model=SummarizeInput,
    output_model=SummarizeOutput
)
def summarize_file(file_id: str) -> dict:
    adapter = get_adapter()
    llm_agent = get_llm_agent()
    tool = FileSummarizer(llm_agent)
    return tool.use(adapter, file_id)

# ==== Entry Point ====
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4010)
