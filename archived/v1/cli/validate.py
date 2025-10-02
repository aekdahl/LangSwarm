#!/usr/bin/env python3
"""
LangSwarm Configuration Validator CLI

Provides real-time validation of LangSwarm configurations with helpful error messages and suggestions.

Usage:
    python -m langswarm.cli.validate <config_file>
    python -m langswarm.cli.validate --interactive
    python -m langswarm.cli.validate --check-examples
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from langswarm.core.validation import validate_config_file, validate_config_dict, ValidationResult
    from langswarm.core.config import LangSwarmConfigLoader
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Run from project root: python -m langswarm.cli.validate")
    sys.exit(1)


def validate_file(file_path: str, verbose: bool = False) -> bool:
    """Validate a single configuration file."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    print(f"🔍 Validating: {file_path}")
    print("-" * 50)
    
    # Run validation
    result = validate_config_file(file_path)
    
    # Print results
    print(result.get_summary())
    
    if verbose and result.is_valid:
        print("\n📊 Additional checks:")
        try:
            # Try loading with LangSwarm loader
            loader = LangSwarmConfigLoader(file_path)
            workflows, agents, tools, brokers, metadata = loader.load()
            print(f"   ✅ Successfully loaded {len(agents)} agents, {len(workflows)} workflows, {len(tools)} tools")
        except Exception as e:
            print(f"   ⚠️  Loading warning: {e}")
    
    return result.is_valid


def interactive_validation():
    """Interactive configuration validation."""
    print("🎯 LangSwarm Interactive Configuration Validator")
    print("=" * 60)
    print("Create and validate your LangSwarm configuration step by step.\n")
    
    # Start with basic structure
    config = {
        "version": "1.0",
        "agents": [],
        "workflows": []
    }
    
    # Guide user through configuration
    print("📝 Let's build your configuration:")
    
    # Add agents
    while True:
        print("\n🤖 Add an agent:")
        agent_id = input("   Agent ID (e.g., 'assistant'): ").strip()
        if not agent_id:
            break
        
        model = input("   Model (default: gpt-4o): ").strip() or "gpt-4o"
        behavior = input("   Behavior (helpful/coding/research/creative): ").strip() or "helpful"
        
        agent = {
            "id": agent_id,
            "model": model,
            "behavior": behavior
        }
        
        # Optional memory
        memory = input("   Enable memory? (y/n, default: n): ").strip().lower()
        if memory in ['y', 'yes']:
            agent["memory_enabled"] = True
        
        config["agents"].append(agent)
        
        # Validate current config
        result = validate_config_dict(config)
        if not result.is_valid:
            print(f"\n⚠️  Current issues: {len(result.errors)} errors")
            for error in result.errors[-3:]:  # Show last 3 errors
                print(f"   • {error}")
        
        more = input("\n   Add another agent? (y/n): ").strip().lower()
        if more not in ['y', 'yes']:
            break
    
    # Add workflows
    print("\n🔄 Add workflows:")
    print("   Examples: 'assistant -> user', 'researcher -> writer -> user'")
    
    while True:
        workflow = input("   Workflow (simple syntax): ").strip()
        if not workflow:
            break
        
        config["workflows"].append(workflow)
        
        # Validate current config
        result = validate_config_dict(config)
        if not result.is_valid:
            print(f"\n⚠️  Current issues: {len(result.errors)} errors")
            for error in result.errors[-2:]:  # Show last 2 errors
                print(f"   • {error}")
        
        more = input("   Add another workflow? (y/n): ").strip().lower()
        if more not in ['y', 'yes']:
            break
    
    # Final validation
    print("\n🎯 Final Validation:")
    print("-" * 30)
    
    result = validate_config_dict(config)
    print(result.get_summary())
    
    if result.is_valid:
        # Offer to save configuration
        save = input("\n💾 Save configuration to file? (y/n): ").strip().lower()
        if save in ['y', 'yes']:
            filename = input("   Filename (default: langswarm.yaml): ").strip() or "langswarm.yaml"
            
            import yaml
            try:
                with open(filename, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
                print(f"   ✅ Saved to: {filename}")
            except Exception as e:
                print(f"   ❌ Error saving: {e}")
    
    return result.is_valid


def check_examples():
    """Validate example configurations."""
    print("📚 Checking Example Configurations")
    print("=" * 40)
    
    # Find example files
    example_paths = [
        "examples/example_mcp_config",
        "docs/simplification/examples",
        "."
    ]
    
    config_files = []
    for path in example_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith(('.yaml', '.yml')) and 'langswarm' in file.lower():
                    config_files.append(os.path.join(path, file))
    
    if not config_files:
        print("⚠️  No example configuration files found")
        return True
    
    all_valid = True
    for config_file in config_files:
        print(f"\n📄 {config_file}")
        print("-" * len(config_file))
        
        is_valid = validate_file(config_file, verbose=False)
        all_valid = all_valid and is_valid
    
    print(f"\n📊 Summary: {len(config_files)} files checked")
    if all_valid:
        print("✅ All example configurations are valid!")
    else:
        print("❌ Some example configurations have issues")
    
    return all_valid


def create_sample_config():
    """Create a sample configuration file."""
    sample_config = {
        "version": "1.0",
        "project_name": "my-langswarm-project",
        "agents": [
            {
                "id": "assistant",
                "model": "gpt-4o",
                "behavior": "helpful",
                "memory": True
            },
            {
                "id": "researcher",
                "model": "gpt-4o", 
                "behavior": "research"
            }
        ],
        "memory": "production",
        "workflows": [
            "assistant -> user",
            "researcher -> assistant -> user"
        ],
        "tools": [
            {
                "id": "filesystem",
                "type": "mcpfilesystem",
                "description": "Local filesystem access",
                "local_mode": True
            }
        ]
    }
    
    import yaml
    filename = "sample-langswarm.yaml"
    
    try:
        with open(filename, 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Created sample configuration: {filename}")
        print("📝 Edit this file to customize your LangSwarm setup")
        
        # Validate the sample
        print(f"\n🔍 Validating sample configuration:")
        validate_file(filename, verbose=True)
        
        return True
    except Exception as e:
        print(f"❌ Error creating sample: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LangSwarm Configuration Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m langswarm.cli.validate langswarm.yaml     # Validate specific file
  python -m langswarm.cli.validate --interactive      # Interactive mode
  python -m langswarm.cli.validate --check-examples   # Check example configs
  python -m langswarm.cli.validate --create-sample    # Create sample config
        """
    )
    
    parser.add_argument(
        "config_file", 
        nargs="?", 
        help="Configuration file to validate"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive configuration builder"
    )
    
    parser.add_argument(
        "--check-examples", "-e",
        action="store_true", 
        help="Validate example configurations"
    )
    
    parser.add_argument(
        "--create-sample", "-s",
        action="store_true",
        help="Create a sample configuration file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output with additional checks"
    )
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.interactive:
        success = interactive_validation()
    elif args.check_examples:
        success = check_examples()
    elif args.create_sample:
        success = create_sample_config()
    elif args.config_file:
        success = validate_file(args.config_file, args.verbose)
    else:
        # No arguments - try to find and validate config in current directory
        config_files = ["langswarm.yaml", "langswarm.yml", "agents.yaml"]
        found_config = None
        
        for config_file in config_files:
            if os.path.exists(config_file):
                found_config = config_file
                break
        
        if found_config:
            print(f"🔍 Found configuration: {found_config}")
            success = validate_file(found_config, args.verbose)
        else:
            print("❌ No configuration file specified or found")
            print("💡 Usage:")
            print("   python -m langswarm.cli.validate langswarm.yaml")
            print("   python -m langswarm.cli.validate --interactive")
            print("   python -m langswarm.cli.validate --create-sample")
            parser.print_help()
            success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 