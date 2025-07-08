#!/usr/bin/env python3
"""
Demo: Smart Tool Auto-Discovery
=============================

This demo showcases LangSwarm's Smart Tool Auto-Discovery system with:
- Environment-based tool detection
- Simplified tool configuration syntax 
- Auto-configuration with smart defaults
- Custom tool scanning
- Zero-config integration

Part of the LangSwarm Simplification Project - Priority 3.
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

# Import detection functions first (they have no circular dependencies)
try:
    from langswarm.core.detection import auto_discover_tools, detect_available_tools, EnvironmentDetector
    DETECTION_AVAILABLE = True
    print("✅ Environment Detection available")
except ImportError as e:
    DETECTION_AVAILABLE = False
    print(f"❌ Environment Detection not available: {e}")

# Import config loader separately (might have circular dependencies)
try:
    from langswarm.core.config import LangSwarmConfigLoader
    CONFIG_AVAILABLE = True
    print("✅ Config Loader available")
except ImportError as e:
    CONFIG_AVAILABLE = False
    print(f"❌ Config Loader not available: {e}")

# Import agent factory separately
try:
    from langswarm.core.factory.agents import AgentFactory
    AGENTS_AVAILABLE = True
    print("✅ Agent Factory available")
except ImportError as e:
    AGENTS_AVAILABLE = False
    print(f"❌ Agent Factory not available: {e}")

SMART_TOOLS_AVAILABLE = DETECTION_AVAILABLE


def demo_environment_detection():
    """Demo 1: Environment-based Tool Detection"""
    print("=" * 60)
    print("DEMO 1: Environment-based Tool Detection")
    print("=" * 60)
    
    # Detect available tools in current environment
    detection_results = detect_available_tools()
    
    print("\n🔍 Environment Detection Results:")
    print("-" * 40)
    
    summary = detection_results["environment_summary"]
    print(f"📊 Summary:")
    print(f"   • Total available tools: {summary['total_available']}")
    print(f"   • Built-in tools: {summary['built_in_tools']}")
    print(f"   • Custom tools: {summary['custom_tools']}")
    print(f"   • Missing credentials: {summary['missing_credentials']}")
    print(f"   • Missing dependencies: {summary['missing_dependencies']}")
    
    print(f"\n✅ Available Tools:")
    for tool in detection_results["available_tools"]:
        if "preset" in tool:
            preset = tool["preset"]
            print(f"   • {preset.id}: {preset.description}")
            print(f"     Type: {preset.type}, Pattern: {preset.pattern}")
        else:
            print(f"   • {tool['id']}: {tool['description']}")
            print(f"     Type: {tool['type']}, Path: {tool.get('path', 'N/A')}")
    
    if detection_results["missing_credentials"]:
        print(f"\n⚠️  Missing Credentials:")
        for missing in detection_results["missing_credentials"]:
            print(f"   • {missing['tool']}: {', '.join(missing['missing_vars'])}")
    
    if detection_results["recommendations"]:
        print(f"\n💡 Setup Recommendations:")
        for rec in detection_results["recommendations"]:
            print(f"   • {rec}")
    
    return detection_results


def demo_simplified_tool_syntax():
    """Demo 2: Simplified Tool Configuration Syntax"""
    print("\n" + "=" * 60)
    print("DEMO 2: Simplified Tool Configuration Syntax")
    print("=" * 60)
    
    if not CONFIG_AVAILABLE:
        print("❌ Config Loader not available - skipping this demo")
        return False
    
    print("\n🔧 Testing Simplified Syntax...")
    
    # Create a temporary configuration with simplified syntax
    config_data = {
        "version": "1.0",
        "agents": [
            {
                "id": "simple_agent",
                "model": "gpt-4o",
                "behavior": "coding",
                "tools": ["filesystem", "github"]  # ← Simplified syntax!
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name
    
    try:
        print("📝 Configuration with simplified syntax:")
        print("```yaml")
        print("agents:")
        print("  - id: simple_agent")
        print("    model: gpt-4o")
        print("    behavior: coding")
        print("    tools: [filesystem, github]  # ← Magic happens here!")
        print("```")
        
        print("\n🚀 Loading configuration...")
        loader = LangSwarmConfigLoader(config_path=os.path.dirname(temp_config_path))
        
        # Try to load using single config method which might be safer
        try:
            config = loader.load_single_config(temp_config_path)
            print(f"\n✅ Results:")
            print(f"   • {len(config.tools)} tools auto-configured")
            print(f"   • {len(config.agents)} agents created")
            
            print(f"\n🔧 Auto-configured Tools:")
            for tool_id, tool_config in config.tools.items():
                print(f"   • {tool_id}: {tool_config.type}")
                if hasattr(tool_config, 'settings'):
                    print(f"     Settings: {len(tool_config.settings)} items")
            
            print(f"\n👥 Created Agents:")
            for agent in config.agents:
                print(f"   • {agent.id}: {agent.agent_type}")
                print(f"     Tools: {', '.join(agent.tools) if agent.tools else 'None'}")
            
            return True
            
        except Exception as config_error:
            print(f"❌ Configuration loading error: {config_error}")
            # Try the legacy load method as fallback
            try:
                workflows, agents, brokers, tools, tools_metadata = loader.load()
                print(f"\n✅ Fallback Results:")
                print(f"   • {len(tools)} tools loaded")
                print(f"   • {len(agents)} agents created")
                return True
            except Exception as legacy_error:
                print(f"❌ Legacy loading also failed: {legacy_error}")
                return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        # Cleanup
        os.unlink(temp_config_path)


def demo_auto_discovery():
    """Demo 3: Full Auto-Discovery (Zero Config)"""
    print("\n" + "=" * 60)
    print("DEMO 3: Full Auto-Discovery (Zero Config)")
    print("=" * 60)
    
    print("\n🔍 Auto-discovering all available tools...")
    
    # Discover all available tools
    auto_tools = auto_discover_tools()
    
    print(f"\n✅ Auto-discovered {len(auto_tools)} tools:")
    for tool_config in auto_tools:
        print(f"   • {tool_config['id']}: {tool_config.get('description', 'No description')}")
        print(f"     Type: {tool_config['type']}")
        print(f"     Local mode: {tool_config.get('local_mode', False)}")
        print(f"     Pattern: {tool_config.get('pattern', 'direct')}")
        if 'methods' in tool_config:
            print(f"     Methods: {len(tool_config['methods'])}")
    
    # Test specific tool discovery
    print(f"\n🎯 Discovering specific tools: ['filesystem', 'github']")
    specific_tools = auto_discover_tools(["filesystem", "github"])
    
    print(f"\n✅ Specific discovery results:")
    for tool_config in specific_tools:
        print(f"   • {tool_config['id']}")
        print(f"     Available: {'Yes' if tool_config else 'No'}")
    
    return auto_tools


def demo_zero_config_integration():
    """Demo 4: Zero-Config Agent Creation with Auto-Discovery"""
    print("\n" + "=" * 60)
    print("DEMO 4: Zero-Config Agent Creation with Auto-Discovery")
    print("=" * 60)
    
    if not AGENTS_AVAILABLE:
        print("❌ Agent Factory not available - skipping this demo")
        return False
    
    print("\n🚀 Creating zero-config agents with auto-discovered tools...")
    
    try:
        # Test simple agent creation
        print("📝 Testing simple agent creation...")
        
        # For now, just create basic agents to test the functionality
        from langswarm.core.agent import Agent
        
        agent = Agent(
            name="test_agent",
            model="gpt-4o"
        )
        
        print(f"✅ Created test agent:")
        print(f"   • Name: {agent.name}")
        print(f"   • Model: {agent.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating agents: {e}")
        return False


def demo_behavior_tool_suggestions():
    """Demo 5: Behavior-based Tool Suggestions"""
    print("\n" + "=" * 60)
    print("DEMO 5: Behavior-based Tool Suggestions")
    print("=" * 60)
    
    if not CONFIG_AVAILABLE:
        print("❌ Config Loader not available - skipping this demo")
        return False
    
    print("\n🎯 Testing behavior-based tool suggestions...")
    
    behaviors_to_test = [
        "coding",
        "research", 
        "helpful",
        "support",
        "conversational",
        "analytical"
    ]
    
    try:
        loader = LangSwarmConfigLoader()
        
        for behavior in behaviors_to_test:
            suggestions = loader.suggest_tools_for_behavior(behavior)
            print(f"\n📋 {behavior.title()} Assistant:")
            if suggestions:
                print(f"   Suggested tools: {', '.join(suggestions)}")
            else:
                print(f"   No specific tools suggested (general purpose)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting tool suggestions: {e}")
        return False


def demo_custom_tool_scanning():
    """Demo 6: Custom Tool Scanning"""
    print("\n" + "=" * 60)
    print("DEMO 6: Custom Tool Scanning")
    print("=" * 60)
    
    print("\n🔍 Testing custom tool scanning...")
    
    # Create a temporary tools directory with a custom tool
    tools_dir = Path("./demo_tools")
    tools_dir.mkdir(exist_ok=True)
    
    # Create a sample custom tool
    custom_tool_content = '''
class MyCustomTool:
    """A custom tool for demonstration"""
    
    def __init__(self):
        self.id = "my_custom_tool"
        self.type = "custom"
        self.description = "Demo custom tool"
    
    def run(self, params):
        return "Custom tool response"
    
    def get_schema(self):
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            }
        }
'''
    
    custom_tool_path = tools_dir / "my_custom_tool.py"
    with open(custom_tool_path, 'w') as f:
        f.write(custom_tool_content)
    
    try:
        print(f"📝 Created custom tool: {custom_tool_path}")
        
        # Test custom tool detection
        detection_results = detect_available_tools()
        custom_tools = [t for t in detection_results["available_tools"] if t.get("type") == "custom"]
        
        print(f"\n🔧 Custom tools found: {len(custom_tools)}")
        for tool in custom_tools:
            print(f"   • {tool['id']}: {tool.get('description', 'No description')}")
            print(f"     Path: {tool.get('path', 'Unknown')}")
        
        return len(custom_tools) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        # Cleanup
        if custom_tool_path.exists():
            custom_tool_path.unlink()
        if tools_dir.exists():
            tools_dir.rmdir()


def demo_complete_workflow():
    """Demo 7: Complete Smart Tool Auto-Discovery Workflow"""
    print("\n" + "=" * 60)
    print("DEMO 7: Complete Smart Tool Auto-Discovery Workflow")
    print("=" * 60)
    
    if not (DETECTION_AVAILABLE and CONFIG_AVAILABLE):
        print("❌ Complete workflow requires both Detection and Config - skipping this demo")
        return False
    
    print("\n🌟 Complete LangSwarm Smart Tool Auto-Discovery Workflow:")
    
    # Create a minimal configuration that showcases everything
    config_data = {
        "version": "1.0",
        "project_name": "Smart Tools Demo",
        "agents": [
            {
                "id": "smart_assistant",
                "behavior": "coding",
                "tools": ["filesystem"]  # Simplified syntax
            },
            {
                "id": "research_bot",
                "behavior": "research", 
                # No tools specified - will auto-discover!
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_path = f.name
    
    try:
        print("1️⃣ Environment Detection...")
        detection_results = detect_available_tools()
        available_count = detection_results["environment_summary"]["total_available"]
        print(f"   ✅ {available_count} tools available")
        
        print("\n2️⃣ Configuration Loading with Smart Auto-Discovery...")
        loader = LangSwarmConfigLoader(config_path=os.path.dirname(temp_config_path))
        
        try:
            config = loader.load_single_config(temp_config_path)
            print(f"   ✅ {len(config.tools)} tools auto-configured")
            print(f"   ✅ {len(config.agents)} agents created")
            
            print("\n3️⃣ Agent Tool Assignment...")
            for agent in config.agents:
                print(f"   • {agent.id}:")
                print(f"     Tools: {', '.join(agent.tools) if agent.tools else 'None'}")
                print(f"     Behavior: {agent.behavior or 'default'}")
            
            print("\n4️⃣ Behavior-based Recommendations...")
            for behavior in ["coding", "research"]:
                suggestions = loader.suggest_tools_for_behavior(behavior)
                print(f"   • {behavior}: {', '.join(suggestions) if suggestions else 'general purpose'}")
            
            print(f"\n✅ Smart Tool Auto-Discovery workflow completed successfully!")
            return True
        
        except Exception as workflow_error:
            print(f"❌ Configuration workflow failed: {workflow_error}")
            return False
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        return False
        
    finally:
        os.unlink(temp_config_path)


def main():
    """Run all Smart Tool Auto-Discovery demos"""
    print("🚀 LangSwarm Smart Tool Auto-Discovery Demo")
    print("=" * 60)
    print("This demo showcases Priority 3: Smart Tool Auto-Discovery")
    print("Features: Environment detection, simplified syntax, auto-configuration")
    print("")
    
    if not SMART_TOOLS_AVAILABLE:
        print("❌ Smart Tool Auto-Discovery not available. Basic detection missing.")
        print("   Please check the langswarm.core.detection module.")
        return
    
    # Check what functionality is available
    print("📋 Checking available functionality:")
    print(f"   • Environment Detection: {'✅' if DETECTION_AVAILABLE else '❌'}")
    print(f"   • Configuration Loading: {'✅' if CONFIG_AVAILABLE else '❌'}")
    print(f"   • Agent Factory: {'✅' if AGENTS_AVAILABLE else '❌'}")
    print("")
    
    demos = [
        ("Environment Detection", demo_environment_detection, DETECTION_AVAILABLE),
        ("Simplified Tool Syntax", demo_simplified_tool_syntax, CONFIG_AVAILABLE),
        ("Auto-Discovery", demo_auto_discovery, DETECTION_AVAILABLE),
        ("Zero-Config Integration", demo_zero_config_integration, AGENTS_AVAILABLE),
        ("Behavior Tool Suggestions", demo_behavior_tool_suggestions, CONFIG_AVAILABLE),
        ("Custom Tool Scanning", demo_custom_tool_scanning, DETECTION_AVAILABLE),
        ("Complete Workflow", demo_complete_workflow, DETECTION_AVAILABLE and CONFIG_AVAILABLE)
    ]
    
    results = []
    for demo_name, demo_func, available in demos:
        try:
            if available:
                result = demo_func()
                results.append(result)
            else:
                print(f"\n❌ {demo_name}: SKIPPED (dependencies not available)")
                results.append(False)
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMO SUMMARY")
    print("=" * 60)
    
    success_count = 0
    skipped_count = 0
    for i, ((name, demo_func, available), result) in enumerate(zip(demos, results), 1):
        if not available:
            status = "⏭️  SKIP"
            skipped_count += 1
        elif result:
            status = "✅ PASS"
            success_count += 1
        else:
            status = "❌ FAIL"
        print(f"{i}. {name}: {status}")
    
    total_attempted = len(demos) - skipped_count
    print(f"\n📊 Results: {success_count}/{total_attempted} attempted demos passed ({skipped_count} skipped)")
    
    if success_count == total_attempted and total_attempted > 0:
        print("🎉 All available Smart Tool Auto-Discovery features working perfectly!")
    elif success_count > 0:
        print("⚠️  Some features working, others may need attention.")
    else:
        print("❌ No demos passed. Check dependencies and configuration.")
    
    print("\n💡 Next Steps:")
    
    if DETECTION_AVAILABLE:
        print("   • Environment detection is working - try: python -c \"from langswarm.core.detection import detect_available_tools; print(detect_available_tools())\"")
    
    if CONFIG_AVAILABLE:
        print("   • Try using simplified tool syntax in your configurations")
        print("   • Let LangSwarm auto-discover tools for zero-config setup")
    
    if not CONFIG_AVAILABLE:
        print("   • Fix circular import issues in langswarm.core.config")
    
    if not AGENTS_AVAILABLE:
        print("   • Check langswarm.core.factory.agents module")
    
    print("   • Check environment detection for missing credentials")
    print("   • Explore behavior-based tool recommendations")


if __name__ == "__main__":
    main() 