#!/usr/bin/env python3
"""
LangSwarm Zero-Config Agents Demo

This demo showcases the new zero-config agent creation capabilities in LangSwarm.
Instead of complex JSON system prompts, agents can now be created with simple behavior patterns.

Key Features Demonstrated:
1. Behavior-driven agent creation (helpful, coding, research, creative, etc.)
2. Simplified AgentFactory methods
3. Automatic tool integration based on behavior
4. Generated system prompts with JSON format instructions
5. One-line agent creation for common use cases

Run this demo to see how easy agent creation has become!
"""

import os
import sys
import json
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from langswarm.core.factory.agents import AgentFactory
from langswarm.core.config import LangSwarmConfigLoader

def print_demo_header(title: str):
    """Print a formatted demo section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_agent_info(agent, behavior: str):
    """Print agent information and generated system prompt preview"""
    print(f"\n✅ Created {behavior} agent: {agent.name}")
    print(f"   Model: {agent.model}")
    print(f"   Agent Type: {agent.agent_type}")
    
    # Show first 200 characters of system prompt
    if hasattr(agent, 'system_prompt') and agent.system_prompt:
        prompt_preview = agent.system_prompt[:200] + "..." if len(agent.system_prompt) > 200 else agent.system_prompt
        print(f"   System Prompt Preview: {prompt_preview}")
    print()

def demo_basic_zero_config_creation():
    """Demonstrate basic zero-config agent creation"""
    print_demo_header("1. Basic Zero-Config Agent Creation")
    
    print("Creating agents with simple behavior patterns...")
    
    # Create different behavior-based agents
    agents = {}
    
    # Helpful assistant (default)
    agents['helpful'] = AgentFactory.create_simple(
        name="helpful_assistant",
        behavior="helpful"
    )
    print_agent_info(agents['helpful'], "helpful")
    
    # Coding assistant
    agents['coding'] = AgentFactory.create_simple(
        name="code_helper", 
        behavior="coding",
        tools=["filesystem", "github"]
    )
    print_agent_info(agents['coding'], "coding")
    
    # Research assistant
    agents['research'] = AgentFactory.create_simple(
        name="researcher",
        behavior="research", 
        tools=["web_search", "filesystem"]
    )
    print_agent_info(agents['research'], "research")
    
    # Creative assistant
    agents['creative'] = AgentFactory.create_simple(
        name="creative_helper",
        behavior="creative"
    )
    print_agent_info(agents['creative'], "creative")
    
    return agents

def demo_specialized_factory_methods():
    """Demonstrate specialized factory methods for common use cases"""
    print_demo_header("2. Specialized Factory Methods")
    
    print("Using specialized factory methods for common use cases...")
    
    # Coding assistant with pre-configured tools
    coding_agent = AgentFactory.create_coding_assistant(
        name="dev_assistant",
        model="gpt-4o"
    )
    print(f"✅ Coding Assistant: {coding_agent.name}")
    print(f"   Pre-configured with filesystem and github tools")
    print(f"   Optimized for: Programming, debugging, code review")
    
    # Research assistant with analysis tools
    research_agent = AgentFactory.create_research_assistant(
        name="analyst", 
        model="gpt-4o"
    )
    print(f"✅ Research Assistant: {research_agent.name}")
    print(f"   Pre-configured with web_search and filesystem tools")
    print(f"   Optimized for: Information gathering, data analysis")
    
    # Support agent with interactive tools
    support_agent = AgentFactory.create_support_agent(
        name="help_desk",
        model="gpt-4o-mini"  # Cost-efficient for support
    )
    print(f"✅ Support Agent: {support_agent.name}")
    print(f"   Pre-configured with dynamic-forms and filesystem tools")
    print(f"   Optimized for: Customer service, issue resolution")
    
    # Conversational agent for natural chat
    chat_agent = AgentFactory.create_conversational_agent(
        name="chat_buddy",
        model="gpt-4o-mini"  # Fast responses for chat
    )
    print(f"✅ Conversational Agent: {chat_agent.name}")
    print(f"   Minimal tools for fast, natural dialogue")
    print(f"   Optimized for: Engaging conversations, friendly chat")
    
    return {
        'coding': coding_agent,
        'research': research_agent, 
        'support': support_agent,
        'chat': chat_agent
    }

def demo_config_based_creation():
    """Demonstrate creating agents through config loader"""
    print_demo_header("3. Config-Based Zero-Config Creation")
    
    print("Creating agents using LangSwarmConfigLoader...")
    
    config_loader = LangSwarmConfigLoader()
    
    # Show available behaviors
    behaviors = config_loader.get_available_behaviors()
    print(f"Available behaviors: {', '.join(behaviors)}")
    print()
    
    # Create agent configs programmatically
    agent_configs = []
    
    # Analytical assistant
    analytical_config = config_loader.create_simple_agent(
        agent_id="data_analyst",
        behavior="analytical",
        tools=["filesystem", "calculator"],
        model="gpt-4o"
    )
    agent_configs.append(analytical_config)
    print(f"✅ Created config for analytical agent: {analytical_config.id}")
    print(f"   Behavior: {analytical_config.behavior}")
    print(f"   Tools: {analytical_config.tools}")
    
    # Educational assistant
    educational_config = config_loader.create_simple_agent(
        agent_id="tutor",
        behavior="educational",
        tools=["filesystem", "web_search"],
        model="gpt-4o"
    )
    agent_configs.append(educational_config)
    print(f"✅ Created config for educational agent: {educational_config.id}")
    print(f"   Behavior: {educational_config.behavior}")
    print(f"   Tools: {educational_config.tools}")
    
    return agent_configs

def demo_multi_behavior_agent():
    """Demonstrate creating agents with multiple behavior patterns"""
    print_demo_header("4. Multi-Behavior Agent Creation")
    
    print("Creating agents that combine multiple behavior patterns...")
    
    config_loader = LangSwarmConfigLoader()
    
    # Create a versatile agent combining coding and research
    versatile_config = config_loader.create_multi_behavior_agent(
        agent_id="versatile_assistant",
        primary_behavior="coding",
        secondary_behaviors=["research", "analytical"],
        tools=["filesystem", "github", "web_search", "calculator"],
        model="gpt-4o"
    )
    
    print(f"✅ Created multi-behavior agent: {versatile_config.id}")
    print(f"   Primary behavior: {versatile_config.behavior}")
    print(f"   Combined capabilities: coding + research + analytical")
    print(f"   Tools: {versatile_config.tools}")
    print(f"   System prompt includes all behavior aspects")
    
    return versatile_config

def demo_behavior_comparison():
    """Demonstrate the differences between behavior patterns"""
    print_demo_header("5. Behavior Pattern Comparison")
    
    print("Comparing system prompts generated for different behaviors...")
    
    config_loader = LangSwarmConfigLoader()
    
    behaviors_to_compare = ["helpful", "coding", "research", "creative"]
    
    for behavior in behaviors_to_compare:
        # Generate a system prompt for this behavior
        sample_prompt = config_loader._generate_behavior_prompt(behavior, ["filesystem"])
        
        # Show first 150 characters to compare personalities
        preview = sample_prompt.split('\n')[0][:150] + "..."
        
        print(f"\n🎭 {behavior.title()} Behavior:")
        print(f"   Personality: {preview}")
        
        # Show tool instructions presence
        if "## Available Tools" in sample_prompt:
            print(f"   ✅ Includes comprehensive tool instructions")
        if "## Response Format" in sample_prompt:
            print(f"   ✅ Includes JSON format instructions")

def demo_yaml_config_generation():
    """Demonstrate generating YAML config with zero-config agents"""
    print_demo_header("6. YAML Configuration Generation")
    
    print("Generating langswarm.yaml with zero-config agents...")
    
    # Create a sample unified config using zero-config agents
    sample_config = {
        "version": "1.0",
        "project_name": "Zero-Config Demo",
        "agents": [
            {
                "id": "helpful_bot",
                "behavior": "helpful",
                "model": "gpt-4o-mini",
                "tools": ["filesystem"]
            },
            {
                "id": "code_assistant", 
                "behavior": "coding",
                "model": "gpt-4o",
                "tools": ["filesystem", "github"]
            },
            {
                "id": "research_bot",
                "behavior": "research", 
                "model": "gpt-4o",
                "tools": ["web_search", "filesystem"]
            },
            {
                "id": "support_agent",
                "behavior": "support",
                "model": "gpt-4o-mini", 
                "tools": ["dynamic-forms", "filesystem"]
            }
        ],
        "tools": {
            "filesystem": {"type": "mcp-filesystem", "local_mode": True},
            "github": {"type": "mcp-github", "settings": {"token": "env:GITHUB_TOKEN"}},
            "web_search": {"type": "web-search"},
            "dynamic-forms": {"type": "mcp-dynamic-forms"}
        }
    }
    
    print("Sample langswarm.yaml with zero-config agents:")
    print("```yaml")
    
    # Print formatted YAML-like structure
    import yaml
    yaml_output = yaml.dump(sample_config, default_flow_style=False, indent=2)
    print(yaml_output)
    print("```")
    
    print("\n✨ Key Benefits:")
    print("   • No complex system_prompt fields needed")
    print("   • Behavior field automatically generates appropriate prompts")
    print("   • Tools are automatically documented in generated prompts")
    print("   • JSON format instructions included automatically")
    print("   • Consistent behavior across all agents")

def demo_before_after_comparison():
    """Show before/after comparison of agent creation complexity"""
    print_demo_header("7. Before vs After Comparison")
    
    print("BEFORE - Complex manual configuration:")
    print("```python")
    print("""# Old way - complex and error-prone
agent = AgentWrapper(
    name="coding_assistant",
    agent=openai_client,
    model="gpt-4o",
    system_prompt=\"\"\"You are a coding assistant. Help with programming tasks, 
    code review, debugging, and technical questions. You must respond in JSON format:
    {
      "response": "Your message",
      "mcp": {"tool": "name", "method": "method", "params": {}}
    }
    Available tools:
    - filesystem: read files and list directories
    - github: interact with repositories
    \"\"\",
    agent_type="generic",
    memory=None,
    # ... 15+ more parameters
)""")
    print("```")
    
    print("\nAFTER - Simple zero-config creation:")
    print("```python")
    print("""# New way - simple and intuitive
agent = AgentFactory.create_coding_assistant(
    name="coding_assistant"
)

# Or even simpler:
agent = AgentFactory.create_simple(
    name="coding_assistant",
    behavior="coding",
    tools=["filesystem", "github"]
)""")
    print("```")
    
    print("\n📊 Improvement Metrics:")
    print("   • Lines of code: 15+ → 3 (80% reduction)")
    print("   • Configuration complexity: High → Low")
    print("   • Error potential: High → Minimal")
    print("   • Maintenance burden: High → Low")
    print("   • New user learning curve: Steep → Gentle")

def main():
    """Run the complete zero-config agents demo"""
    print("🚀 LangSwarm Zero-Config Agents Demo")
    print("=====================================")
    print("Demonstrating simplified agent creation with behavior-driven prompts")
    
    try:
        # Run all demo sections
        agents_basic = demo_basic_zero_config_creation()
        agents_specialized = demo_specialized_factory_methods()
        agent_configs = demo_config_based_creation()
        multi_behavior_config = demo_multi_behavior_agent()
        demo_behavior_comparison()
        demo_yaml_config_generation()
        demo_before_after_comparison()
        
        # Summary
        print_demo_header("🎉 Demo Complete - Zero-Config Agents Summary")
        
        total_agents = len(agents_basic) + len(agents_specialized)
        print(f"✅ Successfully created {total_agents} agents with zero-config approach")
        print("✅ All agents have behavior-driven system prompts")
        print("✅ JSON format instructions automatically included")
        print("✅ Tool-specific guidance automatically generated")
        print("✅ Ready for production use with simplified configuration")
        
        print("\n🎯 Key Benefits Achieved:")
        print("   • 80% reduction in configuration complexity")
        print("   • Eliminated manual JSON prompt engineering")
        print("   • Consistent behavior patterns across agents")
        print("   • Automatic tool integration and documentation")
        print("   • One-line agent creation for common use cases")
        print("   • Easy customization while maintaining simplicity")
        
        print("\n📚 Next Steps:")
        print("   1. Try creating your own agents with different behaviors")
        print("   2. Experiment with tool combinations")
        print("   3. Use the simplified YAML configuration format")
        print("   4. Explore multi-behavior agent patterns")
        print("   5. Check out the generated system prompts for insights")
        
        print(f"\n🏁 Zero-Config Agents demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 