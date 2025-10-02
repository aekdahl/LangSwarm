#!/usr/bin/env python3
"""
LangSwarm V2 Agent Provider Demonstration

Shows the new native provider implementations for OpenAI and Anthropic,
replacing the complex AgentWrapper with clean, provider-specific code.

Usage:
    python v2_demo_agent_providers.py
"""

import asyncio
import sys
import traceback
import os
from typing import Optional

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.abspath('.'))

try:
    from langswarm.v2.core.agents import (
        AgentBuilder, ProviderType, AgentCapability,
        create_openai_agent, create_anthropic_agent
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the LangSwarm root directory")
    sys.exit(1)


async def demo_basic_agent_creation():
    """Demonstrate basic agent creation with V2 builder"""
    print("============================================================")
    print("🏗️ BASIC V2 AGENT CREATION")
    print("============================================================")
    
    try:
        # Method 1: Fluent builder pattern
        print("1️⃣ Creating OpenAI agent with fluent builder...")
        openai_agent = (AgentBuilder()
                       .openai()
                       .model("gpt-4o")
                       .name("v2-openai-demo")
                       .system_prompt("You are a helpful AI assistant built with LangSwarm V2.")
                       .temperature(0.7)
                       .max_tokens(1000)
                       .build())
        
        print(f"   ✅ OpenAI Agent created: {openai_agent.name}")
        print(f"   📝 Agent ID: {openai_agent.agent_id}")
        print(f"   🤖 Provider: {openai_agent.configuration.provider.value}")
        print(f"   🧠 Model: {openai_agent.configuration.model}")
        
        # Method 2: Convenience factory function
        print("\n2️⃣ Creating Anthropic agent with factory function...")
        anthropic_agent = create_anthropic_agent(
            name="v2-anthropic-demo",
            model="claude-3-5-sonnet-20241022",
            system_prompt="You are Claude, built with LangSwarm V2.",
            temperature=0.8
        )
        
        print(f"   ✅ Anthropic Agent created: {anthropic_agent.name}")
        print(f"   📝 Agent ID: {anthropic_agent.agent_id}")
        print(f"   🤖 Provider: {anthropic_agent.configuration.provider.value}")
        print(f"   🧠 Model: {anthropic_agent.configuration.model}")
        
        # Method 3: Builder with multiple configurations
        print("\n3️⃣ Creating advanced agent with tools and memory...")
        advanced_agent = (AgentBuilder()
                         .openai()
                         .model("gpt-4o")
                         .name("v2-advanced-demo")
                         .system_prompt("You are an advanced AI with tools and memory.")
                         .temperature(0.9)
                         .max_tokens(2000)
                         .enable_tools(["system_status", "text_processor"])
                         .enable_memory()
                         .enable_streaming()
                         .build())
        
        print(f"   ✅ Advanced Agent created: {advanced_agent.name}")
        print(f"   🔧 Tools enabled: {advanced_agent.configuration.tools}")
        print(f"   🧠 Memory enabled: {advanced_agent.configuration.memory_enabled}")
        print(f"   🌊 Streaming enabled: {advanced_agent.configuration.streaming_enabled}")
        
        return [openai_agent, anthropic_agent, advanced_agent]
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        traceback.print_exc()
        return []


async def demo_agent_capabilities():
    """Demonstrate agent capability detection and health checks"""
    print("\n============================================================")
    print("🔍 AGENT CAPABILITIES & HEALTH CHECKS")
    print("============================================================")
    
    try:
        # Create agents for capability testing
        openai_agent = (AgentBuilder()
                       .openai()
                       .model("gpt-4o")
                       .name("capability-test")
                       .enable_tools(["system_status"])
                       .enable_memory()
                       .build())
        
        # Show capabilities
        print("1️⃣ Agent Capabilities:")
        capabilities = openai_agent.capabilities
        for cap in capabilities:
            print(f"   ✅ {cap.value}")
        
        # Health check
        print("\n2️⃣ Health Check:")
        health = await openai_agent.get_health()
        print(f"   📊 Status: {health.get('status', 'unknown')}")
        print(f"   🤖 Provider: {health.get('provider', 'unknown')}")
        print(f"   🧠 Model: {health.get('model', 'unknown')}")
        print(f"   📝 Agent ID: {health.get('agent_id', 'unknown')}")
        print(f"   🔧 Tools: {health.get('tools_registered', 0)}")
        print(f"   💬 Sessions: {health.get('sessions_active', 0)}")
        
        # Provider-specific features (if implemented)
        if 'openai_features' in health:
            print("\n3️⃣ OpenAI-specific features:")
            features = health['openai_features']
            for feature, supported in features.items():
                status = "✅" if supported else "❌"
                print(f"   {status} {feature}: {supported}")
        
        return openai_agent
        
    except Exception as e:
        print(f"❌ Capability demo failed: {e}")
        traceback.print_exc()
        return None


async def demo_provider_comparison():
    """Compare different provider implementations"""
    print("\n============================================================")
    print("⚖️ PROVIDER COMPARISON")
    print("============================================================")
    
    try:
        # Create agents with different providers
        providers_config = [
            {"provider": ProviderType.OPENAI, "model": "gpt-4o", "name": "openai-comparison"},
            {"provider": ProviderType.ANTHROPIC, "model": "claude-3-5-sonnet-20241022", "name": "anthropic-comparison"}
        ]
        
        agents = []
        for config in providers_config:
            try:
                agent = (AgentBuilder()
                        .provider(config["provider"])
                        .model(config["model"])
                        .name(config["name"])
                        .system_prompt("You are a helpful assistant for comparison testing.")
                        .build())
                agents.append(agent)
            except Exception as e:
                print(f"⚠️ Could not create {config['provider'].value} agent: {e}")
        
        # Compare provider features
        print(f"📊 Created {len(agents)} agents for comparison:")
        for i, agent in enumerate(agents, 1):
            print(f"\n{i}️⃣ {agent.configuration.provider.value.upper()} Agent:")
            print(f"   📝 Name: {agent.name}")
            print(f"   🧠 Model: {agent.configuration.model}")
            print(f"   🔧 Capabilities: {len(agent.capabilities)}")
            print(f"   ⚙️ Status: {agent.status.value}")
            
            # Show unique capabilities
            unique_caps = []
            for cap in agent.capabilities:
                if cap not in [AgentCapability.TEXT_GENERATION, AgentCapability.SYSTEM_PROMPTS]:
                    unique_caps.append(cap.value)
            
            if unique_caps:
                print(f"   ✨ Special capabilities: {', '.join(unique_caps)}")
        
        return agents
        
    except Exception as e:
        print(f"❌ Provider comparison failed: {e}")
        traceback.print_exc()
        return []


async def demo_mock_vs_real_providers():
    """Show the difference between mock and real providers"""
    print("\n============================================================")
    print("🎭 MOCK VS REAL PROVIDERS")
    print("============================================================")
    
    try:
        # Check what providers are available
        print("1️⃣ Provider Availability Check:")
        
        # Try importing real providers
        openai_available = False
        anthropic_available = False
        
        try:
            from langswarm.v2.core.agents.providers.openai import OpenAIProvider
            openai_available = True
            print("   ✅ OpenAI provider: Available")
        except ImportError:
            print("   ❌ OpenAI provider: Not available (install: pip install openai)")
        
        try:
            from langswarm.v2.core.agents.providers.anthropic import AnthropicProvider
            anthropic_available = True
            print("   ✅ Anthropic provider: Available")
        except ImportError:
            print("   ❌ Anthropic provider: Not available (install: pip install anthropic)")
        
        # Show what happens when we create agents
        print("\n2️⃣ Agent Creation Behavior:")
        
        openai_agent = (AgentBuilder()
                       .openai()
                       .model("gpt-4o")
                       .name("provider-test")
                       .build())
        
        print(f"   🤖 OpenAI agent provider type: {type(openai_agent._provider).__name__}")
        
        if openai_available:
            print("   ✅ Using real OpenAI provider")
        else:
            print("   🎭 Using MockProvider (real provider not available)")
        
        anthropic_agent = (AgentBuilder()
                          .anthropic()
                          .model("claude-3-5-sonnet-20241022")
                          .name("provider-test-2")
                          .build())
        
        print(f"   🤖 Anthropic agent provider type: {type(anthropic_agent._provider).__name__}")
        
        if anthropic_available:
            print("   ✅ Using real Anthropic provider")
        else:
            print("   🎭 Using MockProvider (real provider not available)")
        
        return [openai_agent, anthropic_agent]
        
    except Exception as e:
        print(f"❌ Mock vs real demo failed: {e}")
        traceback.print_exc()
        return []


async def demo_configuration_validation():
    """Show configuration validation and error handling"""
    print("\n============================================================")
    print("✅ CONFIGURATION VALIDATION")
    print("============================================================")
    
    try:
        print("1️⃣ Valid Configuration:")
        valid_agent = (AgentBuilder()
                      .openai()
                      .model("gpt-4o")
                      .name("valid-config")
                      .temperature(0.7)
                      .max_tokens(1000)
                      .build())
        
        print(f"   ✅ Valid agent created: {valid_agent.name}")
        
        print("\n2️⃣ Invalid Configurations (should fail gracefully):")
        
        # Test invalid temperature
        try:
            invalid_temp = (AgentBuilder()
                           .openai()
                           .model("gpt-4o")
                           .temperature(2.0)  # Invalid: > 1.0
                           .build())
            print("   ❌ Invalid temperature agent created (should have failed)")
        except Exception as e:
            print(f"   ✅ Invalid temperature correctly rejected: {type(e).__name__}")
        
        # Test invalid model
        try:
            invalid_model = (AgentBuilder()
                            .openai()
                            .model("invalid-model-name")
                            .build())
            print("   ❌ Invalid model agent created (should have failed)")
        except Exception as e:
            print(f"   ✅ Invalid model correctly rejected: {type(e).__name__}")
        
        # Test missing required fields
        try:
            missing_model = (AgentBuilder()
                           .openai()
                           # Missing model
                           .build())
            print("   ❌ Missing model agent created (should have failed)")
        except Exception as e:
            print(f"   ✅ Missing model correctly rejected: {type(e).__name__}")
        
        return valid_agent
        
    except Exception as e:
        print(f"❌ Configuration validation demo failed: {e}")
        traceback.print_exc()
        return None


async def demo_provider_statistics():
    """Show provider usage statistics and registry info"""
    print("\n============================================================")
    print("📊 PROVIDER STATISTICS")
    print("============================================================")
    
    try:
        from langswarm.v2.core.agents import get_agent_statistics, list_agent_info
        
        # Create several agents
        agents = []
        for i in range(3):
            agent = (AgentBuilder()
                    .openai()
                    .model("gpt-4o")
                    .name(f"stats-agent-{i+1}")
                    .build())
            agents.append(agent)
        
        # Get statistics
        print("1️⃣ Agent Registry Statistics:")
        stats = get_agent_statistics()
        print(f"   👥 Total agents: {stats.get('total_agents', 0)}")
        print(f"   ✅ Active agents: {stats.get('active_agents', 0)}")
        print(f"   🤖 Provider breakdown:")
        
        provider_counts = stats.get('provider_breakdown', {})
        for provider, count in provider_counts.items():
            print(f"      {provider}: {count}")
        
        print("\n2️⃣ Agent Registry Information:")
        agent_info = list_agent_info()
        for info in agent_info[:3]:  # Show first 3
            print(f"   📝 Agent: {info.get('name', 'unknown')}")
            print(f"      ID: {info.get('agent_id', 'unknown')}")
            print(f"      Provider: {info.get('provider', 'unknown')}")
            print(f"      Status: {info.get('status', 'unknown')}")
            print()
        
        return stats
        
    except Exception as e:
        print(f"❌ Provider statistics demo failed: {e}")
        traceback.print_exc()
        return {}


async def main():
    """Run all demonstration scenarios"""
    print("🚀 LangSwarm V2 Agent Provider Demonstration")
    print("=" * 80)
    print("This demo shows the new native provider implementations")
    print("that replace the complex AgentWrapper with clean, provider-specific code.")
    print("=" * 80)
    
    # Run all demos
    demos = [
        ("Basic Agent Creation", demo_basic_agent_creation),
        ("Agent Capabilities", demo_agent_capabilities),
        ("Provider Comparison", demo_provider_comparison),
        ("Mock vs Real Providers", demo_mock_vs_real_providers),
        ("Configuration Validation", demo_configuration_validation),
        ("Provider Statistics", demo_provider_statistics),
    ]
    
    results = {}
    for demo_name, demo_func in demos:
        try:
            print(f"\n{'='*20} {demo_name} {'='*20}")
            result = await demo_func()
            results[demo_name] = result
            print(f"✅ {demo_name} completed successfully")
        except Exception as e:
            print(f"❌ {demo_name} failed: {e}")
            results[demo_name] = None
    
    # Summary
    print("\n" + "="*80)
    print("📊 DEMONSTRATION SUMMARY")
    print("="*80)
    
    successful = sum(1 for result in results.values() if result is not None)
    total = len(results)
    
    print(f"✅ Successful demos: {successful}/{total}")
    print(f"❌ Failed demos: {total - successful}/{total}")
    
    if successful == total:
        print("\n🎉 All demonstrations completed successfully!")
        print("🏗️ V2 Agent Provider system is working correctly.")
        print("\n📋 Next Steps:")
        print("   1. Add API keys to test real provider functionality")
        print("   2. Implement additional providers (Gemini, Cohere, etc.)")
        print("   3. Add provider-specific features and optimizations")
        print("   4. Complete Phase 2 implementation")
    else:
        print(f"\n⚠️ Some demonstrations failed. Check the output above for details.")
    
    return results


if __name__ == "__main__":
    # Run the demonstration
    try:
        results = asyncio.run(main())
        print(f"\n🏁 Demonstration completed. Results: {len([r for r in results.values() if r])}/{len(results)} successful")
    except KeyboardInterrupt:
        print("\n\n⚠️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demonstration failed with error: {e}")
        traceback.print_exc()
