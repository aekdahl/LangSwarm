# 🐝 LangSwarm

**Multi-Agent AI Orchestration Framework**

Build intelligent systems where multiple AI agents collaborate to solve complex tasks. LangSwarm makes it easy to create, orchestrate, and scale AI agent workflows with support for all major LLM providers and a rich ecosystem of tools.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 What is LangSwarm?

LangSwarm is a framework for **multi-agent AI orchestration**. Unlike simple chatbot libraries, LangSwarm enables you to:

- **Orchestrate multiple specialized agents** working together on complex tasks
- **Build workflows** where agents collaborate, hand off work, and combine their outputs
- **Integrate tools** through the Model Context Protocol (MCP) for real-world capabilities
- **Support any LLM provider** (OpenAI, Anthropic, Google, Mistral, local models, and more)
- **Scale from prototypes to production** with enterprise-grade memory, observability, and deployment options

### Why Multi-Agent?

Single AI agents hit limits quickly. Multi-agent systems unlock:

- **Specialization**: Each agent excels at specific tasks (research, writing, analysis, coding)
- **Collaboration**: Agents work together, combining strengths and compensating for weaknesses
- **Scalability**: Distribute workload across multiple agents and providers
- **Reliability**: Redundancy and validation through multiple perspectives
- **Modularity**: Build, test, and deploy agents independently

---

## ⚡ Quick Start

### Installation

```bash
pip install langswarm openai
export OPENAI_API_KEY="your-api-key-here"
```

### Simple Agent (30 seconds)

```python
import asyncio
from langswarm import create_agent

async def main():
    # Create an agent
    agent = create_agent(model="gpt-3.5-turbo")
    
    # Chat with it
    response = await agent.chat("What's the capital of France?")
    print(response)

asyncio.run(main())
```

### Multi-Agent Orchestration (Real Power)

```python
from langswarm.core.agents import create_openai_agent, register_agent
from langswarm.core.workflows import create_simple_workflow, get_workflow_engine

# Create specialized agents
researcher = create_openai_agent(
    name="researcher",
    system_prompt="You are a research specialist. Gather comprehensive information."
)

writer = create_openai_agent(
    name="writer", 
    system_prompt="You are a writing specialist. Create clear, engaging content."
)

# Register for orchestration
register_agent(researcher)
register_agent(writer)

# Create workflow: researcher → writer
workflow = create_simple_workflow(
    workflow_id="content_creation",
    name="Research and Write",
    agent_chain=["researcher", "writer"]
)

# Execute orchestrated workflow
engine = get_workflow_engine()
result = await engine.execute_workflow(
    workflow=workflow,
    input_data={"input": "Write an article about AI agents"}
)

print(result.output)  # Final result from both agents working together
```

---

## 🧠 Core Concepts

### 1. **Agents**

Agents are AI-powered entities with specific roles and capabilities. LangSwarm supports:

- **Multiple providers**: OpenAI, Anthropic (Claude), Google (Gemini), Mistral, Cohere, local models
- **Flexible configuration**: System prompts, temperature, tools, memory
- **Built-in capabilities**: Streaming, structured outputs, cost tracking

```python
# Simple agent creation
agent = create_agent(model="gpt-4", memory=True)

# Advanced agent with tools
agent = create_openai_agent(
    name="assistant",
    model="gpt-4",
    system_prompt="You are a helpful assistant",
    tools=["filesystem", "web_search"]
)
```

### 2. **Workflows**

Workflows define how agents collaborate:

- **Sequential**: Agent A → Agent B → Agent C
- **Parallel**: Multiple agents work simultaneously
- **Conditional**: Route based on results or criteria
- **Nested**: Complex multi-stage pipelines

```python
# Simple sequential workflow
workflow = create_simple_workflow("task", "My Task", ["agent1", "agent2"])

# Execute
engine = get_workflow_engine()
result = await engine.execute_workflow(workflow, {"input": "task data"})
```

### 4. **Memory**

LangSwarm's conversational memory system is powered by **[AgentMem](./agentmem)**, a standalone package that provides enterprise-grade memory management for AI agents.

**Key Features:**
- **Session Management**: Organize conversations with persistent sessions
- **Multiple Backends**: SQLite, Redis, In-Memory, and vector stores
- **Auto-Summarization**: Automatic conversation compression when limits reached
- **Token Management**: Keep context within model limits
- **LLM Integration**: Native OpenAI and Anthropic format support

```python
from langswarm.core.memory import create_memory_manager, Message, MessageRole

# Create memory manager
manager = create_memory_manager("sqlite", db_path="conversations.db")
await manager.backend.connect()

# Create a session
session = await manager.create_session(user_id="user123")

# Add messages
await session.add_message(Message(role=MessageRole.USER, content="Hello"))
```

**AgentMem as Standalone Package:**

AgentMem can also be used independently in other projects:

```bash
pip install agentmem
```

See the [AgentMem documentation](./agentmem/README.md) for more details on standalone usage.

---

## 🛠️ Tools (MCP)

LangSwarm implements the Model Context Protocol (MCP) for tool integration:

**Built-in Tools:**
- `filesystem` - File operations (read, write, list)
- `web_search` - Web search capabilities
- `github` - GitHub repository operations
- `sql_database` - SQL database access
- `bigquery_vector_search` - Semantic search in BigQuery
- `codebase_indexer` - Code analysis and understanding
- `workflow_executor` - Dynamic workflow execution
- `tasklist` - Task management
- `message_queue` - Pub/sub message handling

```python
# Agent with tools
agent = create_agent(
    model="gpt-4",
    tools=["filesystem", "web_search"]
)

# Tools are automatically discovered and injected
response = await agent.chat("Find the latest Python news and save it to a file")
```

### 4. **Memory**

Conversation history and context management with multiple backends:

- **SQLite**: Zero-config, local development
- **Redis**: Fast, distributed caching
- **ChromaDB**: Vector embeddings and semantic search
- **BigQuery**: Analytics-ready, enterprise scale
- **Elasticsearch**: Full-text search and analytics
- **Qdrant**: High-performance vector search
- **Pinecone**: Managed vector database

```python
# Simple memory
agent = create_agent(model="gpt-3.5-turbo", memory=True)

# Advanced memory configuration
config = {
    "memory": {
        "backend": "chromadb",
        "settings": {
            "persist_directory": "./data/memory",
            "embedding_model": "text-embedding-3-small"
        }
    }
}
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LangSwarm Framework                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Agents     │  │  Workflows   │  │    Tools     │ │
│  │              │  │              │  │              │ │
│  │ • OpenAI     │  │ • Sequential │  │ • MCP Local  │ │
│  │ • Anthropic  │  │ • Parallel   │  │ • MCP Remote │ │
│  │ • Google     │  │ • Conditional│  │ • Built-in   │ │
│  │ • Mistral    │  │ • Nested     │  │ • Custom     │ │
│  │ • Local      │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────────────────────────────────────────┐   │
│  │           Infrastructure Layer                  │   │
│  │                                                 │   │
│  │  Memory    Session      Observability   Config │   │
│  │  • SQLite  • Storage    • OpenTelemetry • YAML │   │
│  │  • Redis   • Providers  • LangSmith     • JSON │   │
│  │  • ChromaDB• Lifecycle  • Tracing       • Code │   │
│  │  • BigQuery                                     │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Use Cases

### Content Creation Pipeline

```python
# Specialized agents
researcher = create_openai_agent(name="researcher", system_prompt="Research topics")
writer = create_openai_agent(name="writer", system_prompt="Write engaging content")
editor = create_openai_agent(name="editor", system_prompt="Edit and polish")

# Register all
for agent in [researcher, writer, editor]:
    register_agent(agent)

# Workflow: research → write → edit
workflow = create_simple_workflow("content", "Content Pipeline", 
                                 ["researcher", "writer", "editor"])

# Execute
result = await get_workflow_engine().execute_workflow(
    workflow, {"input": "AI in Healthcare"}
)
```

### Code Analysis & Documentation

```python
# Agent with code analysis tools
coder = create_agent(
    model="gpt-4",
    tools=["codebase_indexer", "filesystem", "github"]
)

# Analyze and document
result = await coder.chat(
    "Analyze the repository, find all API endpoints, and create documentation"
)
```

### Customer Support System

```python
# Multiple agents for different tasks
classifier = create_agent(system_prompt="Classify customer inquiries")
support = create_agent(system_prompt="Provide support answers", tools=["bigquery_vector_search"])
escalation = create_agent(system_prompt="Handle escalations")

# Conditional workflow based on classification
# (See docs for advanced workflow patterns)
```

---

## 🔧 Configuration

### Code Configuration

```python
from langswarm import create_agent

agent = create_agent(
    model="gpt-4",
    system_prompt="You are a helpful assistant",
    memory=True,
    tools=["filesystem", "web_search"],
    temperature=0.7,
    stream=False,
    track_costs=True
)
```

### YAML Configuration

```yaml
# langswarm.yaml
version: "2.0"
project_name: "my-agents"

agents:
  - id: assistant
    model: gpt-4
    provider: openai
    system_prompt: "You are a helpful assistant"
    tools: ["filesystem", "web_search"]
    
  - id: analyst
    model: claude-3-sonnet-20240229
    provider: anthropic
    system_prompt: "You are a data analyst"
    memory_enabled: true

memory:
  backend: chromadb
  settings:
    persist_directory: "./data/memory"

workflows:
  - id: research_task
    workflow: "assistant -> analyst -> user"
```

Load and use:

```python
from langswarm.core.config import load_config

config = load_config("langswarm.yaml")
agent = config.get_agent("assistant")
response = await agent.chat("Hello!")
```

---

## 🚀 Advanced Features

### Streaming Responses

```python
agent = create_agent(model="gpt-4")

async for chunk in agent.chat_stream("Tell me a story"):
    print(chunk, end="", flush=True)
```

### Cost Tracking

```python
agent = create_agent(model="gpt-4", track_costs=True)

await agent.chat("Hello!")

stats = agent.get_usage_stats()
print(f"Tokens used: {stats['total_tokens']}")
print(f"Estimated cost: ${stats['estimated_cost']}")
```

### Structured Outputs

```python
from pydantic import BaseModel

class UserInfo(BaseModel):
    name: str
    age: int
    email: str

agent = create_agent(model="gpt-4")
result = await agent.chat(
    "Extract: John Doe, 30 years old, john@example.com",
    response_format=UserInfo
)
# result is a UserInfo instance
```

### Observability (OpenTelemetry)

```python
from langswarm.observability import enable_instrumentation

# Enable tracing
enable_instrumentation(
    service_name="my-agents",
    exporter="jaeger",  # or "otlp", "prometheus"
    endpoint="http://localhost:14268/api/traces"
)

# All agent/workflow operations now traced
```

---

## 🛠️ MCP Tool Development

Create custom tools using the Model Context Protocol:

```python
from langswarm.tools import UnifiedTool
from langswarm.core.errors import ErrorContext

class MyCustomTool(UnifiedTool):
    """Custom tool for specific operations"""
    
    metadata = {
        "name": "My Custom Tool",
        "description": "Does something specific",
        "version": "1.0.0"
    }
    
    async def execute(self, input_data: dict, context: ErrorContext = None) -> dict:
        """Main execution method"""
        operation = input_data.get("operation")
        
        if operation == "do_something":
            result = await self._do_something(input_data)
            return {"success": True, "result": result}
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}
    
    async def _do_something(self, data: dict):
        # Your tool logic here
        return {"message": "Operation completed"}

# Register and use
from langswarm.tools import ToolRegistry

registry = ToolRegistry()
registry.register_tool(MyCustomTool())

# Now available to agents
agent = create_agent(model="gpt-4", tools=["my_custom_tool"])
```

---

## 📖 Documentation

**📋 Main Resources**
- **[Documentation Index](docs/INDEX.md)** - Complete documentation map
- **[Quick Start Guide](docs/guides/QUICK_START_COMPLETE.md)** - Get up and running in 5 minutes
- **[Multi-Agent Orchestration](docs/MULTI_AGENT_ORCHESTRATION_GUIDE.md)** - Learn workflow patterns
- **[Simple Examples](examples/simple/)** - 10 working examples to learn from

**🆕 V2 - Hierarchical Planning**
- **[Hierarchical Planning](docs/planning/HIERARCHICAL_PLANNING_COMPLETE.md)** - Advanced orchestration system
- **[Retrospective Validation](docs/planning/RETROSPECTIVE_VALIDATION_COMPLETE.md)** - Async validation & rollback
- **[Planning Examples](examples/planning/)** - 6 comprehensive workflow examples

**📦 V1 - Legacy Support**
- **[V1 Quick Start](docs/v1/README_V1_USERS.md)** - Fix V1 bugs (LangChain + UTF-8)
- **[V1 Migration](docs/v1/V1_MIGRATION_GUIDE.md)** - Upgrade to fixed V1
- **[V1 Monkey Patch](docs/v1/langswarm_v1_monkey_patch.py)** - Standalone bug fix

**🔧 Advanced Topics**
- **[Tool Development](docs/tools/mcp/MCP_TOOL_DEVELOPER_GUIDE.md)** - Create custom tools
- **[API Reference](docs/api-reference/)** - Complete API documentation
- **[Migration Guide](docs/migration/)** - Upgrading from older versions
- **[Release Notes](docs/releases/RELEASE_NOTES_v0.0.54.dev46.md)** - Latest release info

---

## 🎯 Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "app.py"]
```

### Environment Variables

```bash
# Required
export OPENAI_API_KEY="sk-..."

# Optional providers
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."

# Memory backends
export REDIS_URL="redis://localhost:6379"
export BIGQUERY_PROJECT="my-project"
export CHROMADB_PATH="./data/chromadb"

# Observability
export LANGSMITH_API_KEY="..."
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
```

### Cloud Deployment

LangSwarm supports deployment to:

- **Google Cloud Platform** (Cloud Run, Cloud Functions, GKE)
- **AWS** (Lambda, ECS, EKS)
- **Azure** (Functions, Container Apps, AKS)

See [deployment documentation](docs/deployment/) for platform-specific guides.

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest tests/

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run examples
cd examples/simple
python 01_basic_chat.py
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/aekdahl/langswarm.git
cd langswarm

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run examples
cd examples/simple && python test_all_examples.py
```

---

## 📊 Supported Providers

| Provider | Status | Models | Notes |
|----------|--------|--------|-------|
| **OpenAI** | ✅ Stable | GPT-4, GPT-3.5, etc. | Full support, function calling |
| **Anthropic** | ✅ Stable | Claude 3.5, Claude 3 | Full support, tool use |
| **Google** | ✅ Stable | Gemini Pro, Gemini Pro Vision | Multimodal support |
| **Mistral** | ✅ Stable | Mixtral, Mistral Large | Function calling |
| **Cohere** | ✅ Stable | Command R+, Command R | RAG capabilities |
| **Hugging Face** | ✅ Beta | Open source models | Local & API |
| **Local** | ✅ Beta | Ollama, LocalAI, etc. | OpenAI-compatible |
| **Custom** | ✅ Beta | Any OpenAI-compatible API | Community template |

---

## 🛠️ Built-in MCP Tools

| Tool | Description | Status |
|------|-------------|--------|
| `filesystem` | File operations (read, write, list) | ✅ Stable |
| `web_search` | Web search capabilities | ✅ Stable |
| `github` | GitHub repository operations | ✅ Stable |
| `sql_database` | SQL database access | ✅ Stable |
| `bigquery_vector_search` | Semantic search in BigQuery | ✅ Stable |
| `codebase_indexer` | Code analysis and search | ✅ Stable |
| `workflow_executor` | Dynamic workflow execution | ✅ Stable |
| `tasklist` | Task management | ✅ Stable |
| `message_queue_publisher` | Publish to message queues | ✅ Stable |
| `message_queue_consumer` | Consume from message queues | ✅ Stable |
| `realtime_voice` | OpenAI Realtime API integration | ✅ Beta |
| `daytona_environment` | Dev environment management | ✅ Beta |
| `gcp_environment` | GCP resource management | ✅ Beta |
| `dynamic_forms` | Dynamic form generation | ✅ Beta |

---

## 📝 License

LangSwarm is MIT licensed. See [LICENSE](LICENSE) for details.

---

## 🙋 Support

- **Issues**: [GitHub Issues](https://github.com/aekdahl/langswarm/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aekdahl/langswarm/discussions)
- **Email**: alexander.ekdahl@gmail.com

---

## 🎉 Examples

See the [`examples/simple/`](examples/simple/) directory for 10 working examples:

1. **Basic Chat** - Simple agent conversation
2. **Memory Chat** - Agent with conversation memory
3. **Two Agents** - Multiple agents working together
4. **Different Models** - Using different LLM providers
5. **With Tools** - Agents using tools (filesystem, web search)
6. **Workflow** - Sequential agent workflows
7. **Web Search** - Agent with web search capabilities
8. **Config From File** - Loading configuration from YAML
9. **Streaming Response** - Real-time streaming responses
10. **Cost Tracking** - Tracking token usage and costs

Each example is **10-25 lines of code** and **fully working**.

---

## 🚀 Quick Links

- **[GitHub Repository](https://github.com/aekdahl/langswarm)**
- **[Documentation](docs/INDEX.md)**
- **[Examples](examples/simple/)**
- **[PyPI Package](https://pypi.org/project/langswarm/)**

---

**Built with ❤️ by the LangSwarm community**
