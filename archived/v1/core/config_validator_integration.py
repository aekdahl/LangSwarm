"""
Configuration Validator Integration

Integrates real-time validation into the LangSwarm configuration loading process
with helpful error messages and suggestions.
"""

import os
from typing import Dict, Any, List, Optional
from functools import wraps

try:
    from langswarm.core.validation import validate_config_dict, ValidationResult
    from langswarm.core.errors import format_validation_errors, LangSwarmError
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    ValidationResult = None


def validate_during_loading(func):
    """Decorator to add validation during configuration loading."""
    
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Call original method
        result = func(self, *args, **kwargs)
        
        # Add validation if available
        if VALIDATION_AVAILABLE and hasattr(self, 'config_data') and self.config_data:
            validation_result = validate_config_dict(self.config_data)
            
            if not validation_result.is_valid:
                # Print validation errors as warnings (non-blocking)
                print("❌ Configuration validation errors:")
                for error in validation_result.errors:
                    print(f"  - {error}")
                
                if validation_result.suggestions:
                    print("\n💡 Suggestions:")
                    for suggestion in validation_result.suggestions[:3]:  # Show top 3
                        print(f"  - {suggestion}")
            
            if validation_result.warnings:
                print("⚠️  Configuration warnings:")
                for warning in validation_result.warnings[:5]:  # Show top 5
                    print(f"  - {warning}")
        
        return result
    
    return wrapper


def validate_agent_tools(agents: List[Dict[str, Any]], available_tools: Dict[str, Any]) -> List[str]:
    """Validate that agents reference existing tools."""
    errors = []
    available_tool_ids = set(available_tools.keys())
    
    for agent in agents:
        agent_id = agent.get('id', 'unknown')
        agent_tools = agent.get('tools', [])
        
        # Handle both tool auto-discovery and explicit tool lists
        if isinstance(agent_tools, list):
            for tool_name in agent_tools:
                if tool_name not in available_tool_ids:
                    # Get suggestions for similar tool names
                    suggestions = get_tool_suggestions(tool_name, available_tool_ids)
                    suggestion_text = f" (did you mean: {', '.join(suggestions)}?)" if suggestions else ""
                    
                    errors.append(f"agents.tools: Agent {agent_id} references unknown tool: {tool_name}{suggestion_text}")
    
    return errors


def get_tool_suggestions(tool_name: str, available_tools: set) -> List[str]:
    """Get suggestions for similar tool names."""
    suggestions = []
    
    # Simple similarity matching
    for available_tool in available_tools:
        # Check if tool name is a substring or similar
        if (tool_name.lower() in available_tool.lower() or 
            available_tool.lower() in tool_name.lower() or
            abs(len(tool_name) - len(available_tool)) <= 2):
            suggestions.append(available_tool)
    
    return suggestions[:3]  # Return top 3 suggestions


def validate_workflow_agents(workflows: List[Any], agent_ids: set) -> List[str]:
    """Validate that workflows reference existing agents."""
    errors = []
    
    for i, workflow in enumerate(workflows):
        if isinstance(workflow, str):
            # Simple syntax workflow
            errors.extend(validate_simple_workflow_agents(workflow, agent_ids, f"workflows[{i}]"))
        elif isinstance(workflow, dict):
            if "simple" in workflow or "workflow" in workflow:
                syntax = workflow.get("simple") or workflow.get("workflow")
                workflow_id = workflow.get("id", f"workflows[{i}]")
                errors.extend(validate_simple_workflow_agents(syntax, agent_ids, workflow_id))
    
    return errors


def validate_simple_workflow_agents(syntax: str, agent_ids: set, workflow_ref: str) -> List[str]:
    """Validate agents in simple workflow syntax."""
    errors = []
    
    if not syntax or "->" not in syntax:
        return errors
    
    # Extract agent names from workflow syntax
    parts = [part.strip() for part in syntax.split("->")]
    
    for part in parts[:-1]:  # Exclude 'user' at the end
        # Handle different syntax patterns
        if "," in part:
            # Parallel: agent1, agent2
            agent_names = [name.strip() for name in part.split(",")]
        elif "|" in part:
            # Conditional: (agent1 | agent2)
            conditional_part = part.strip("()")
            agent_names = [name.strip() for name in conditional_part.split("|")]
        else:
            # Simple: agent
            agent_names = [part.strip()]
        
        # Check each agent
        for agent_name in agent_names:
            if agent_name and agent_name != "user" and agent_name not in agent_ids:
                # Get suggestions for similar agent names
                suggestions = get_tool_suggestions(agent_name, agent_ids)
                suggestion_text = f" (did you mean: {', '.join(suggestions)}?)" if suggestions else ""
                
                errors.append(f"{workflow_ref}: Unknown agent '{agent_name}' in workflow{suggestion_text}")
    
    return errors


def create_configuration_summary(config: Dict[str, Any]) -> str:
    """Create a helpful summary of the configuration."""
    summary = []
    
    # Count components
    agents = config.get("agents", [])
    workflows = config.get("workflows", [])
    tools = config.get("tools", [])
    
    summary.append(f"📊 Configuration Summary:")
    summary.append(f"   • {len(agents)} agent(s) defined")
    summary.append(f"   • {len(workflows)} workflow(s) defined")
    summary.append(f"   • {len(tools)} tool(s) configured")
    
    # Memory configuration
    memory = config.get("memory")
    if memory:
        if memory is True:
            summary.append("   • Memory: Development (SQLite)")
        elif isinstance(memory, str):
            summary.append(f"   • Memory: {memory.title()} tier")
        else:
            summary.append("   • Memory: Custom configuration")
    else:
        summary.append("   • Memory: Disabled")
    
    # Show agent behaviors if available
    if agents:
        behaviors = [agent.get("behavior", "custom") for agent in agents if isinstance(agent, dict)]
        if behaviors:
            unique_behaviors = list(set(behaviors))
            summary.append(f"   • Agent behaviors: {', '.join(unique_behaviors)}")
    
    return "\n".join(summary)


def suggest_improvements(config: Dict[str, Any]) -> List[str]:
    """Suggest configuration improvements."""
    suggestions = []
    
    # Check for missing version
    if "version" not in config:
        suggestions.append("Add version field for better compatibility: version: '1.0'")
    
    # Check for project name
    if "project_name" not in config:
        suggestions.append("Add project_name for better organization: project_name: 'my-project'")
    
    # Check agent configurations
    agents = config.get("agents", [])
    if agents:
        for agent in agents:
            if isinstance(agent, dict):
                agent_id = agent.get("id", "unknown")
                
                # Suggest memory for agents without it
                if not agent.get("memory_enabled") and not config.get("memory"):
                    suggestions.append(f"Consider enabling memory for agent '{agent_id}': memory_enabled: true")
                
                # Suggest tools for coding agents
                if agent.get("behavior") == "coding" and not agent.get("tools"):
                    suggestions.append(f"Coding agent '{agent_id}' might benefit from tools: tools: [filesystem]")
    
    # Check for simple workflow syntax opportunities
    workflows = config.get("workflows", [])
    complex_workflows = [w for w in workflows if isinstance(w, dict) and "steps" in w]
    if complex_workflows:
        suggestions.append("Consider using simple workflow syntax for better readability: 'agent1 -> agent2 -> user'")
    
    return suggestions[:5]  # Return top 5 suggestions


def print_configuration_help(config: Dict[str, Any]):
    """Print helpful information about the configuration."""
    if not VALIDATION_AVAILABLE:
        return
    
    print(create_configuration_summary(config))
    
    # Show improvement suggestions
    suggestions = suggest_improvements(config)
    if suggestions:
        print("\n💡 Improvement suggestions:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    print("\n📚 Documentation:")
    print("   • Quick start: docs/SIMPLIFIED_LANGSWARM_GUIDE.md")
    print("   • Examples: docs/simplification/BEFORE_AND_AFTER_EXAMPLES.md")
    print("   • Migration: docs/simplification/MIGRATION_GUIDE.md")


# Integration hooks for the main configuration loader
def integrate_validation_hooks():
    """Integrate validation hooks into the main configuration system."""
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        
        # Add validation to the unified config loading
        if hasattr(LangSwarmConfigLoader, '_load_unified_config'):
            original_method = LangSwarmConfigLoader._load_unified_config
            LangSwarmConfigLoader._load_unified_config = validate_during_loading(original_method)
            
        print("🔧 Validation hooks integrated successfully")
        return True
        
    except ImportError:
        print("⚠️  Could not integrate validation hooks - core modules not available")
        return False
    except Exception as e:
        print(f"⚠️  Error integrating validation hooks: {e}")
        return False


if __name__ == "__main__":
    # Test the validation integration
    print("🧪 Testing validation integration...")
    
    test_config = {
        "version": "1.0",
        "agents": [
            {"id": "test_agent", "model": "gpt-4o", "behavior": "helpful"}
        ],
        "workflows": ["test_agent -> user"]
    }
    
    print(create_configuration_summary(test_config))
    
    suggestions = suggest_improvements(test_config)
    if suggestions:
        print("\n💡 Suggestions:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    print("\n✅ Validation integration test complete") 