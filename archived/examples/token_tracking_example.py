"""
LangSwarm V2 Token Tracking System Example

This example demonstrates how to use the comprehensive token tracking system
in LangSwarm V2 for monitoring token usage, costs, and context sizes.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Import V2 components
from langswarm.v2.core.middleware import create_enhanced_pipeline
from langswarm.v2.core.observability import (
    initialize_observability,
    TokenBudgetConfig,
    TokenUsageAggregator,
    ContextSizeMonitor,
    TokenBudgetManager
)
from langswarm.v2.core.middleware.interceptors import create_token_tracking_interceptor
from langswarm.v2.core.agents import BaseAgent, AgentConfiguration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_token_tracking():
    """
    Example 1: Basic token tracking without budget enforcement.
    This shows how token usage is automatically tracked for all agent interactions.
    """
    
    print("=" * 60)
    print("Example 1: Basic Token Tracking")
    print("=" * 60)
    
    # Initialize observability system
    initialize_observability({
        "enabled": True,
        "metrics_enabled": True,
        "tracing_enabled": True
    })
    
    # Create enhanced pipeline with token tracking
    pipeline = create_enhanced_pipeline(
        enable_token_tracking=True,
        enable_budget_enforcement=False,
        enable_context_monitoring=True
    )
    
    print("✓ Created enhanced pipeline with token tracking")
    
    # Simulate agent configuration
    config = AgentConfiguration(
        provider="openai",
        model="gpt-4o-mini",
        api_key="your-api-key-here"
    )
    
    # Create agent with enhanced pipeline
    agent = BaseAgent(
        agent_id="token-tracking-example",
        name="Token Tracking Example Agent",
        configuration=config
    )
    
    print("✓ Created agent with token tracking capabilities")
    
    # Simulate some interactions (in real usage, these would be actual API calls)
    interactions = [
        "Hello, how are you today?",
        "Can you explain quantum computing in simple terms?",
        "Write a short story about a robot learning to paint.",
        "What's the weather like in New York?",
    ]
    
    for i, message in enumerate(interactions, 1):
        print(f"\nInteraction {i}: {message[:50]}...")
        
        # In real usage, this would make actual API calls and track tokens
        # For this example, we'll simulate the token tracking
        await simulate_token_usage(agent, message, i)
    
    # Get usage statistics
    print("\n" + "=" * 40)
    print("Usage Statistics")
    print("=" * 40)
    
    # Access token tracking interceptor from pipeline
    token_interceptor = next(
        (interceptor for interceptor in pipeline._interceptors 
         if interceptor.name == "token_tracking"), 
        None
    )
    
    if token_interceptor:
        stats = await token_interceptor.get_tracking_stats()
        print(f"Events tracked: {stats['events_tracked']}")
        print(f"Contexts monitored: {stats['contexts_monitored']}")
        
        # Get session usage
        session_usage = await token_interceptor.get_session_usage("example-session")
        if session_usage:
            print(f"Session tokens: {session_usage.get('total_tokens', 0)}")
            print(f"Session cost: ${session_usage.get('total_cost', 0.0):.4f}")


async def example_budget_enforcement():
    """
    Example 2: Token budget enforcement with limits and alerts.
    This shows how to set up budget limits and enforce them.
    """
    
    print("\n" + "=" * 60)
    print("Example 2: Budget Enforcement")
    print("=" * 60)
    
    # Create budget configuration
    budget_config = TokenBudgetConfig(
        daily_token_limit=10000,
        session_token_limit=2000,
        cost_limit_usd=5.0,
        token_alert_threshold=0.8,
        cost_alert_threshold=0.8,
        enforce_limits=True,
        auto_compress_context=True
    )
    
    print("✓ Created budget configuration:")
    print(f"  Daily limit: {budget_config.daily_token_limit:,} tokens")
    print(f"  Session limit: {budget_config.session_token_limit:,} tokens")
    print(f"  Cost limit: ${budget_config.cost_limit_usd}")
    
    # Create pipeline with budget enforcement
    pipeline = create_enhanced_pipeline(
        enable_token_tracking=True,
        enable_budget_enforcement=True,
        enable_context_monitoring=True
    )
    
    # Get token tracking interceptor and configure budget
    token_interceptor = next(
        (interceptor for interceptor in pipeline._interceptors 
         if interceptor.name == "token_tracking"), 
        None
    )
    
    if token_interceptor:
        await token_interceptor.configure_budget("user_123", budget_config)
        print("✓ Configured budget for user_123")
        
        # Simulate usage that approaches limits
        print("\nSimulating usage that approaches budget limits...")
        
        for i in range(5):
            usage_result = await simulate_budget_check(
                token_interceptor, 
                "user_123", 
                f"session_{i}", 
                tokens=1500 + (i * 200)
            )
            
            print(f"  Check {i+1}: {usage_result}")
    
    # Show budget status
    if token_interceptor:
        budget_status = await token_interceptor.budget_manager.get_budget_status("user_123")
        print(f"\nBudget Status: {budget_status}")


async def example_context_monitoring():
    """
    Example 3: Context size monitoring and optimization recommendations.
    This shows how to monitor conversation context and get compression recommendations.
    """
    
    print("\n" + "=" * 60)
    print("Example 3: Context Size Monitoring")
    print("=" * 60)
    
    # Initialize context monitor
    context_monitor = ContextSizeMonitor()
    
    # Simulate different context scenarios
    scenarios = [
        {"model": "gpt-4o", "messages": 10, "avg_length": 100},
        {"model": "gpt-3.5-turbo", "messages": 50, "avg_length": 200},
        {"model": "gpt-4", "messages": 30, "avg_length": 300},
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['model']} with {scenario['messages']} messages")
        
        # Simulate context calculation
        context_info = await simulate_context_calculation(
            context_monitor,
            scenario['model'],
            scenario['messages'],
            scenario['avg_length']
        )
        
        print(f"  Context size: {context_info.current_size:,} tokens")
        print(f"  Utilization: {context_info.utilization_percent:.1f}%")
        print(f"  Compression recommended: {context_info.compression_recommended}")
        
        if context_info.compression_recommended:
            print(f"  Urgency: {context_info.compression_urgency.value}")
            print(f"  Target size: {context_info.recommended_target_size:,} tokens")
        
        # Get compression recommendation
        recommendation = await context_monitor.get_compression_recommendation(context_info)
        if recommendation.get("compress"):
            print(f"  Strategy: {recommendation.get('strategy', 'N/A')}")
            print(f"  Reason: {recommendation.get('reason', 'N/A')}")


async def example_usage_analytics():
    """
    Example 4: Usage analytics and optimization insights.
    This shows how to analyze token usage patterns and get recommendations.
    """
    
    print("\n" + "=" * 60)
    print("Example 4: Usage Analytics")
    print("=" * 60)
    
    # Create usage aggregator
    aggregator = TokenUsageAggregator()
    
    # Simulate historical usage data
    await simulate_historical_usage(aggregator)
    
    # Get analytics for different time ranges and groupings
    analytics_queries = [
        {"group_by": "model", "description": "Usage by model"},
        {"group_by": "provider", "description": "Usage by provider"},
        {"group_by": "day", "description": "Daily usage pattern"},
    ]
    
    for query in analytics_queries:
        print(f"\n{query['description']}:")
        
        analytics = await aggregator.get_usage_analytics(
            user_id="user_123",
            time_range=(
                datetime.utcnow() - timedelta(days=30),
                datetime.utcnow()
            ),
            group_by=query.get("group_by")
        )
        
        print(f"  Total tokens: {analytics.get('total_tokens', 0):,}")
        print(f"  Total cost: ${analytics.get('total_cost', 0.0):.2f}")
        print(f"  Average cost per token: ${analytics.get('cost_per_token', 0.0):.6f}")
        
        grouped_data = analytics.get("grouped_data", {})
        if grouped_data:
            print("  Top categories:")
            sorted_items = sorted(
                grouped_data.items(),
                key=lambda x: x[1].get("tokens", 0),
                reverse=True
            )[:3]
            
            for name, data in sorted_items:
                print(f"    {name}: {data.get('tokens', 0):,} tokens, ${data.get('cost', 0.0):.2f}")


async def example_production_deployment():
    """
    Example 5: Production deployment configuration.
    This shows how to configure the token tracking system for production use.
    """
    
    print("\n" + "=" * 60)
    print("Example 5: Production Deployment")
    print("=" * 60)
    
    # Production configuration
    production_config = {
        "observability": {
            "enabled": True,
            "log_level": "INFO",
            "metrics_enabled": True,
            "tracing_enabled": True,
            "async_processing": True
        },
        "token_tracking": {
            "enabled": True,
            "budget_enforcement": True,
            "context_monitoring": True,
            "budget_limits": {
                "daily_token_limit": 1000000,
                "session_token_limit": 50000,
                "cost_limit_usd": 100.0
            },
            "alerts": {
                "token_threshold": 0.8,
                "cost_threshold": 0.8,
                "context_threshold": 0.9
            },
            "optimization": {
                "auto_compress_context": True,
                "compression_threshold": 0.85
            }
        }
    }
    
    print("✓ Production configuration:")
    for section, settings in production_config.items():
        print(f"  {section}:")
        for key, value in settings.items():
            if isinstance(value, dict):
                print(f"    {key}:")
                for subkey, subvalue in value.items():
                    print(f"      {subkey}: {subvalue}")
            else:
                print(f"    {key}: {value}")
    
    # Initialize with production configuration
    initialize_observability(production_config["observability"])
    
    # Create production pipeline
    from langswarm.v2.core.middleware.enhanced_pipeline import create_production_pipeline
    
    pipeline = create_production_pipeline(
        token_budget_config=production_config["token_tracking"],
        enable_all_monitoring=True
    )
    
    print("\n✓ Created production pipeline with full token tracking")
    print("✓ Budget enforcement enabled")
    print("✓ Context monitoring enabled")
    print("✓ All observability features enabled")


# Helper functions for simulation

async def simulate_token_usage(agent, message: str, interaction_num: int):
    """Simulate token usage for demonstration purposes"""
    
    # Simulate token counts based on message length
    input_tokens = len(message) // 4 + 10  # Rough approximation
    output_tokens = input_tokens // 2 + 50  # Simulated response
    total_tokens = input_tokens + output_tokens
    
    # Simulate cost (rough OpenAI pricing)
    cost_estimate = (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
    
    print(f"  Tokens: {input_tokens} in + {output_tokens} out = {total_tokens} total")
    print(f"  Cost estimate: ${cost_estimate:.4f}")


async def simulate_budget_check(token_interceptor, user_id: str, session_id: str, tokens: int):
    """Simulate budget check for demonstration"""
    
    if not token_interceptor.budget_manager:
        return "Budget manager not available"
    
    result = await token_interceptor.budget_manager.check_budget_limit(
        user_id=user_id,
        session_id=session_id,
        projected_tokens=tokens
    )
    
    status = "✓ Allowed" if result.within_limit else "✗ Blocked"
    reason = f" ({result.reason})" if result.reason else ""
    
    return f"{tokens} tokens: {status}{reason}"


async def simulate_context_calculation(monitor, model: str, num_messages: int, avg_length: int):
    """Simulate context size calculation"""
    
    # Calculate approximate context size
    total_chars = num_messages * avg_length
    current_size = total_chars // 4  # Rough token approximation
    
    # Get model limit
    model_limits = {
        "gpt-4o": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 4096
    }
    max_size = model_limits.get(model, 4096)
    
    # Calculate utilization
    utilization_percent = (current_size / max_size) * 100
    
    # Create mock context info
    from langswarm.v2.core.observability.token_tracking import ContextSizeInfo
    
    return ContextSizeInfo(
        current_size=current_size,
        max_size=max_size,
        utilization_percent=utilization_percent,
        messages_count=num_messages
    )


async def simulate_historical_usage(aggregator):
    """Simulate historical usage data for analytics"""
    
    from langswarm.v2.core.observability.token_tracking import TokenUsageEvent, TokenEventType
    
    # Simulate various usage events
    events = [
        {"model": "gpt-4o", "tokens": 1500, "cost": 0.045, "type": TokenEventType.CHAT},
        {"model": "gpt-4o-mini", "tokens": 2000, "cost": 0.012, "type": TokenEventType.CHAT},
        {"model": "gpt-3.5-turbo", "tokens": 1000, "cost": 0.003, "type": TokenEventType.TOOL_CALL},
        {"model": "gpt-4o", "tokens": 3000, "cost": 0.090, "type": TokenEventType.FUNCTION_CALL},
        {"model": "gpt-4o-mini", "tokens": 800, "cost": 0.005, "type": TokenEventType.CHAT},
    ]
    
    for i, event_data in enumerate(events):
        event = TokenUsageEvent(
            session_id="example-session",
            agent_id="analytics-agent",
            user_id="user_123",
            model=event_data["model"],
            provider="openai",
            total_tokens=event_data["tokens"],
            input_tokens=int(event_data["tokens"] * 0.3),
            output_tokens=int(event_data["tokens"] * 0.7),
            cost_estimate=event_data["cost"],
            event_type=event_data["type"]
        )
        
        await aggregator.record_usage(event)


async def main():
    """Run all examples"""
    
    print("LangSwarm V2 Token Tracking System Examples")
    print("=" * 60)
    
    try:
        await example_basic_token_tracking()
        await example_budget_enforcement()
        await example_context_monitoring()
        await example_usage_analytics()
        await example_production_deployment()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
