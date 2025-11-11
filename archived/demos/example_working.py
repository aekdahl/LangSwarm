#!/usr/bin/env python3
"""
LangSwarm - Complete Working Example
====================================

This example demonstrates the core LangSwarm functionality with a simple,
working agent that you can run immediately.

Requirements:
- Python 3.8+
- OpenAI API key (set as OPENAI_API_KEY environment variable)
- LangSwarm installed (pip install langswarm)

Usage:
    export OPENAI_API_KEY="your-key-here"
    python example_working.py
"""

import asyncio
import os
import sys
from typing import Optional

def check_requirements() -> bool:
    """Check if all requirements are met."""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    print("✅ OpenAI API key found")
    
    # Check LangSwarm import
    try:
        from langswarm.core.agents import create_openai_agent
        print("✅ LangSwarm imported successfully")
        return True
    except ImportError as e:
        print(f"❌ LangSwarm import failed: {e}")
        print("   Install with: pip install langswarm")
        return False

async def simple_agent_example():
    """Demonstrate basic agent creation and usage."""
    print("\n🤖 Creating OpenAI agent...")
    
    try:
        from langswarm.core.agents import create_openai_agent
        
        # Create agent with minimal configuration
        agent = create_openai_agent(
            model="gpt-3.5-turbo",  # Use cheaper model for demo
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        print("✅ Agent created successfully")
        
        # Test conversation
        print("\n💬 Starting conversation...")
        response = await agent.chat("Hello! Please introduce yourself in one sentence.")
        
        print(f"🤖 Agent: {response.content}")
        print("✅ Conversation successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent example failed: {e}")
        return False

async def builder_pattern_example():
    """Demonstrate the builder pattern for more advanced configuration."""
    print("\n🏗️ Testing builder pattern...")
    
    try:
        from langswarm.core.agents import AgentBuilder
        
        # Create agent with builder pattern
        agent = (AgentBuilder()
                .openai()
                .model("gpt-3.5-turbo")
                .system_prompt("You are a helpful assistant that always responds with enthusiasm!")
                .build())
        
        print("✅ Builder pattern agent created")
        
        # Test with custom system prompt
        response = await agent.chat("What's the weather like?")
        print(f"🤖 Enthusiastic Agent: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Builder pattern failed: {e}")
        return False

async def configuration_example():
    """Demonstrate configuration loading."""
    print("\n📋 Testing configuration system...")
    
    try:
        from langswarm.core.config import LangSwarmConfig
        
        # Create minimal configuration
        config_dict = {
            "version": "2.0",
            "agents": [
                {
                    "id": "test_agent",
                    "name": "Test Agent",
                    "provider": "openai",
                    "model": "gpt-3.5-turbo",
                    "system_prompt": "You are a test agent."
                }
            ],
            "tools": {},
            "workflows": []
        }
        
        # Load configuration
        config = LangSwarmConfig.from_dict(config_dict)
        print(f"✅ Configuration loaded: {len(config.agents)} agents")
        
        # Access agent configuration
        agent_config = config.get_agent("test_agent")
        print(f"✅ Agent config: {agent_config.name} using {agent_config.provider}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration example failed: {e}")
        return False

def print_success_summary():
    """Print success summary and next steps."""
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! LangSwarm is working correctly!")
    print("=" * 60)
    print()
    print("✅ What worked:")
    print("   • Agent creation and chat functionality")
    print("   • Builder pattern for advanced configuration")
    print("   • Configuration system loading")
    print()
    print("🚀 Next steps:")
    print("   • Read the quickstart guide: docs_v2/getting-started/quickstart/")
    print("   • Try the first project tutorial: docs_v2/getting-started/first-project/")
    print("   • Explore more examples in the documentation")
    print()
    print("📚 Documentation:")
    print("   • Main docs: docs_v2/README.md")
    print("   • User guides: docs_v2/user-guides/")
    print("   • API reference: docs_v2/api-reference/")
    print()

async def main():
    """Main function to run all examples."""
    print("🚀 LangSwarm - Complete Working Example")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements not met. Please fix the issues above and try again.")
        return
    
    print("\n✅ All requirements met! Running examples...")
    
    # Run examples
    examples = [
        ("Simple Agent", simple_agent_example),
        ("Builder Pattern", builder_pattern_example),
        ("Configuration", configuration_example)
    ]
    
    success_count = 0
    for name, example_func in examples:
        try:
            print(f"\n{'='*20} {name} {'='*20}")
            success = await example_func()
            if success:
                success_count += 1
        except Exception as e:
            print(f"❌ {name} failed with unexpected error: {e}")
    
    # Summary
    print(f"\n📊 Results: {success_count}/{len(examples)} examples successful")
    
    if success_count == len(examples):
        print_success_summary()
    else:
        print("\n⚠️ Some examples failed. Check the error messages above.")
        print("   This might indicate installation or configuration issues.")

if __name__ == "__main__":
    # Handle missing asyncio on older Python versions
    try:
        asyncio.run(main())
    except AttributeError:
        # Python 3.6 compatibility
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
