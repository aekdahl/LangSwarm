#!/usr/bin/env python3
"""
LangSwarm Hybrid Instrumentation Example

This example demonstrates the hybrid approach to observability:
- Key operations are automatically instrumented
- Detailed tracing can be added manually for fine-grained control

Prerequisites:
1. Install LangSwarm with OpenTelemetry support:
   pip install langswarm[opentelemetry]

2. Start Jaeger (optional):
   docker run -d --name jaeger -p 16686:16686 -p 14268:14268 jaegertracing/all-in-one:latest
"""

import asyncio
import logging
from datetime import datetime

from langswarm.core.observability import (
    ObservabilityConfig, ObservabilityProvider,
    initialize_auto_instrumentation, start_auto_instrumentation,
    instrument_agent_operation, auto_instrument_function
)
from langswarm.core.agents import BaseAgent, AgentConfiguration, ProviderType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example of manual instrumentation for detailed tracing
@instrument_agent_operation("custom_reasoning")
async def custom_reasoning_step(agent, query: str):
    """Example of manually instrumented function for detailed tracing"""
    # This function is automatically traced because of the decorator
    await asyncio.sleep(0.1)  # Simulate reasoning time
    return f"Reasoning result for: {query}"


@auto_instrument_function("data_processing", "custom_component")
async def process_data(data: dict):
    """Example of generic auto-instrumentation"""
    # This function is automatically traced with custom component name
    await asyncio.sleep(0.05)  # Simulate processing
    return {"processed": True, "items": len(data)}


class MockAgentProvider:
    """Mock agent provider for demonstration"""
    
    async def validate_configuration(self, config):
        pass
    
    async def send_message(self, message, session, config):
        # Simulate LLM response
        await asyncio.sleep(0.2)
        
        from langswarm.core.agents.base import AgentResponse, AgentMessage, AgentUsage
        
        response_message = AgentMessage(
            role="assistant",
            content=f"Mock response to: {message.content}"
        )
        
        usage = AgentUsage(
            input_tokens=len(message.content) // 4,
            output_tokens=len(response_message.content) // 4,
            total_tokens=(len(message.content) + len(response_message.content)) // 4
        )
        
        return AgentResponse(
            success=True,
            message=response_message,
            usage=usage
        )


async def main():
    """Main example function demonstrating hybrid instrumentation"""
    
    print("🔄 LangSwarm Hybrid Instrumentation Example")
    print("=" * 50)
    
    # 1. Initialize automatic instrumentation
    print("1️⃣  Initializing automatic instrumentation...")
    
    config = ObservabilityConfig(
        # Basic observability
        enabled=True,
        log_level="INFO",
        tracing_enabled=True,
        metrics_enabled=True,
        
        # OpenTelemetry integration (optional)
        opentelemetry_enabled=True,
        opentelemetry_service_name="hybrid-instrumentation-example",
        opentelemetry_jaeger_endpoint="http://localhost:14268/api/traces",
        opentelemetry_prometheus_enabled=True,
        opentelemetry_prometheus_port=8002,
    )
    
    # Initialize and start auto-instrumentation
    provider = initialize_auto_instrumentation(config)
    await start_auto_instrumentation()
    
    print("   ✅ Auto-instrumentation initialized")
    print("   📊 Metrics available at: http://localhost:8002/metrics")
    print("   🔍 Traces available at: http://localhost:16686 (if Jaeger running)")
    
    # 2. Create an agent (automatically instrumented)
    print("\n2️⃣  Creating agent with automatic instrumentation...")
    
    agent_config = AgentConfiguration(
        provider=ProviderType.OPENAI,
        model="gpt-4",
        system_prompt="You are a helpful assistant."
    )
    
    agent = BaseAgent(
        name="demo-agent",
        configuration=agent_config,
        provider=MockAgentProvider()
    )
    
    # Initialize agent (automatically traced)
    await agent.initialize()
    print("   ✅ Agent initialized (automatically traced)")
    
    # 3. Demonstrate automatic instrumentation
    print("\n3️⃣  Demonstrating automatic instrumentation...")
    
    # These operations are automatically traced and metrics recorded
    response1 = await agent.chat("Hello, how are you?")
    print(f"   📤 Chat 1: {response1.content[:50]}...")
    
    response2 = await agent.chat("What's the weather like?")
    print(f"   📤 Chat 2: {response2.content[:50]}...")
    
    response3 = await agent.chat("Tell me a joke")
    print(f"   📤 Chat 3: {response3.content[:50]}...")
    
    print("   ✅ All chat operations automatically traced and metrics recorded")
    
    # 4. Demonstrate manual instrumentation for detailed tracing
    print("\n4️⃣  Demonstrating manual instrumentation...")
    
    # Custom reasoning step with detailed tracing
    reasoning_result = await custom_reasoning_step(agent, "complex problem")
    print(f"   🧠 Custom reasoning: {reasoning_result}")
    
    # Generic data processing with custom component
    data = {"items": ["a", "b", "c"], "metadata": {"version": 1}}
    processed = await process_data(data)
    print(f"   📊 Data processing: {processed}")
    
    print("   ✅ Manual instrumentation completed")
    
    # 5. Show what gets automatically exported
    print("\n5️⃣  What gets automatically exported:")
    print("   🔍 Traces:")
    print("     - agent.initialize (agent initialization)")
    print("     - agent.chat (each chat request)")
    print("     - agent.provider_call (LLM API calls)")
    print("     - custom_reasoning (manual instrumentation)")
    print("     - data_processing (manual instrumentation)")
    print()
    print("   📊 Metrics:")
    print("     - agent.initializations_total")
    print("     - agent.chat_requests_total")
    print("     - agent.chat_duration_seconds")
    print("     - agent.chat_input_tokens, agent.chat_output_tokens")
    print("     - custom_reasoning.calls_total, custom_reasoning.duration_seconds")
    print("     - data_processing.calls_total, data_processing.duration_seconds")
    print()
    print("   🏷️  Tags/Attributes:")
    print("     - agent_name, provider, model")
    print("     - success/error status")
    print("     - token usage, response times")
    print("     - custom tags from manual instrumentation")
    
    # 6. Demonstrate error handling
    print("\n6️⃣  Demonstrating error handling...")
    
    try:
        # This will cause an error (invalid session)
        await agent.chat("This should work", session_id="invalid-session")
    except Exception as e:
        print(f"   ❌ Expected error caught: {type(e).__name__}")
        print("   ✅ Error automatically traced and metrics recorded")
    
    # 7. Cleanup
    print("\n7️⃣  Cleaning up...")
    
    # Flush all telemetry data
    await provider.flush()
    
    # Stop auto-instrumentation
    from langswarm.core.observability import stop_auto_instrumentation
    await stop_auto_instrumentation()
    
    print("   ✅ Cleanup completed")
    
    print("\n🎉 Hybrid instrumentation example completed!")
    print("\nKey Benefits of Hybrid Approach:")
    print("✅ Zero-configuration automatic tracing for key operations")
    print("✅ Detailed manual instrumentation when needed")
    print("✅ Comprehensive metrics collection")
    print("✅ OpenTelemetry export to external tools")
    print("✅ Production-ready with minimal overhead")


if __name__ == "__main__":
    asyncio.run(main())
