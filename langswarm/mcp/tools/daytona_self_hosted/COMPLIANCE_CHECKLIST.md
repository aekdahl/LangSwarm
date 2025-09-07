# Daytona Self-Hosted Tool - Compliance Checklist

**Status**: 🚨 **MAJOR RESTRUCTURING NEEDED**  
**Priority**: HIGH - Missing core workflow infrastructure

## 🚨 Critical Issues

### 1. Missing Core Files
- [ ] **Create `agents.yaml`** - No agent definitions exist
- [ ] **Create `workflows.yaml`** - No workflow definitions exist  
- [ ] **Create `template.md`** - No LLM instructions exist
- [ ] **Create `__init__.py`** - Package initialization missing

### 2. Tool Structure Issues
- [ ] **Verify main.py class structure** - Ensure follows MCP tool standards
- [ ] **Add standardized error handling** - Implement error standards
- [ ] **Verify `_bypass_pydantic = True`** - Required for workflow compatibility

## 📝 Required Changes

### 1. Create agents.yaml
```yaml
agents:
  daytona_manager:
    description: "Manages Daytona self-hosted environment operations"
    model: "gpt-4o"
    instructions: |
      You manage Daytona self-hosted development environments.
      
      CAPABILITIES:
      - Create and configure development environments
      - Manage container lifecycle
      - Handle workspace operations
      - Monitor environment health
    
    tools:
      - daytona_self_hosted
    
    response_mode: "conversational"

  environment_validator:
    description: "Validates Daytona environment configurations"
    model: "gpt-4o"
    instructions: |
      You validate Daytona environment configurations for security and correctness.
    
    response_mode: "conversational"

  response_formatter:
    description: "Formats Daytona operation results"
    model: "gpt-4o"
    instructions: |
      Format Daytona operation results for user presentation.
    
    response_mode: "conversational"
```

### 2. Create workflows.yaml
```yaml
workflows:
  - id: main_daytona_workflow
    description: "Primary workflow for Daytona self-hosted operations"
    steps:
      - id: validate_request
        agent: environment_validator
        input: |
          user_input: ${user_input}
          user_query: ${user_query}
        output:
          to: validated_request

      - id: execute_operation
        agent: daytona_manager
        input: |
          Validated request: ${context.step_outputs.validate_request}
          
          Execute the Daytona operation safely.
        output:
          to: operation_result

      - id: format_response
        agent: response_formatter
        input: |
          Operation result: ${context.step_outputs.execute_operation}
          Original request: ${context.step_outputs.validate_request}
        output:
          to: user
```

### 3. Create template.md
```markdown
# Daytona Self-Hosted Tool Instructions

You have access to the daytona_self_hosted tool for managing self-hosted Daytona development environments.

## Tool Capabilities

1. **Environment Management**: Create, configure, and manage development environments
2. **Container Operations**: Handle Docker container lifecycle
3. **Workspace Operations**: Manage development workspaces
4. **Health Monitoring**: Monitor environment health and performance

## Usage Patterns

### Direct Tool Calls
For specific operations:
```json
{
  "response": "I'll create that development environment.",
  "mcp": {
    "tool": "daytona_self_hosted",
    "method": "create_environment",
    "params": {"name": "dev-env", "image": "ubuntu:latest"}
  }
}
```

### Intent-Based Calls
For complex operations:
```json
{
  "response": "I'll set up the development environment as requested.",
  "mcp": {
    "tool": "daytona_self_hosted",
    "intent": "create development environment for Python project",
    "context": "user needs Django development setup"
  }
}
```

## Security Guidelines

- Validate all container configurations
- Respect resource limits
- Ensure secure container isolation
- Monitor for security vulnerabilities
```

### 4. Update main.py (if needed)
- [ ] Ensure class name ends with 'MCPTool'
- [ ] Add `_bypass_pydantic = True`
- [ ] Implement standardized error responses
- [ ] Follow developer guide patterns

## ✅ Already Compliant

- [x] Has `readme.md` documentation
- [x] Has Docker infrastructure (`Dockerfile`, `docker-compose.yml`)
- [x] Has `requirements.txt` for dependencies
- [x] Documentation file is lowercase

## ⚠️ Needs Verification

### 1. Main.py Structure
- [ ] Verify class follows `*MCPTool` naming convention
- [ ] Verify `_bypass_pydantic = True` exists
- [ ] Check error handling implementation
- [ ] Ensure proper inheritance from BaseTool

### 2. Container Configuration
- [ ] Verify Docker setup is optimal
- [ ] Check security configurations
- [ ] Validate resource limits
- [ ] Test container networking

## 🧪 Testing Required

- [ ] Test tool registration and discovery
- [ ] Verify workflow execution
- [ ] Test container operations
- [ ] Validate security measures
- [ ] Test error handling

## 📅 Implementation Order

1. **CRITICAL**: Create missing core files (`agents.yaml`, `workflows.yaml`, `template.md`)
2. **HIGH**: Verify and fix main.py structure
3. **MEDIUM**: Test and validate all functionality
4. **LOW**: Optimize Docker configuration

## 🎯 Success Criteria

- [ ] All required files exist and follow standards
- [ ] Tool can be registered and discovered
- [ ] Workflows execute successfully
- [ ] Agents respond appropriately
- [ ] Error handling works correctly
- [ ] Container operations function properly

## 🔍 File Structure Check

Required files:
- [ ] `__init__.py`
- [ ] `main.py` (exists, needs verification)
- [ ] `agents.yaml` (missing)
- [ ] `workflows.yaml` (missing)
- [x] `readme.md` (exists)
- [ ] `template.md` (missing)
- [x] `Dockerfile` (exists)
- [x] `docker-compose.yml` (exists)
- [x] `requirements.txt` (exists)

---

**Estimated Fix Time**: 4-6 hours  
**Risk Level**: High (missing core functionality)  
**Dependencies**: May require main.py updates
