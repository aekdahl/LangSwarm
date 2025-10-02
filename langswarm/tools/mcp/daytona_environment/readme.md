# 🚀 Daytona Environment MCP Tool

A comprehensive development environment management tool built on the MCP (Model-Compatible Protocol) framework with Daytona integration for LangSwarm workflows.

## Overview

The Daytona Environment MCP Tool provides secure and elastic infrastructure for running AI-generated code using [Daytona](https://github.com/daytonaio/daytona) sandboxes. It enables agents to create isolated development environments, execute code safely, manage files, and perform git operations with lightning-fast performance and enterprise-grade security.

---

## ✨ Features

- 🏎️ **Lightning-Fast**: Sub-90ms sandbox creation from code to execution
- 🔒 **Secure & Isolated**: Execute AI-generated code with zero risk to infrastructure  
- 🔄 **Full Lifecycle Management**: Create, manage, execute, and destroy environments
- 📁 **Complete File Operations**: Upload, download, read, write, list, delete files
- 🔧 **Git Integration**: Clone, pull, push, commit, status, checkout operations
- 🐳 **OCI/Docker Compatible**: Use any OCI/Docker image for custom environments
- ♾️ **Unlimited Persistence**: Environments can live forever or be temporary
- 🤖 **Intent-Based Interface**: Natural language environment management
- 🛡️ **Error Handling**: Comprehensive validation and error recovery
- ⚡ **Local Mode Support**: Zero-latency local execution option

---

## 🛠️ Installation & Setup

### Prerequisites

1. **Daytona Account**: Create an account at [https://app.daytona.io](https://app.daytona.io)
2. **API Key**: Generate a Daytona API key from your dashboard
3. **Python Dependencies**: Ensure you have the required packages

### Install Dependencies

```bash
# Install Daytona SDK
pip install daytona

# Or install with specific version requirement
pip install "daytona>=0.10.5"
```

### Environment Variables

```bash
# Required: Your Daytona API key
export DAYTONA_API_KEY="your_api_key_here"

# Optional: Daytona API URL 
# - For cloud service (default): https://app.daytona.io
# - For self-hosted instance: https://your-daytona-instance.com
export DAYTONA_API_URL="https://app.daytona.io"
```

### Deployment Architecture

**Recommended (Current Implementation):**
```
LangSwarm Agent → MCP Tool (local) → Daytona Cloud API → Managed Sandboxes
```
- ✅ Simple setup and configuration
- ✅ Scalable infrastructure managed by Daytona
- ✅ No local resource overhead for environments
- ✅ Enterprise-grade security and performance

**Alternative (Self-Hosted):**
```
LangSwarm Agent → MCP Tool (local) → Self-Hosted Daytona → Local/Remote Sandboxes
```
- ⚠️ Requires managing your own Daytona infrastructure
- ⚠️ More complex setup and maintenance
- ✅ Full control over infrastructure and data
- ✅ Can run on private networks/air-gapped systems

---

## 📁 Directory Structure

```
mcp/tools/daytona_environment/
├── main.py               # Core MCP server implementation with Daytona integration
├── agents.yaml           # Specialized agents for environment operations
├── workflows.yaml        # Workflow definitions for different use cases
├── template.md           # LLM-consumable tool instructions
└── README.md            # Human-readable documentation (this file)
```

---

## 🚀 Quick Start

### Using with LangSwarm

**Basic Configuration**:
```yaml
tools:
  - id: daytona_env
    type: daytona_environment
    description: "Secure development environments with Daytona"
    local_mode: true
    pattern: "intent"
    main_workflow: "use_daytona_environment_tool"
    permission: anonymous
```

**Advanced Configuration**:
```yaml
tools:
  - id: daytona_dev
    type: daytona_environment
    description: "Full-featured development environment management"
    local_mode: true
    pattern: "intent"
    main_workflow: "create_development_environment"
    permission: authenticated
    config:
      api_key: "${DAYTONA_API_KEY}"
      api_url: "${DAYTONA_API_URL}"
      default_language: "python"
      default_persistent: false
```

---

## 📖 Usage Examples

### Natural Language (Intent-Based)

```
"Create a Python development environment for my Flask project"
"Run this code in a secure sandbox: print('Hello, Daytona!')"
"Clone my repository into a new environment"
"List all my current development environments"
"Upload my project files to the sandbox"
"Execute npm test in my Node.js environment"
"Delete the old testing environment"
```

### Direct API Calls

```python
# Create a new sandbox
tool.run({
    "method": "create_sandbox",
    "params": {
        "language": "python",
        "name": "ml-project",
        "git_repo": "https://github.com/user/ml-project.git",
        "persistent": True,
        "environment_vars": {
            "PYTHONPATH": "/workspace",
            "ENV": "development"
        }
    }
})

# Execute code in the sandbox
tool.run({
    "method": "execute_code", 
    "params": {
        "sandbox_id": "sandbox-abc123",
        "code": "import pandas as pd\nprint(pd.__version__)",
        "language": "python"
    }
})

# Perform file operations
tool.run({
    "method": "file_operation",
    "params": {
        "sandbox_id": "sandbox-abc123",
        "operation": "write",
        "file_path": "/app/config.py", 
        "content": "DATABASE_URL = 'sqlite:///app.db'"
    }
})
```

---

## 🔧 Available Operations

### Sandbox Management
- **create_sandbox**: Spin up new development environments
- **list_sandboxes**: View all your environments
- **get_sandbox_info**: Get detailed environment information
- **delete_sandbox**: Clean up environments

### Code Execution
- **execute_code**: Run Python, JavaScript, or other code safely
- **execute_shell**: Execute shell commands and CLI operations

### File Management  
- **file_operation**: Complete file management (read, write, upload, download, list, delete)

### Version Control
- **git_operation**: Full git workflow support (clone, pull, push, commit, status, checkout)

---

## 🎯 Use Cases

### 🧑‍💻 Development Workflows
- **Rapid Prototyping**: Spin up environments for quick experimentation
- **Code Testing**: Test code changes in isolated environments
- **Multi-Project Development**: Manage multiple project environments
- **Collaborative Development**: Share consistent development environments

### 🎓 Educational Use Cases
- **Coding Tutorials**: Provide students with clean, consistent environments
- **Interactive Learning**: Execute code examples safely
- **Assignment Grading**: Test student code in isolated sandboxes

### 🤖 AI & Automation
- **AI Code Generation**: Execute AI-generated code safely
- **Automated Testing**: Run test suites in fresh environments  
- **CI/CD Workflows**: Integration with deployment pipelines
- **Code Analysis**: Analyze and execute code from various sources

### 🔬 Research & Experimentation
- **Data Science**: Isolated environments for data analysis
- **Machine Learning**: Train models in controlled environments
- **Research Reproducibility**: Consistent computational environments

---

## ⚙️ Configuration Options

### Environment Creation Options
```yaml
language: "python"              # Runtime language/environment
image: "python:3.9-slim"        # Custom Docker image
name: "my-dev-environment"      # Human-readable name
git_repo: "https://github.com/user/repo.git"  # Repository to clone
git_branch: "development"       # Branch to checkout
persistent: true                # Keep environment after session
environment_vars:               # Custom environment variables
  API_KEY: "secret"
  DEBUG: "true"
```

### File Operation Types
- `read`: Read file contents
- `write`: Write content to file
- `upload`: Upload local file to sandbox
- `download`: Download file from sandbox  
- `list`: List directory contents
- `delete`: Delete files or directories

### Git Operation Types
- `clone`: Clone repository
- `pull`: Pull latest changes
- `push`: Push changes to remote
- `status`: Check git status
- `commit`: Commit changes
- `checkout`: Switch branches

---

## 🛡️ Security Features

### Isolation & Safety
- **Complete Isolation**: Sandboxes are fully isolated from host systems
- **Resource Limits**: Automatic resource management and limits
- **Secure File Access**: Controlled file system access
- **Network Security**: Configurable network access controls

### Access Control
- **API Key Authentication**: Secure API access
- **Permission Management**: Fine-grained access controls
- **Environment Variables**: Secure secrets management
- **Audit Logging**: Track all environment operations

---

## 🔧 Troubleshooting

### Common Issues

**API Key Missing**:
```
Error: Daytona API key is required
Solution: Set DAYTONA_API_KEY environment variable
```

**Sandbox Not Found**:
```
Error: Sandbox not found
Solution: Use 'list_sandboxes' to see available environments
```

**Code Execution Failed**:
```
Error: Code execution failed with exit code 1
Solution: Check code syntax and dependencies
```

**File Operation Failed**:
```
Error: Permission denied
Solution: Check file permissions and sandbox access
```

### Debug Mode

Enable debug logging by setting:
```bash
export LANGSWARM_DEBUG=true
export DAYTONA_DEBUG=true
```

### Support

- **Documentation**: [Daytona Docs](https://docs.daytona.io)
- **Community**: [Daytona Discord](https://discord.gg/daytona)
- **Issues**: [GitHub Issues](https://github.com/daytonaio/daytona/issues)

---

## 📊 Performance & Limits

### Performance Characteristics
- **Startup Time**: Sub-90ms sandbox creation
- **Code Execution**: Near-native performance
- **File Operations**: High-speed I/O operations
- **Concurrent Sandboxes**: Multiple environments supported

### Resource Limits
- **Memory**: Configurable per sandbox
- **CPU**: Shared compute resources
- **Storage**: Persistent and temporary storage options
- **Network**: Controlled internet access

### Best Practices
- Use persistent environments for long-running development
- Clean up temporary environments regularly
- Optimize Docker images for faster startup
- Monitor resource usage for cost efficiency

---

## 🔄 Integration Examples

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Test in Daytona Environment
  uses: daytona/test-action@v1
  with:
    api_key: ${{ secrets.DAYTONA_API_KEY }}
    test_command: "python -m pytest"
```

### Jupyter Notebook Integration
```python
# Execute notebook cells in Daytona
from daytona_mcp_tool import DaytonaEnvironmentMCPTool

tool = DaytonaEnvironmentMCPTool("daytona-jupyter")
result = tool.run({
    "method": "execute_code",
    "params": {
        "sandbox_id": "jupyter-env",
        "code": notebook_cell_content
    }
})
```

### Custom Workflow Integration
```yaml
workflows:
  custom_development:
    steps:
      - create_environment
      - setup_dependencies  
      - run_tests
      - deploy_if_successful
```

---

## 📈 Roadmap

### Upcoming Features
- [ ] **Multi-language Support**: Additional runtime environments
- [ ] **Advanced Networking**: Custom network configurations
- [ ] **Backup & Restore**: Environment snapshot capabilities
- [ ] **Team Collaboration**: Shared environment management
- [ ] **Resource Monitoring**: Real-time resource usage tracking
- [ ] **Custom Images**: Build and deploy custom environment images

### Integration Roadmap
- [ ] **VS Code Extension**: Direct IDE integration
- [ ] **Slack Bot**: Environment management via Slack
- [ ] **API Gateway**: REST API for external integrations
- [ ] **Monitoring Dashboard**: Web-based environment monitoring

---

## 🤝 Contributing

We welcome contributions! Please see the main LangSwarm contributing guidelines for details on how to contribute to this MCP tool.

### Development Setup
```bash
# Clone the repository
git clone https://github.com/your-org/langswarm.git

# Navigate to the tool directory
cd langswarm/mcp/tools/daytona_environment

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

---

## 📄 License

This tool is part of the LangSwarm project and follows the same licensing terms. See the main project LICENSE file for details.

---

**Made with ❤️ by the LangSwarm Team**

For more information about LangSwarm and its capabilities, visit the [main documentation](../../docs/).
