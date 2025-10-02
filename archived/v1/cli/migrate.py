"""
LangSwarm Configuration Migration Tool

Migrate from multi-file configuration to unified single-file configuration.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

def migrate_config(source_dir: str, target_file: str = "langswarm.yaml", project_name: Optional[str] = None):
    """Migrate from multi-file to single-file configuration"""
    
    print(f"🔄 Migrating configuration from {source_dir} to {target_file}")
    
    # Load existing multi-file configuration
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        loader = LangSwarmConfigLoader(source_dir)
        workflows, agents, brokers, tools, tools_metadata = loader.load()
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False
    
    # Convert agents to simplified format
    simplified_agents = []
    for agent_id, agent in agents.items():
        # Try to detect behavior from system prompt
        behavior = _detect_behavior_from_prompt(agent.system_prompt)
        
        agent_config = {
            "id": agent_id,
            "name": getattr(agent, 'name', None) or agent_id.replace('_', ' ').title(),
            "model": getattr(agent, 'model', 'gpt-4o'),
            "agent_type": getattr(agent, 'agent_type', 'generic'),
        }
        
        # Use behavior if detected, otherwise keep original system prompt
        if behavior:
            agent_config["behavior"] = behavior
        else:
            agent_config["system_prompt"] = agent.system_prompt
            
        # Add other agent properties
        if hasattr(agent, 'tools') and agent.tools:
            agent_config["tools"] = [tool.id if hasattr(tool, 'id') else str(tool) for tool in agent.tools]
        
        if hasattr(agent, 'max_tokens') and agent.max_tokens:
            agent_config["max_tokens"] = agent.max_tokens
            
        if hasattr(agent, 'temperature') and agent.temperature is not None:
            agent_config["temperature"] = agent.temperature
            
        simplified_agents.append(agent_config)
    
    # Convert tools to simplified format
    simplified_tools = {}
    for tool in tools:
        tool_id = getattr(tool, 'id', 'unknown')
        tool_type = type(tool).__name__.lower().replace('tool', '').replace('mcp', '')
        
        tool_config = {
            "local_mode": getattr(tool, 'local_mode', True),
        }
        
        # Add tool-specific settings
        if hasattr(tool, 'config') and tool.config:
            tool_config["settings"] = tool.config
        elif hasattr(tool, 'settings') and tool.settings:
            tool_config["settings"] = tool.settings
            
        simplified_tools[tool_id] = tool_config
    
    # Convert workflows to simplified format
    simplified_workflows = []
    for workflow_id, workflow in workflows.items():
        workflow_config = {
            "id": workflow_id,
            "name": workflow.get("name", workflow_id.replace('_', ' ').title()),
            "steps": workflow.get("steps", [])
        }
        simplified_workflows.append(workflow_config)
    
    # Build unified configuration
    unified_config = {
        "version": "1.0",
        "project_name": project_name or os.path.basename(os.path.abspath(source_dir)),
        "langswarm": {
            "debug": False,
            "log_level": "INFO",
            "config_validation": True
        },
        "agents": simplified_agents,
        "tools": simplified_tools,
        "workflows": simplified_workflows,
        "memory": {
            "enabled": True,
            "backend": "auto"
        }
    }
    
    # Add advanced configurations if they exist
    advanced_config = {}
    
    if brokers:
        advanced_brokers = []
        for broker_id, broker in brokers.items():
            broker_config = {
                "id": broker_id,
                "type": getattr(broker, 'type', 'internal'),
                "settings": getattr(broker, 'settings', {})
            }
            advanced_brokers.append(broker_config)
        advanced_config["brokers"] = advanced_brokers
    
    # Add other advanced configs if files exist
    for config_file in ["queues.yaml", "registries.yaml", "plugins.yaml", "retrievers.yaml"]:
        file_path = os.path.join(source_dir, config_file)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            section_name = config_file.replace('.yaml', '')
            if section_name in data:
                advanced_config[section_name] = data[section_name]
    
    if advanced_config:
        unified_config["advanced"] = advanced_config
    
    # Write unified configuration
    try:
        with open(target_file, 'w') as f:
            yaml.dump(unified_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Successfully migrated configuration to {target_file}")
        print(f"📊 Simplified from {_count_original_files(source_dir)} files to 1 file")
        
        # Show statistics
        _show_migration_stats(source_dir, target_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing configuration: {e}")
        return False

def validate_config(config_file: str):
    """Validate unified configuration file"""
    
    print(f"🔍 Validating configuration: {config_file}")
    
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        return False
    
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        loader = LangSwarmConfigLoader(config_file)
        
        if loader._is_unified_config():
            unified_config = loader._load_unified_config()
            errors = unified_config.validate()
            
            if errors:
                print("❌ Configuration validation errors:")
                for error in errors:
                    print(f"  - {error.section or 'general'}.{error.field}: {error.message}")
                return False
            else:
                print("✅ Configuration is valid")
                return True
        else:
            print("❌ Not a unified configuration file")
            return False
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def split_config(unified_file: str, output_dir: str = "./multi-file-config"):
    """Split unified configuration back to multi-file format"""
    
    print(f"🔄 Splitting unified configuration to multi-file format")
    
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        loader = LangSwarmConfigLoader(unified_file)
        unified_config = loader.load_single_config(unified_file)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert back to legacy format
        legacy_data = unified_config.to_legacy_format()
        
        # Write separate files
        files_written = 0
        
        for section, data in legacy_data.items():
            if data:  # Only write non-empty sections
                filename = f"{section}.yaml"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w') as f:
                    yaml.dump({section: data}, f, default_flow_style=False)
                
                files_written += 1
                print(f"  ✅ Created {filename}")
        
        print(f"✅ Successfully split configuration into {files_written} files in {output_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Error splitting configuration: {e}")
        return False

def _detect_behavior_from_prompt(system_prompt: str) -> Optional[str]:
    """Try to detect behavior type from system prompt"""
    if not system_prompt:
        return None
    
    prompt_lower = system_prompt.lower()
    
    # Simple keyword detection
    if any(word in prompt_lower for word in ["code", "programming", "debug", "developer"]):
        return "coding"
    elif any(word in prompt_lower for word in ["research", "analyze", "study", "investigate"]):
        return "research"
    elif any(word in prompt_lower for word in ["creative", "write", "story", "brainstorm"]):
        return "creative"
    elif any(word in prompt_lower for word in ["support", "help", "customer", "assist"]):
        return "helpful"
    elif any(word in prompt_lower for word in ["analytic", "data", "logic", "reasoning"]):
        return "analytical"
    else:
        # Default to helpful if it seems like a generic assistant prompt
        if any(word in prompt_lower for word in ["helpful", "assistant", "polite", "informative"]):
            return "helpful"
    
    return None

def _count_original_files(source_dir: str) -> int:
    """Count original configuration files"""
    config_files = [
        "agents.yaml", "tools.yaml", "workflows.yaml", "brokers.yaml",
        "queues.yaml", "registries.yaml", "plugins.yaml", "retrievers.yaml"
    ]
    
    count = 0
    for filename in config_files:
        if os.path.exists(os.path.join(source_dir, filename)):
            count += 1
    
    return count

def _show_migration_stats(source_dir: str, target_file: str):
    """Show migration statistics"""
    # Count lines in original files
    original_lines = 0
    original_files = 0
    
    config_files = [
        "agents.yaml", "tools.yaml", "workflows.yaml", "brokers.yaml",
        "queues.yaml", "registries.yaml", "plugins.yaml", "retrievers.yaml"
    ]
    
    for filename in config_files:
        filepath = os.path.join(source_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                original_lines += len(f.readlines())
            original_files += 1
    
    # Count lines in new file
    with open(target_file, 'r') as f:
        new_lines = len(f.readlines())
    
    # Calculate reduction
    line_reduction = ((original_lines - new_lines) / original_lines * 100) if original_lines > 0 else 0
    
    print("\n📊 Migration Statistics:")
    print(f"  Files: {original_files} → 1 ({original_files - 1} fewer)")
    print(f"  Lines: {original_lines} → {new_lines} ({line_reduction:.1f}% reduction)")
    print(f"  Complexity: Significantly reduced")

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="LangSwarm Configuration Migration Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Migrate multi-file to single-file configuration")
    migrate_parser.add_argument("source", help="Source directory containing multi-file configuration")
    migrate_parser.add_argument("--output", "-o", default="langswarm.yaml", help="Output file name")
    migrate_parser.add_argument("--project-name", "-p", help="Project name for the configuration")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate unified configuration file")
    validate_parser.add_argument("config", help="Configuration file to validate")
    
    # Split command
    split_parser = subparsers.add_parser("split", help="Split unified configuration to multi-file format")
    split_parser.add_argument("config", help="Unified configuration file to split")
    split_parser.add_argument("--output-dir", "-o", default="./multi-file-config", help="Output directory")
    
    args = parser.parse_args()
    
    if args.command == "migrate":
        success = migrate_config(args.source, args.output, args.project_name)
        sys.exit(0 if success else 1)
        
    elif args.command == "validate":
        success = validate_config(args.config)
        sys.exit(0 if success else 1)
        
    elif args.command == "split":
        success = split_config(args.config, args.output_dir)
        sys.exit(0 if success else 1)
        
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 