#!/usr/bin/env python3
"""
LangSwarm configuration initializer - creates configs interactively.
"""

import os
import yaml
from typing import Dict, Any, List
from pathlib import Path


class ConfigWizard:
    """Interactive configuration creator."""
    
    TEMPLATES = {
        "minimal": {
            "name": "Minimal (Just the basics)",
            "description": "Simplest possible configuration",
            "agents": 1,
            "complexity": "beginner"
        },
        "chatbot": {
            "name": "Chatbot",
            "description": "Conversational AI assistant", 
            "agents": 1,
            "complexity": "beginner"
        },
        "customer-support": {
            "name": "Customer Support",
            "description": "Multi-agent support system with routing",
            "agents": 3,
            "complexity": "intermediate"
        },
        "content-pipeline": {
            "name": "Content Creation",
            "description": "Research → Write → Edit pipeline",
            "agents": 3,
            "complexity": "intermediate"
        },
        "code-assistant": {
            "name": "Code Assistant", 
            "description": "AI pair programmer with file access",
            "agents": 1,
            "complexity": "intermediate"
        },
        "custom": {
            "name": "Custom Configuration",
            "description": "Build your own from scratch",
            "agents": 0,
            "complexity": "any"
        }
    }
    
    def run(self):
        """Run the configuration wizard."""
        print("🚀 LangSwarm Configuration Wizard")
        print("=" * 40)
        print("Let's create your configuration!\n")
        
        # Choose template or custom
        template = self._choose_template()
        
        if template == "custom":
            config = self._build_custom_config()
        else:
            config = self._load_template(template)
            config = self._customize_template(config, template)
        
        # Choose filename
        filename = self._choose_filename()
        
        # Save configuration
        self._save_config(config, filename)
        
        print(f"\n✅ Configuration saved to: {filename}")
        print("\n🎯 Next steps:")
        print(f"   1. Set your API key: export OPENAI_API_KEY='your-key'")
        print(f"   2. Run your config: python -m langswarm.run {filename}")
        print(f"   3. Check templates/ for more examples")
    
    def _choose_template(self) -> str:
        """Let user choose a template."""
        print("📝 Choose a starting point:\n")
        
        options = []
        for key, info in self.TEMPLATES.items():
            options.append(key)
            agents_text = f"{info['agents']} agent{'s' if info['agents'] != 1 else ''}" if info['agents'] > 0 else "flexible"
            print(f"  {len(options)}. {info['name']} - {info['description']}")
            print(f"     ({agents_text}, {info['complexity']})")
            print()
        
        while True:
            try:
                choice = input("Enter your choice (1-6): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(options):
                    return options[index]
            except ValueError:
                pass
            print("Please enter a number between 1 and 6")
    
    def _build_custom_config(self) -> Dict[str, Any]:
        """Build a custom configuration interactively."""
        config = {"version": "2.0", "agents": [], "workflows": []}
        
        print("\n🤖 Let's configure your agents:")
        
        # Add agents
        agent_count = self._get_number("How many agents do you need?", 1, 10, 1)
        
        for i in range(agent_count):
            print(f"\n📋 Agent {i + 1}:")
            agent = {}
            
            # Agent ID
            default_id = f"agent{i + 1}" if i > 0 else "assistant"
            agent["id"] = input(f"   ID [{default_id}]: ").strip() or default_id
            
            # Model selection
            print("   Model options:")
            print("     1. gpt-3.5-turbo (fast & cheap)")
            print("     2. gpt-4 (best quality)")
            print("     3. claude-3-sonnet (balanced)")
            print("     4. custom")
            
            model_choice = input("   Choose model [1]: ").strip() or "1"
            model_map = {
                "1": "gpt-3.5-turbo",
                "2": "gpt-4", 
                "3": "claude-3-sonnet"
            }
            
            if model_choice in model_map:
                agent["model"] = model_map[model_choice]
            else:
                agent["model"] = input("   Enter model name: ").strip()
            
            # System prompt
            print("   System prompt (press Enter twice when done):")
            lines = []
            while True:
                line = input("   > ")
                if not line and lines:
                    break
                lines.append(line)
            
            if lines:
                agent["system_prompt"] = "\n".join(lines)
            
            config["agents"].append(agent)
        
        # Add workflow if multiple agents
        if len(config["agents"]) > 1:
            print("\n🔄 Workflow configuration:")
            print("   Examples:")
            print("   - Linear: agent1 -> agent2 -> user")
            print("   - Conditional: classifier -> (option1 | option2) -> user")
            print("   - Parallel: agent1, agent2 -> aggregator -> user")
            
            workflow = input("\n   Enter workflow [agent1 -> user]: ").strip()
            if workflow:
                config["workflows"].append(workflow)
        elif config["agents"]:
            # Single agent default workflow
            config["workflows"].append(f"{config['agents'][0]['id']} -> user")
        
        return config
    
    def _load_template(self, template_name: str) -> Dict[str, Any]:
        """Load a template configuration."""
        template_path = Path(__file__).parent.parent.parent / "templates" / f"{template_name}.yaml"
        
        if template_path.exists():
            with open(template_path) as f:
                return yaml.safe_load(f)
        else:
            # Fallback to basic template
            return {
                "version": "2.0",
                "agents": [{
                    "id": "assistant",
                    "model": "gpt-3.5-turbo",
                    "system_prompt": "You are a helpful AI assistant."
                }]
            }
    
    def _customize_template(self, config: Dict[str, Any], template_name: str) -> Dict[str, Any]:
        """Allow customization of loaded template."""
        print(f"\n✏️  Customize your {self.TEMPLATES[template_name]['name']} configuration:")
        
        # Optionally change model
        print("\n🧠 Model Selection:")
        print("   Current models:")
        for agent in config.get("agents", []):
            print(f"   - {agent['id']}: {agent.get('model', 'not set')}")
        
        if input("\n   Change models? (y/N): ").strip().lower() == 'y':
            for agent in config.get("agents", []):
                print(f"\n   {agent['id']} model options:")
                print("     1. Keep current (" + agent.get('model', 'gpt-3.5-turbo') + ")")
                print("     2. gpt-3.5-turbo (fast & cheap)")
                print("     3. gpt-4 (best quality)")
                print("     4. claude-3-sonnet (balanced)")
                
                choice = input("   Choice [1]: ").strip() or "1"
                if choice == "2":
                    agent["model"] = "gpt-3.5-turbo"
                elif choice == "3":
                    agent["model"] = "gpt-4"
                elif choice == "4":
                    agent["model"] = "claude-3-sonnet"
        
        # Memory backend
        print("\n💾 Memory Backend:")
        print("   1. SQLite (default, local)")
        print("   2. Redis (faster, requires server)")
        print("   3. In-memory only (no persistence)")
        
        memory_choice = input("   Choice [1]: ").strip() or "1"
        if memory_choice == "2":
            config["memory"] = {"backend": "redis"}
        elif memory_choice == "3":
            config["memory"] = {"backend": "memory"}
        
        # Add tools
        if template_name in ["code-assistant", "custom"]:
            print("\n🔧 Available Tools:")
            print("   1. filesystem - Read/write files")
            print("   2. web_search - Search the internet")
            print("   3. code_executor - Run code snippets")
            print("   4. None")
            
            tool_choice = input("   Add tools (comma-separated numbers) [4]: ").strip() or "4"
            if tool_choice != "4":
                tools = []
                if "1" in tool_choice:
                    tools.append("filesystem")
                if "2" in tool_choice:
                    tools.append("web_search")
                if "3" in tool_choice:
                    tools.append("code_executor")
                
                if tools and config.get("agents"):
                    config["agents"][0]["tools"] = tools
        
        return config
    
    def _choose_filename(self) -> str:
        """Let user choose output filename."""
        default = "langswarm.yaml"
        filename = input(f"\n📄 Configuration filename [{default}]: ").strip() or default
        
        # Ensure .yaml extension
        if not filename.endswith(('.yaml', '.yml')):
            filename += '.yaml'
        
        # Warn if file exists
        if os.path.exists(filename):
            if input(f"\n⚠️  {filename} already exists. Overwrite? (y/N): ").strip().lower() != 'y':
                filename = input("   New filename: ").strip()
                if not filename.endswith(('.yaml', '.yml')):
                    filename += '.yaml'
        
        return filename
    
    def _save_config(self, config: Dict[str, Any], filename: str):
        """Save configuration to file."""
        with open(filename, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def _get_number(self, prompt: str, min_val: int, max_val: int, default: int) -> int:
        """Get a number from user with validation."""
        while True:
            try:
                value = input(f"{prompt} [{default}]: ").strip() or str(default)
                num = int(value)
                if min_val <= num <= max_val:
                    return num
                print(f"Please enter a number between {min_val} and {max_val}")
            except ValueError:
                print("Please enter a valid number")


def main():
    """Run the configuration wizard."""
    wizard = ConfigWizard()
    wizard.run()


if __name__ == "__main__":
    main()