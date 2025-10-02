# 🏠 Self-Hosted Daytona MCP Server

A dedicated MCP server for integrating with self-hosted Daytona instances, providing secure on-premises development environments with full control over your infrastructure.

## Overview

This MCP server provides integration with **self-hosted Daytona instances** running on your own infrastructure. Unlike the cloud-based Daytona tool, this server:

- 🏗️ **Runs as HTTP MCP Server** (not local mode) for distributed deployment
- 🔧 **Uses Daytona CLI** for direct integration with self-hosted instances
- 🏠 **On-Premises Control** - complete control over your development environments
- 🔒 **Enhanced Security** - all data and code stays within your infrastructure
- ⚙️ **Customizable** - modify and extend for your specific needs

---

## 🏗️ Architecture

### Deployment Model
```
LangSwarm Agent → HTTP Request → Self-Hosted MCP Server → Daytona CLI → Self-Hosted Daytona → Local Docker Containers
```

### Key Differences from Cloud Version

| Feature | Cloud Version | Self-Hosted Version |
|---------|---------------|-------------------|
| **Deployment** | Local mode (API client) | HTTP server mode |
| **Daytona Integration** | Daytona Cloud API | Daytona CLI commands |
| **Infrastructure** | Daytona's managed cloud | Your own servers |
| **Network** | Internet required | Can run air-gapped |
| **Customization** | Limited to API features | Full CLI access |
| **Data Location** | Daytona's servers | Your infrastructure |

---

## 🛠️ Installation & Setup

### Prerequisites

1. **Self-Hosted Daytona Instance** running and accessible
2. **Daytona CLI** installed on the MCP server machine
3. **Docker** installed (for Daytona workspaces)
4. **Python 3.8+** and required dependencies

### Step 1: Install Self-Hosted Daytona

Download and install Daytona from the official repository:

```bash
# Download latest Daytona binary
curl -sf https://download.daytona.io/daytona/install.sh | sh

# Start Daytona server
daytona server

# Configure your profile (if needed)
daytona profile use local
```

### Step 2: Install MCP Server Dependencies

```bash
# Install Python dependencies
pip install fastapi uvicorn pydantic aiohttp

# Ensure Daytona CLI is accessible
daytona version
```

### Step 3: Configure Environment

```bash
# Optional: Set Daytona server URL if not default
export DAYTONA_SERVER_URL="http://localhost:8080"

# Optional: Configure Daytona profile if needed
daytona profile list
```

### Step 4: Start MCP Server

```bash
# Run the self-hosted MCP server
cd langswarm/mcp/tools/daytona_self_hosted
python main.py

# Server will start on http://localhost:8001
```

---

## 🔧 Configuration

### LangSwarm Configuration

```yaml
# For self-hosted Daytona integration
tools:
  - id: daytona_self_hosted
    type: remote_mcp
    url: "http://localhost:8001"  # Your MCP server URL
    description: "Self-hosted Daytona development environments"
    permission: authenticated
    methods:
      - create_sandbox
      - execute_code
      - execute_shell
      - file_operation
      - git_operation
      - list_sandboxes
      - delete_sandbox
      - get_sandbox_info
```

### Advanced Configuration

```yaml
# Production deployment with multiple instances
tools:
  - id: daytona_dev
    type: remote_mcp
    url: "http://daytona-mcp-dev.internal:8001"
    description: "Development environment Daytona"
    permission: developer
    
  - id: daytona_prod
    type: remote_mcp
    url: "http://daytona-mcp-prod.internal:8001"
    description: "Production environment Daytona"
    permission: admin
```

---

## 🐳 Docker Deployment

### Docker Compose Example

```yaml
# docker-compose.yml for self-hosted Daytona + MCP Server
version: '3.8'

services:
  # Self-hosted Daytona server
  daytona-server:
    image: daytonaio/daytona:latest
    ports:
      - "8080:8080"
    volumes:
      - daytona_data:/data
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DAYTONA_WORKSPACE_DIR=/workspaces
    command: ["daytona", "server", "--host", "0.0.0.0"]

  # Self-hosted Daytona MCP Server
  daytona-mcp:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
    depends_on:
      - daytona-server
    environment:
      - DAYTONA_SERVER_URL=http://daytona-server:8080
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # For CLI access to Docker

volumes:
  daytona_data:
```

### Dockerfile for MCP Server

```dockerfile
# Dockerfile for self-hosted Daytona MCP Server
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Daytona CLI
RUN curl -sf https://download.daytona.io/daytona/install.sh | sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy MCP server code
COPY langswarm/mcp/tools/daytona_self_hosted /app
WORKDIR /app

# Expose MCP server port
EXPOSE 8001

# Start MCP server
CMD ["python", "main.py"]
```

---

## 🚀 Usage Examples

### Creating Development Environment

```bash
# HTTP POST to MCP server
curl -X POST http://localhost:8001/create_sandbox \
  -H "Content-Type: application/json" \
  -d '{
    "language": "python",
    "name": "ml-project",
    "git_repo": "https://github.com/user/ml-project.git",
    "environment_vars": {
      "PYTHONPATH": "/workspace",
      "ENV": "development"
    }
  }'
```

### Executing Code

```bash
curl -X POST http://localhost:8001/execute_code \
  -H "Content-Type: application/json" \
  -d '{
    "sandbox_id": "ml-project",
    "code": "import pandas as pd\nprint(pd.__version__)",
    "language": "python"
  }'
```

### LangSwarm Integration

```python
# Via LangSwarm agent
"Create a Python development environment and clone my FastAPI project"
"Run the unit tests in my development workspace"
"List all my current development environments"
"Execute a shell script to deploy my application"
```

---

## ⚙️ Operation Details

### Workspace Management

The self-hosted version uses Daytona CLI commands:

- **Create**: `daytona create [repo] --name workspace-name`
- **List**: `daytona list`
- **Execute**: `daytona exec workspace-name "command"`
- **Delete**: `daytona delete workspace-name --force`
- **Info**: `daytona info workspace-name`

### File Operations

File operations are performed via `daytona exec` commands:

```bash
# Read file
daytona exec workspace-name "cat /path/to/file"

# Write file
daytona exec workspace-name "echo 'content' > /path/to/file"

# List directory
daytona exec workspace-name "ls -la /path/to/directory"
```

### Git Operations

Git operations run within workspaces:

```bash
# Clone repository
daytona exec workspace-name "git clone https://github.com/user/repo.git"

# Commit changes
daytona exec workspace-name "cd /project && git add -A && git commit -m 'Update'"

# Push changes
daytona exec workspace-name "cd /project && git push"
```

---

## 🔒 Security Considerations

### Network Security

- **Internal Networks**: Deploy MCP server on internal networks only
- **Authentication**: Implement proper authentication for MCP endpoints
- **TLS/SSL**: Use HTTPS in production deployments
- **Firewall Rules**: Restrict access to Daytona and MCP server ports

### Access Control

```yaml
# Example with authentication
tools:
  - id: daytona_self_hosted
    type: remote_mcp
    url: "https://daytona-mcp.internal:8001"
    description: "Self-hosted Daytona environments"
    permission: authenticated
    auth:
      type: api_key
      key: "${DAYTONA_MCP_API_KEY}"
```

### Resource Limits

```bash
# Configure Docker resource limits for workspaces
export DAYTONA_WORKSPACE_MEMORY_LIMIT="2g"
export DAYTONA_WORKSPACE_CPU_LIMIT="1.0"
```

---

## 🔧 Troubleshooting

### Common Issues

**MCP Server Won't Start**
```bash
# Check if Daytona CLI is accessible
daytona version

# Verify Docker access
docker ps

# Check port availability
netstat -tlnp | grep 8001
```

**Workspace Creation Fails**
```bash
# Check Daytona server status
daytona server status

# Verify Docker daemon
systemctl status docker

# Check available resources
df -h
docker system df
```

**CLI Command Failures**
```bash
# Verify Daytona configuration
daytona profile list
daytona profile use local

# Check workspace status
daytona list
daytona info workspace-name
```

### Debug Mode

Enable debug logging:

```bash
export DAYTONA_LOG_LEVEL=debug
export MCP_DEBUG=true
python main.py
```

### Health Checks

```bash
# Check MCP server health
curl http://localhost:8001/schema

# Check Daytona server health
curl http://localhost:8080/health

# Verify workspace functionality
daytona create --name test-workspace
daytona exec test-workspace "echo 'Hello, World!'"
daytona delete test-workspace --force
```

---

## 📊 Performance & Scaling

### Performance Characteristics

- **Workspace Creation**: 2-5 seconds (depending on base image)
- **Code Execution**: Near-native performance
- **File Operations**: Fast local filesystem access
- **Git Operations**: Network-dependent

### Scaling Options

1. **Horizontal Scaling**: Deploy multiple MCP server instances
2. **Load Balancing**: Use nginx/HAProxy for distribution
3. **Resource Allocation**: Dedicated compute nodes for workspaces
4. **Storage**: Network-attached storage for workspace persistence

### Monitoring

```yaml
# Example monitoring configuration
monitoring:
  metrics:
    - workspace_count
    - execution_time
    - resource_usage
  alerts:
    - high_memory_usage
    - workspace_creation_failures
    - disk_space_low
```

---

## 🔄 Integration Patterns

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Test in Self-Hosted Daytona
  run: |
    curl -X POST $DAYTONA_MCP_URL/create_sandbox \
      -d '{"name": "ci-test", "git_repo": "${{ github.repository }}"}'
    
    curl -X POST $DAYTONA_MCP_URL/execute_code \
      -d '{"sandbox_id": "ci-test", "code": "python -m pytest"}'
```

### Development Workflow

```bash
# Create development environment
curl -X POST /create_sandbox -d '{"name": "feature-branch"}'

# Develop and test
curl -X POST /execute_code -d '{"sandbox_id": "feature-branch", "code": "..."}'

# Commit and cleanup
curl -X POST /git_operation -d '{"sandbox_id": "feature-branch", "operation": "commit"}'
curl -X POST /delete_sandbox -d '{"sandbox_id": "feature-branch"}'
```

---

## 🔮 Future Enhancements

### Planned Features

- [ ] **Multi-tenancy**: Support for multiple teams/projects
- [ ] **Resource Quotas**: Per-user/team resource limits
- [ ] **Workspace Templates**: Pre-configured environment templates
- [ ] **Backup/Restore**: Workspace snapshot capabilities
- [ ] **Metrics Dashboard**: Real-time monitoring interface

### Integration Roadmap

- [ ] **Kubernetes Support**: Deploy workspaces on K8s clusters
- [ ] **LDAP/SSO Integration**: Enterprise authentication
- [ ] **Audit Logging**: Comprehensive operation tracking
- [ ] **Custom Providers**: Support for additional infrastructure providers

---

## 📄 Comparison with Cloud Version

| Feature | Cloud Version | Self-Hosted Version |
|---------|---------------|-------------------|
| **Setup Complexity** | Minimal (API key only) | Moderate (self-hosted setup) |
| **Infrastructure Control** | Limited | Complete |
| **Data Privacy** | Daytona's servers | Your infrastructure |
| **Customization** | API limitations | Full CLI access |
| **Scaling** | Managed by Daytona | Manual/custom |
| **Maintenance** | None required | Self-managed |
| **Network Requirements** | Internet access | Can be air-gapped |
| **Cost Model** | Pay-per-use | Infrastructure costs |

---

## 🤝 Contributing

To contribute to the self-hosted Daytona integration:

1. **Fork the repository**
2. **Create feature branch**
3. **Add/modify self-hosted specific features**
4. **Test with actual self-hosted Daytona instance**
5. **Submit pull request**

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/langswarm.git

# Set up development environment
cd langswarm/mcp/tools/daytona_self_hosted
pip install -r requirements-dev.txt

# Start development server
python main.py --debug
```

---

**Made with ❤️ for the self-hosted development community**

For more information about LangSwarm and its capabilities, visit the [main documentation](../../../docs/).


