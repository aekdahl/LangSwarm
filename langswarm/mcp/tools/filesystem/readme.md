# 🗂 MCP Filesystem Tool

This is a standardized MCP (Model-Compatible Protocol) tool that exposes read-only access to the local filesystem. It supports directory listing and file reading, and is designed to be fully autonomous and interoperable with agent frameworks such as **LangSwarm**.

---

## ✅ Features

- `list_directory`: Lists the contents of a local directory
- `read_file`: Reads the content of a text file
- Standard MCP-compliant schema endpoints (`/schema`, `/task/schema`)
- Thread-safe, concurrent-safe access
- Auto-discoverable by LangSwarm via `workflow.yaml`
- Includes a dedicated multi-step `workflow.yaml` for agent interaction

---

## 📁 Folder Structure

```
mcp/tools/filesystem/
├── main.py            # MCP server implementation
├── workflow.yaml      # LangSwarm-compatible tool usage workflow
└── README.md          # You're here
```

---

## 🚀 Running the Tool

```bash
python mcp/tools/filesystem/main.py
```

This will start a FastAPI server on `http://localhost:4020` exposing MCP endpoints:

- `/schema` — Root tool schema
- `/list_directory` — POST endpoint
- `/list_directory/schema` — GET schema for directory listing
- `/read_file` — POST endpoint
- `/read_file/schema` — GET schema for reading files

---

## 🧠 Agent Usage

Agents can use the tool by calling:

```python
from langswarm.runtime.tool_runtime import use_tool

result = use_tool("filesystem", {"user_query": "Show me what's inside the logs folder"})
print(result)
```

The system will:
- Load `workflow.yaml`
- Trigger helper agents to choose the tool task, extract file paths, build inputs
- Call the MCP endpoints via `mcp_call()`
- Return a summarized result to the user

---

## 🧩 Extending the Tool

To add new capabilities:
- Define a new `task` (e.g., `search_file_contents`) in `main.py`
- Add schema and handler via `.add_task()`
- Extend `workflow.yaml` to route and handle new functionality

---

## 🔐 Thread Safety

The server uses a `threading.Lock()` to ensure all reads are atomic and safe for concurrent access.

---

## 🛠 Dependencies

- Python 3.8+
- FastAPI
- Uvicorn
- Pydantic

Install with:
```bash
pip install fastapi uvicorn pydantic
```

---

## 📚 References

- [Anthropic MCP Spec](https://github.com/anthropics/mcp)
- LangSwarm internal: `use_tool()`, `workflow.yaml`, `mcp_call()`

---

## 🧭 Future Roadmap

- ✅ Read-only (done)
- 🔄 CRUD file support (next)
- ☁️ Pluggable backends (local, S3, GCS, etc.)
- 🔐 Optional auth integration

---

Built with ❤️ for agent-first systems.

