"""
LangSwarm Enhanced Error Handling

Provides descriptive, user-friendly error messages with actionable guidance.
"""

class LangSwarmError(Exception):
    """Base exception for all LangSwarm errors with enhanced messaging."""
    
    def __init__(self, message: str, suggestion: str = None, example: str = None, context: str = None):
        self.message = message
        self.suggestion = suggestion
        self.example = example
        self.context = context
        
        # Build comprehensive error message
        full_message = f"❌ {message}"
        
        if context:
            full_message += f"\n\n🔍 Context: {context}"
        
        if suggestion:
            full_message += f"\n\n💡 Suggestion: {suggestion}"
        
        if example:
            full_message += f"\n\n📝 Example:\n{example}"
        
        super().__init__(full_message)


class ConfigurationError(LangSwarmError):
    """Configuration-related errors with helpful guidance."""
    pass


class ConfigurationNotFoundError(ConfigurationError):
    """No configuration files found."""
    
    def __init__(self, config_path: str):
        message = "No LangSwarm configuration found"
        
        context = f"Searched in: {config_path}"
        
        suggestion = (
            "Create a configuration file to get started. "
            "You can use either a single unified file or separate files."
        )
        
        example = """Single file approach (recommended):
# langswarm.yaml
version: "1.0"
agents:
  - id: assistant
    model: gpt-4o
    behavior: helpful
    memory: true
workflows:
  - "assistant -> user"

OR multi-file approach:
# agents.yaml + workflows.yaml + other config files"""
        
        super().__init__(message, suggestion, example, context)


class AgentConfigurationError(ConfigurationError):
    """Agent configuration errors."""
    pass


class InvalidAgentBehaviorError(AgentConfigurationError):
    """Invalid agent behavior specified."""
    
    def __init__(self, behavior: str, valid_behaviors: list):
        message = f"Invalid agent behavior: '{behavior}'"
        
        context = f"Valid behaviors are: {', '.join(valid_behaviors)}"
        
        suggestion = (
            "Choose a valid behavior or create a custom system prompt. "
            "Behaviors provide pre-configured personality and capabilities."
        )
        
        example = f"""Valid options:
# Use a built-in behavior
agents:
  - id: my_agent
    behavior: helpful  # or: coding, research, creative, analytical

# Or create custom behavior
agents:
  - id: my_agent
    system_prompt: "You are a specialized assistant for..."
    
# Most popular behaviors:
- helpful: General assistance and problem-solving
- coding: Programming and technical guidance  
- research: Information gathering and analysis
- creative: Idea generation and creative problem-solving"""
        
        super().__init__(message, suggestion, example, context)


class ToolConfigurationError(ConfigurationError):
    """Tool configuration errors."""
    pass


class UnknownToolError(ToolConfigurationError):
    """Tool not found in registry."""
    
    def __init__(self, tool_name: str, available_tools: list = None):
        message = f"Unknown tool: '{tool_name}'"
        
        if available_tools:
            context = f"Available tools: {', '.join(available_tools[:10])}"
            if len(available_tools) > 10:
                context += f" (and {len(available_tools) - 10} more)"
        else:
            context = "No tools are currently loaded"
        
        suggestion = (
            "Check the tool name spelling or ensure the tool is properly configured. "
            "You can also use tool auto-discovery by setting agent behaviors."
        )
        
        example = """Tool configuration options:

# Option 1: Auto-discovery (recommended)
agents:
  - id: coding_agent
    behavior: coding  # Auto-discovers filesystem, github tools

# Option 2: Explicit tool list  
agents:
  - id: my_agent
    tools: [filesystem, web_search]

# Option 3: Custom tool configuration
tools:
  - id: my_custom_tool
    type: mcpfilesystem
    description: "Custom filesystem tool"
    local_mode: true"""
        
        super().__init__(message, suggestion, example, context)


class WorkflowError(LangSwarmError):
    """Workflow-related errors."""
    pass


class WorkflowNotFoundError(WorkflowError):
    """Workflow not found."""
    
    def __init__(self, workflow_id: str, available_workflows: list = None):
        message = f"Workflow not found: '{workflow_id}'"
        
        if available_workflows:
            context = f"Available workflows: {', '.join(available_workflows)}"
        else:
            context = "No workflows are configured"
        
        suggestion = (
            "Check the workflow name or create a new workflow. "
            "You can use simple syntax for common patterns."
        )
        
        example = """Workflow configuration options:

# Simple syntax (covers 80% of use cases)
workflows:
  - "assistant -> user"
  - "researcher -> writer -> editor -> user"

# Named workflows
workflows:
  - id: my_workflow
    simple: "agent1 -> agent2 -> user"
    
# Complex workflows (when needed)  
workflows:
  - id: complex_workflow
    steps:
      - id: step1
        agent: my_agent
        input: ${context.user_input}
        output: {to: user}"""
        
        super().__init__(message, suggestion, example, context)


class InvalidWorkflowSyntaxError(WorkflowError):
    """Invalid workflow syntax."""
    
    def __init__(self, syntax: str, error_details: str = None):
        message = f"Invalid workflow syntax: '{syntax}'"
        
        context = error_details if error_details else "Syntax parsing failed"
        
        suggestion = (
            "Check the workflow syntax against supported patterns. "
            "Make sure agent names are correct and arrows are properly formatted."
        )
        
        example = """Valid workflow syntax patterns:

# Linear workflow
"agent1 -> user"

# Chained workflow  
"agent1 -> agent2 -> agent3 -> user"

# Parallel workflow
"agent1, agent2, agent3 -> consensus_agent -> user"

# Conditional workflow
"router -> (specialist1 | specialist2) -> user"

# Complex workflow
"intake -> analyzer -> (simple_response | expert1, expert2 -> consensus) -> user"

Common mistakes:
❌ "agent1 -> -> user"        # Double arrows
❌ "agent1 - user"           # Missing >
❌ "agent1 → user"           # Wrong arrow type
✅ "agent1 -> user"          # Correct"""
        
        super().__init__(message, suggestion, example, context)


class MemoryConfigurationError(ConfigurationError):
    """Memory configuration errors."""
    pass


class InvalidMemoryTierError(MemoryConfigurationError):
    """Invalid memory tier specified."""
    
    def __init__(self, tier: str):
        message = f"Invalid memory tier: '{tier}'"
        
        context = "Memory Made Simple supports 3 tiers for different complexity levels"
        
        suggestion = (
            "Choose an appropriate memory tier based on your needs. "
            "Each tier provides different levels of configuration complexity."
        )
        
        example = """Memory tier options:

# Tier 1: Development (zero configuration)
memory: true  # SQLite auto-configured

# Tier 2: Production (smart backend selection)  
memory: production  # Auto-detects optimal backend:
                   # - Google Cloud → BigQuery
                   # - AWS → Elasticsearch  
                   # - Redis available → Redis
                   # - Fallback → ChromaDB

# Tier 3: Custom (full control)
memory:
  backend: chromadb
  settings:
    persist_directory: "/custom/path"
    collection_name: "my_collection"

# Disable memory
memory: false"""
        
        super().__init__(message, suggestion, example, context)


class DependencyError(LangSwarmError):
    """Missing dependency errors."""
    pass


class ZeroConfigDependencyError(DependencyError):
    """Zero-config dependencies missing."""
    
    def __init__(self, missing_deps: list = None):
        message = "Zero-config functionality requires additional dependencies"
        
        deps = missing_deps or ["psutil", "requests"]
        context = f"Missing dependencies: {', '.join(deps)}"
        
        suggestion = (
            "Install the required dependencies to enable auto-discovery and smart defaults. "
            "These dependencies help LangSwarm detect your environment and configure optimal settings."
        )
        
        example = f"""Install missing dependencies:

# Install specific packages
pip install {' '.join(deps)}

# Or install LangSwarm with all dependencies
pip install langswarm[all]

# Or continue with manual configuration (no auto-discovery)
# Configure agents, tools, and workflows explicitly in your YAML files"""
        
        super().__init__(message, suggestion, example, context)


class AgentExecutionError(LangSwarmError):
    """Agent execution errors."""
    pass


class AgentToolError(AgentExecutionError):
    """Tool execution errors within agents."""
    
    def __init__(self, tool_name: str, agent_id: str, error_details: str = None):
        message = f"Tool '{tool_name}' failed in agent '{agent_id}'"
        
        context = error_details if error_details else "Tool execution failed"
        
        suggestion = (
            "Check the tool configuration and ensure it's properly registered. "
            "Verify that the tool has the required permissions and dependencies."
        )
        
        example = f"""Tool troubleshooting steps:

1. Verify tool configuration:
tools:
  - id: {tool_name}
    type: mcp{tool_name}  # Check tool type
    local_mode: true      # Try local mode first
    
2. Check agent tool assignment:
agents:
  - id: {agent_id}
    tools: [{tool_name}]  # Ensure tool is listed
    
3. Test tool independently:
python -c "
from langswarm.core.config import LangSwarmConfigLoader
loader = LangSwarmConfigLoader()
# Test tool loading and basic functionality
"

4. Check tool dependencies and permissions"""
        
        super().__init__(message, suggestion, example, context)


def create_helpful_error(error_type: str, **kwargs) -> LangSwarmError:
    """Factory function to create helpful errors based on type."""
    
    error_classes = {
        'config_not_found': ConfigurationNotFoundError,
        'invalid_behavior': InvalidAgentBehaviorError,
        'unknown_tool': UnknownToolError,
        'workflow_not_found': WorkflowNotFoundError,
        'invalid_workflow_syntax': InvalidWorkflowSyntaxError,
        'invalid_memory_tier': InvalidMemoryTierError,
        'zero_config_deps': ZeroConfigDependencyError,
        'agent_tool_error': AgentToolError,
    }
    
    error_class = error_classes.get(error_type, LangSwarmError)
    return error_class(**kwargs)


def format_validation_errors(errors: list) -> str:
    """Format multiple validation errors into a helpful message."""
    
    if not errors:
        return "✅ No validation errors found"
    
    message = f"❌ Found {len(errors)} configuration error(s):\n\n"
    
    for i, error in enumerate(errors, 1):
        message += f"{i}. {error}\n"
    
    message += "\n💡 Tips for fixing configuration errors:\n"
    message += "• Check YAML syntax and indentation\n"
    message += "• Verify agent and tool names are correct\n"
    message += "• Ensure all required fields are provided\n"
    message += "• Use simple syntax for common patterns\n"
    message += "\n📚 See documentation: docs/SIMPLIFIED_LANGSWARM_GUIDE.md"
    
    return message 