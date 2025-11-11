#!/usr/bin/env python3
"""
LLM-Friendly LangSwarm Setup
===========================

This is the recommended way for LLMs to use LangSwarm.
It follows all the best practices identified in the analysis.

Usage:
    export OPENAI_API_KEY="your-key-here"
    python llm_friendly_setup.py
"""

import asyncio
import os
import sys

def validate_environment():
    """Validate that the environment is ready for LangSwarm."""
    print("🔍 Validating environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check LangSwarm installation
    try:
        import langswarm
        print("✅ LangSwarm installed")
    except ImportError:
        print("❌ LangSwarm not installed. Run: pip install langswarm")
        return False
    
    # Check OpenAI package
    try:
        import openai
        print("✅ OpenAI package available")
    except ImportError:
        print("❌ OpenAI package missing. Run: pip install openai")
        return False
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    
    print("✅ Environment ready")
    return True

async def create_simple_agent():
    """Create an agent using the simplest recommended method."""
    print("\n🤖 Creating agent with simple method...")
    
    # Use the recommended simple import
    from langswarm.core.agents import create_openai_agent
    
    # Create agent with minimal configuration
    agent = create_openai_agent(
        model="gpt-3.5-turbo",  # Cost-effective model
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    print("✅ Agent created successfully")
    return agent

async def test_agent_conversation(agent):
    """Test the agent with a simple conversation."""
    print("\n💬 Testing agent conversation...")
    
    # Simple test message
    response = await agent.chat("Hello! Please respond with just 'Hello back!' and nothing else.")
    
    print(f"🤖 Agent response: {response.content}")
    print("✅ Conversation successful")
    
    return response

def create_programmatic_config():
    """Demonstrate programmatic configuration (recommended over YAML)."""
    print("\n📋 Creating programmatic configuration...")
    
    from langswarm.core.config import LangSwarmConfig
    from langswarm.core.config.schema import AgentConfig, MemoryConfig, ProviderType
    
    # Create configuration in code (not YAML)
    config = LangSwarmConfig(
        version="2.0",
        name="LLM-Friendly Setup",
        description="Simple configuration for LLM usage",
        agents=[
            AgentConfig(
                id="assistant",
                name="Simple Assistant",
                provider=ProviderType.OPENAI,
                model="gpt-3.5-turbo",
                system_prompt="You are a helpful and concise assistant.",
                temperature=0.7
            )
        ],
        memory=MemoryConfig(
            backend="sqlite",  # No external dependencies
            config={
                "db_path": "llm_friendly_langswarm.db"
            }
        )
    )
    
    print("✅ Configuration created programmatically")
    print(f"   - Version: {config.version}")
    print(f"   - Agents: {len(config.agents)}")
    print(f"   - Memory: {config.memory.backend}")
    
    return config

async def demonstrate_builder_pattern():
    """Demonstrate the builder pattern for more advanced usage."""
    print("\n🏗️ Demonstrating builder pattern...")
    
    from langswarm.core.agents import AgentBuilder
    
    # Use builder pattern for more control
    agent = (AgentBuilder()
             .openai()  # Uses OPENAI_API_KEY from environment
             .model("gpt-3.5-turbo")
             .system_prompt("You are a helpful assistant that gives brief responses.")
             .temperature(0.5)
             .timeout(30)
             .build())
    
    print("✅ Agent built with builder pattern")
    
    # Test it
    response = await agent.chat("What is 2+2? Answer in one word.")
    print(f"🤖 Builder agent response: {response.content}")
    
    return agent

async def main():
    """Main function demonstrating LLM-friendly LangSwarm usage."""
    print("🚀 LLM-Friendly LangSwarm Setup")
    print("=" * 50)
    
    # Step 1: Validate environment
    if not validate_environment():
        print("\n❌ Environment validation failed. Please fix the issues above.")
        return False
    
    try:
        # Step 2: Create simple agent (recommended method)
        agent = await create_simple_agent()
        
        # Step 3: Test agent
        await test_agent_conversation(agent)
        
        # Step 4: Show programmatic configuration
        config = create_programmatic_config()
        
        # Step 5: Demonstrate builder pattern
        builder_agent = await demonstrate_builder_pattern()
        
        # Success summary
        print(f"\n{'='*50}")
        print("🎉 SUCCESS! LangSwarm setup complete")
        print(f"{'='*50}")
        
        print("\n✅ What worked:")
        print("   • Environment validation")
        print("   • Simple agent creation")
        print("   • Agent conversation")
        print("   • Programmatic configuration")
        print("   • Builder pattern")
        
        print("\n💡 Key takeaways for LLMs:")
        print("   1. Use create_openai_agent() for simplest setup")
        print("   2. Set OPENAI_API_KEY environment variable first")
        print("   3. Use programmatic config instead of YAML")
        print("   4. Start with gpt-3.5-turbo for cost efficiency")
        print("   5. Use builder pattern for advanced configuration")
        
        print("\n📝 Next steps:")
        print("   • Try different models (gpt-4, gpt-4o)")
        print("   • Add system prompts for specific behaviors")
        print("   • Experiment with temperature settings")
        print("   • Add memory and tools as needed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Provide helpful debugging info
        print(f"\n🔧 Debugging info:")
        print(f"   Python version: {sys.version}")
        print(f"   API key set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
        
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            print(f"\n🎯 Setup completed successfully!")
            print(f"You can now use LangSwarm with confidence.")
        else:
            print(f"\n⚠️ Setup had issues. Check the error messages above.")
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
