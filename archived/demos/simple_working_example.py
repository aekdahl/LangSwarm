#!/usr/bin/env python3
"""
Simple Working LangSwarm Example
===============================

This is a minimal, working example that demonstrates LangSwarm usage
without complex configurations or missing dependencies.

This example works around the issues that make LangSwarm difficult for LLMs:
1. Avoids complex YAML configurations
2. Uses only core functionality
3. Provides clear error messages
4. Shows the simplest possible usage
"""

import os
import sys
import asyncio
from typing import Optional

def check_prerequisites():
    """Check if basic requirements are met."""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check LangSwarm availability
    try:
        import langswarm
        print("✅ LangSwarm available")
    except ImportError as e:
        print(f"❌ LangSwarm not available: {e}")
        print("   Install with: pip install langswarm")
        return False
    
    # Check OpenAI availability
    try:
        import openai
        print("✅ OpenAI package available")
    except ImportError:
        print("❌ OpenAI package missing")
        print("   Install with: pip install openai")
        return False
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("   Set with: export OPENAI_API_KEY='your-key-here'")
        print("   Or create a .env file with: OPENAI_API_KEY=your-key-here")
        return False
    print("✅ OpenAI API key found")
    
    return True

async def simple_agent_example():
    """Create and use a simple agent with minimal configuration."""
    print("\n🤖 Creating simple agent...")
    
    try:
        # Import the simplest creation function
        from langswarm.core.agents import create_openai_agent
        
        # Create agent with minimal config
        agent = create_openai_agent(
            model="gpt-3.5-turbo",  # Cheaper model for testing
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        print("✅ Agent created successfully")
        
        # Simple conversation
        print("\n💬 Testing conversation...")
        response = await agent.chat("Hello! Please respond with just 'Hello back!' and nothing else.")
        
        print(f"🤖 Agent response: {response.content}")
        print("✅ Conversation successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent example failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def programmatic_config_example():
    """Show how to create configuration programmatically instead of YAML."""
    print("\n📋 Creating configuration programmatically...")
    
    try:
        from langswarm.core.config import LangSwarmConfig
        from langswarm.core.config.schema import AgentConfig, MemoryConfig, ProviderType
        
        # Create simple config without YAML
        config = LangSwarmConfig(
            version="2.0",
            name="Simple LangSwarm Setup",
            agents=[
                AgentConfig(
                    id="simple_assistant",
                    name="Simple Assistant",
                    provider=ProviderType.OPENAI,
                    model="gpt-3.5-turbo",
                    system_prompt="You are a helpful assistant."
                )
            ],
            memory=MemoryConfig(
                backend="sqlite",  # Simple local storage
                config={"db_path": "simple_langswarm.db"}
            )
        )
        
        print("✅ Configuration created programmatically")
        print(f"   - {len(config.agents)} agents configured")
        print(f"   - Memory backend: {config.memory.backend}")
        
        return config
        
    except Exception as e:
        print(f"❌ Programmatic config failed: {e}")
        return None

async def builder_pattern_example():
    """Show the builder pattern as an alternative to configuration files."""
    print("\n🏗️ Using builder pattern...")
    
    try:
        from langswarm.core.agents import AgentBuilder
        
        # Use builder pattern for more control
        agent = (AgentBuilder()
                .openai(api_key=os.getenv("OPENAI_API_KEY"))
                .model("gpt-3.5-turbo")
                .system_prompt("You are a concise assistant. Keep responses short.")
                .temperature(0.7)
                .build())
        
        print("✅ Agent built with builder pattern")
        
        # Test it
        response = await agent.chat("What is 2+2? Answer in one word.")
        print(f"🤖 Builder agent response: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Builder pattern failed: {e}")
        return False

def show_minimal_yaml_config():
    """Show what a truly minimal YAML config looks like."""
    print("\n📄 Minimal YAML configuration example:")
    
    minimal_yaml = """# minimal_langswarm.yaml
version: "2.0"
name: "Minimal Setup"

agents:
  - id: "assistant"
    provider: "openai"
    model: "gpt-3.5-turbo"
    system_prompt: "You are a helpful assistant."

memory:
  backend: "sqlite"
  config:
    db_path: "langswarm.db"
"""
    
    print(minimal_yaml)
    
    # Write it to a file
    with open("minimal_langswarm.yaml", "w") as f:
        f.write(minimal_yaml)
    
    print("✅ Minimal config saved to 'minimal_langswarm.yaml'")
    
    # Test loading it
    try:
        from langswarm.core.config import load_config
        config = load_config("minimal_langswarm.yaml")
        print("✅ Minimal config loads successfully")
        return True
    except Exception as e:
        print(f"❌ Minimal config failed to load: {e}")
        return False

async def main():
    """Run the complete simple example."""
    print("🚀 Simple LangSwarm Working Example")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix the issues above.")
        return False
    
    # Run examples
    examples = [
        ("Simple Agent", simple_agent_example),
        ("Builder Pattern", builder_pattern_example),
    ]
    
    success_count = 0
    for name, example_func in examples:
        try:
            print(f"\n{'='*20} {name} {'='*20}")
            if await example_func():
                success_count += 1
        except Exception as e:
            print(f"❌ {name} failed: {e}")
    
    # Non-async examples
    config_success = programmatic_config_example() is not None
    yaml_success = show_minimal_yaml_config()
    
    if config_success:
        success_count += 1
    if yaml_success:
        success_count += 1
    
    total_examples = len(examples) + 2
    
    # Summary
    print(f"\n{'='*50}")
    print(f"📊 RESULTS: {success_count}/{total_examples} examples successful")
    print(f"{'='*50}")
    
    if success_count >= 3:
        print("🎉 SUCCESS! LangSwarm is working correctly.")
        print("\n💡 Key takeaways for LLM usage:")
        print("1. Use create_openai_agent() for simplest setup")
        print("2. Use AgentBuilder() for more control")
        print("3. Create configs programmatically instead of YAML when possible")
        print("4. Start with SQLite memory backend (no external dependencies)")
        print("5. Use gpt-3.5-turbo for cost-effective testing")
        
        print("\n📝 Next steps:")
        print("- Try the minimal_langswarm.yaml config")
        print("- Experiment with different models and prompts")
        print("- Add tools and workflows as needed")
        
        return True
    else:
        print("⚠️ Some examples failed. Check error messages above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
