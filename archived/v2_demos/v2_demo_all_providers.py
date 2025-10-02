#!/usr/bin/env python3
"""
LangSwarm V2 All Providers Demonstration

Shows all implemented provider types including OpenAI, Anthropic, Gemini, and Cohere.
Demonstrates Phase 3 completion with comprehensive provider ecosystem.

Usage:
    python v2_demo_all_providers.py
"""

import asyncio
import sys
import traceback
import os
from typing import Optional, List

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.abspath('.'))

try:
    from langswarm.v2.core.agents import (
        AgentBuilder, ProviderType, AgentCapability,
        create_openai_agent, create_anthropic_agent, 
        create_gemini_agent, create_cohere_agent
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the LangSwarm root directory")
    sys.exit(1)


async def demo_all_provider_creation():
    """Demonstrate creating agents with all available providers"""
    print("============================================================")
    print("🌟 ALL PROVIDERS CREATION DEMO")
    print("============================================================")
    
    providers_to_test = [
        {
            "name": "OpenAI",
            "provider": ProviderType.OPENAI,
            "model": "gpt-4o",
            "factory": create_openai_agent,
            "description": "OpenAI GPT models"
        },
        {
            "name": "Anthropic",
            "provider": ProviderType.ANTHROPIC,
            "model": "claude-3-5-sonnet-20241022",
            "factory": create_anthropic_agent,
            "description": "Anthropic Claude models"
        },
        {
            "name": "Gemini",
            "provider": ProviderType.GEMINI,
            "model": "gemini-pro",
            "factory": create_gemini_agent,
            "description": "Google Gemini models"
        },
        {
            "name": "Cohere",
            "provider": ProviderType.COHERE,
            "model": "command-r-plus",
            "factory": create_cohere_agent,
            "description": "Cohere Command models"
        }
    ]
    
    created_agents = []
    
    for provider_info in providers_to_test:
        try:
            print(f"\n🔧 Creating {provider_info['name']} agent...")
            
            # Try creating with factory function
            agent = provider_info['factory'](
                name=f"v2-{provider_info['name'].lower()}-demo",
                model=provider_info['model'],
                system_prompt=f"You are a helpful assistant powered by {provider_info['description']}."
            )
            
            print(f"   ✅ {provider_info['name']} Agent created successfully")
            print(f"   📝 Agent ID: {agent.agent_id}")
            print(f"   🤖 Provider: {agent.configuration.provider.value}")
            print(f"   🧠 Model: {agent.configuration.model}")
            print(f"   ⚡ Provider Type: {type(agent._provider).__name__}")
            
            created_agents.append({
                "provider_name": provider_info['name'],
                "agent": agent,
                "real_provider": "Provider" in type(agent._provider).__name__
            })
            
        except Exception as e:
            print(f"   ⚠️ {provider_info['name']} agent creation failed: {type(e).__name__}")
            print(f"   📝 Reason: {str(e)}")
            if "not installed" in str(e):
                print(f"   💡 Install with: pip install {provider_info['name'].lower()}")
    
    return created_agents


async def demo_provider_capabilities_comparison():
    """Compare capabilities across all providers"""
    print("\n============================================================")
    print("⚖️ PROVIDER CAPABILITIES COMPARISON")
    print("============================================================")
    
    providers = [
        {"type": ProviderType.OPENAI, "model": "gpt-4o", "name": "OpenAI"},
        {"type": ProviderType.ANTHROPIC, "model": "claude-3-5-sonnet-20241022", "name": "Anthropic"},
        {"type": ProviderType.GEMINI, "model": "gemini-pro", "name": "Gemini"},
        {"type": ProviderType.COHERE, "model": "command-r-plus", "name": "Cohere"}
    ]
    
    capability_matrix = {}
    
    for provider_info in providers:
        try:
            agent = (AgentBuilder()
                    .provider(provider_info["type"])
                    .model(provider_info["model"])
                    .name(f"capability-test-{provider_info['name'].lower()}")
                    .build())
            
            capabilities = [cap.value for cap in agent.capabilities]
            capability_matrix[provider_info["name"]] = {
                "agent": agent,
                "capabilities": capabilities,
                "provider_type": type(agent._provider).__name__
            }
            
        except Exception as e:
            capability_matrix[provider_info["name"]] = {
                "error": str(e),
                "capabilities": [],
                "provider_type": "Error"
            }
    
    # Display capability comparison
    all_capabilities = set()
    for provider_data in capability_matrix.values():
        if "capabilities" in provider_data:
            all_capabilities.update(provider_data["capabilities"])
    
    print("📊 Capability Matrix:")
    print(f"{'Capability':<25} | {'OpenAI':<8} | {'Anthropic':<8} | {'Gemini':<8} | {'Cohere':<8}")
    print("-" * 80)
    
    for capability in sorted(all_capabilities):
        row = f"{capability:<25} |"
        for provider in ["OpenAI", "Anthropic", "Gemini", "Cohere"]:
            if provider in capability_matrix and "capabilities" in capability_matrix[provider]:
                has_cap = capability in capability_matrix[provider]["capabilities"]
                symbol = "   ✅   " if has_cap else "   ❌   "
            else:
                symbol = "   ❓   "
            row += f"{symbol}|"
        print(row)
    
    return capability_matrix


async def demo_provider_health_checks():
    """Demonstrate health checks across all providers"""
    print("\n============================================================")
    print("🏥 PROVIDER HEALTH CHECKS")
    print("============================================================")
    
    providers = [
        {"name": "OpenAI", "create": lambda: create_openai_agent("health-openai")},
        {"name": "Anthropic", "create": lambda: create_anthropic_agent("health-anthropic")},
        {"name": "Gemini", "create": lambda: create_gemini_agent("health-gemini")},
        {"name": "Cohere", "create": lambda: create_cohere_agent("health-cohere")}
    ]
    
    health_results = {}
    
    for provider_info in providers:
        try:
            print(f"\n🔍 {provider_info['name']} Health Check:")
            agent = provider_info['create']()
            
            health = await agent.get_health()
            health_results[provider_info['name']] = health
            
            print(f"   📊 Status: {health.get('status', 'unknown')}")
            print(f"   🤖 Provider: {health.get('provider', 'unknown')}")
            print(f"   🧠 Model: {health.get('model', 'unknown')}")
            print(f"   🔧 Tools: {health.get('tools_registered', 0)}")
            print(f"   💬 Sessions: {health.get('sessions_active', 0)}")
            print(f"   📈 Success Rate: {health.get('success_rate', 0):.1%}")
            
            # Provider-specific health info
            provider_health = health.get('provider_health', {})
            if provider_health and isinstance(provider_health, dict):
                api_status = provider_health.get('status', 'unknown')
                print(f"   🌐 API Status: {api_status}")
                
                # Show provider-specific features
                if provider_info['name'].lower() + '_features' in health:
                    features = health[provider_info['name'].lower() + '_features']
                    if isinstance(features, dict):
                        print(f"   ✨ Special Features:")
                        for feature, supported in features.items():
                            symbol = "✅" if supported else "❌"
                            print(f"      {symbol} {feature}")
            
        except Exception as e:
            print(f"   ❌ Health check failed: {type(e).__name__}: {e}")
            health_results[provider_info['name']] = {"error": str(e)}
    
    return health_results


async def demo_provider_builder_patterns():
    """Demonstrate different builder patterns for each provider"""
    print("\n============================================================")
    print("🏗️ PROVIDER BUILDER PATTERNS")
    print("============================================================")
    
    patterns = [
        {
            "name": "Direct Provider Setting",
            "builder": lambda: (AgentBuilder()
                               .provider(ProviderType.OPENAI)
                               .model("gpt-4o")
                               .name("direct-openai")
                               .build())
        },
        {
            "name": "Fluent Provider Chain",
            "builder": lambda: (AgentBuilder()
                               .openai()
                               .model("gpt-4o")
                               .temperature(0.8)
                               .max_tokens(2000)
                               .name("fluent-openai")
                               .build())
        },
        {
            "name": "Factory Function",
            "builder": lambda: create_anthropic_agent(
                name="factory-anthropic",
                model="claude-3-5-sonnet-20241022",
                temperature=0.7
            )
        },
        {
            "name": "Complex Configuration",
            "builder": lambda: (AgentBuilder()
                               .gemini()
                               .model("gemini-pro")
                               .system_prompt("You are a specialized AI assistant.")
                               .enable_tools(["system_status", "text_processor"])
                               .enable_memory(100)
                               .enable_streaming()
                               .temperature(0.9)
                               .name("complex-gemini")
                               .build())
        }
    ]
    
    for pattern in patterns:
        try:
            print(f"\n🔧 {pattern['name']}:")
            agent = pattern['builder']()
            
            print(f"   ✅ Agent created: {agent.name}")
            print(f"   🤖 Provider: {agent.configuration.provider.value}")
            print(f"   🧠 Model: {agent.configuration.model}")
            print(f"   ⚙️ Provider Type: {type(agent._provider).__name__}")
            
            # Show configuration details
            config = agent.configuration
            if config.temperature:
                print(f"   🌡️ Temperature: {config.temperature}")
            if config.max_tokens:
                print(f"   📏 Max Tokens: {config.max_tokens}")
            if config.tools:
                print(f"   🔧 Tools: {', '.join(config.tools)}")
            if config.memory_enabled:
                print(f"   🧠 Memory: Enabled (max {config.max_memory_messages} messages)")
            
        except Exception as e:
            print(f"   ❌ Pattern failed: {type(e).__name__}: {e}")


async def demo_provider_feature_detection():
    """Detect which provider features are actually available"""
    print("\n============================================================")
    print("🔍 PROVIDER FEATURE DETECTION")
    print("============================================================")
    
    providers = ["OpenAI", "Anthropic", "Gemini", "Cohere"]
    feature_results = {}
    
    for provider_name in providers:
        try:
            print(f"\n🔍 {provider_name} Feature Detection:")
            
            # Check if provider package is available
            provider_available = False
            real_provider = False
            
            if provider_name == "OpenAI":
                try:
                    from langswarm.v2.core.agents.providers.openai import OpenAIProvider
                    import openai
                    provider_available = True
                    real_provider = True
                except ImportError:
                    pass
            elif provider_name == "Anthropic":
                try:
                    from langswarm.v2.core.agents.providers.anthropic import AnthropicProvider
                    import anthropic
                    provider_available = True
                    real_provider = True
                except ImportError:
                    pass
            elif provider_name == "Gemini":
                try:
                    from langswarm.v2.core.agents.providers.gemini import GeminiProvider
                    import google.generativeai
                    provider_available = True
                    real_provider = True
                except ImportError:
                    pass
            elif provider_name == "Cohere":
                try:
                    from langswarm.v2.core.agents.providers.cohere import CohereProvider
                    import cohere
                    provider_available = True
                    real_provider = True
                except ImportError:
                    pass
            
            print(f"   📦 Provider Implementation: {'✅ Available' if provider_available else '❌ Not Available'}")
            print(f"   🌐 Native Package: {'✅ Installed' if real_provider else '❌ Not Installed'}")
            
            # Try creating agent to test actual functionality
            try:
                if provider_name == "OpenAI":
                    agent = create_openai_agent(f"test-{provider_name.lower()}")
                elif provider_name == "Anthropic":
                    agent = create_anthropic_agent(f"test-{provider_name.lower()}")
                elif provider_name == "Gemini":
                    agent = create_gemini_agent(f"test-{provider_name.lower()}")
                elif provider_name == "Cohere":
                    agent = create_cohere_agent(f"test-{provider_name.lower()}")
                
                provider_type = type(agent._provider).__name__
                is_mock = "Mock" in provider_type
                print(f"   🎭 Provider Type: {provider_type} ({'Mock' if is_mock else 'Real'})")
                
                feature_results[provider_name] = {
                    "implementation_available": provider_available,
                    "package_installed": real_provider,
                    "provider_type": provider_type,
                    "is_mock": is_mock,
                    "agent_created": True
                }
                
            except Exception as e:
                print(f"   ❌ Agent creation failed: {type(e).__name__}")
                feature_results[provider_name] = {
                    "implementation_available": provider_available,
                    "package_installed": real_provider,
                    "agent_created": False,
                    "error": str(e)
                }
            
        except Exception as e:
            print(f"   ❌ Feature detection failed: {e}")
            feature_results[provider_name] = {"error": str(e)}
    
    return feature_results


async def main():
    """Run all Phase 3 demonstration scenarios"""
    print("🚀 LangSwarm V2 All Providers Demonstration - Phase 3")
    print("=" * 80)
    print("This demo shows all implemented providers including OpenAI, Anthropic,")
    print("Gemini, and Cohere, demonstrating the complete V2 provider ecosystem.")
    print("=" * 80)
    
    # Run all demos
    demos = [
        ("All Provider Creation", demo_all_provider_creation),
        ("Provider Capabilities Comparison", demo_provider_capabilities_comparison),
        ("Provider Health Checks", demo_provider_health_checks),
        ("Provider Builder Patterns", demo_provider_builder_patterns),
        ("Provider Feature Detection", demo_provider_feature_detection),
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
            traceback.print_exc()
            results[demo_name] = None
    
    # Summary
    print("\n" + "="*80)
    print("📊 PHASE 3 DEMONSTRATION SUMMARY")
    print("="*80)
    
    successful = sum(1 for result in results.values() if result is not None)
    total = len(results)
    
    print(f"✅ Successful demos: {successful}/{total}")
    print(f"❌ Failed demos: {total - successful}/{total}")
    
    # Feature detection summary
    if "Provider Feature Detection" in results and results["Provider Feature Detection"]:
        print("\n🔍 Provider Implementation Status:")
        for provider, features in results["Provider Feature Detection"].items():
            if isinstance(features, dict) and "agent_created" in features:
                status = "✅" if features["agent_created"] else "❌"
                provider_type = features.get("provider_type", "Unknown")
                is_mock = " (Mock)" if features.get("is_mock", False) else " (Real)"
                print(f"   {status} {provider}: {provider_type}{is_mock}")
    
    if successful == total:
        print("\n🎉 All Phase 3 demonstrations completed successfully!")
        print("🏗️ V2 Agent Provider ecosystem is comprehensive and working.")
        print("\n📋 Phase 3 Achievements:")
        print("   ✅ 4 Provider implementations (OpenAI, Anthropic, Gemini, Cohere)")
        print("   ✅ Unified builder pattern for all providers")
        print("   ✅ Comprehensive capability comparison")
        print("   ✅ Health monitoring across all providers")
        print("   ✅ Flexible configuration patterns")
        print("   ✅ Graceful fallback to mock providers")
        print("\n🎯 Task 04 Phase 3 is COMPLETE! 🚀")
    else:
        print(f"\n⚠️ Some demonstrations had issues. Check the output above for details.")
    
    return results


if __name__ == "__main__":
    # Run the comprehensive Phase 3 demonstration
    try:
        results = asyncio.run(main())
        successful_results = len([r for r in results.values() if r])
        print(f"\n🏁 Phase 3 demonstration completed. Results: {successful_results}/{len(results)} successful")
    except KeyboardInterrupt:
        print("\n\n⚠️ Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demonstration failed with error: {e}")
        traceback.print_exc()
