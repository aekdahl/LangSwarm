#!/usr/bin/env python3
"""
LangSwarm Priority 3 Demo: Native Streaming Support
==================================================

Comprehensive demonstration of LangSwarm's native streaming capabilities
across multiple LLM providers with configurable streaming modes and fallbacks.

Features Demonstrated:
• Native streaming for OpenAI, Gemini, Mistral, and Cohere
• Client-side streaming simulation for Claude and other models  
• Configurable streaming modes (real_time, immediate, integrated)
• Stream chunk parsing and aggregation
• Integration with structured responses and tool calling
• Backward compatibility with existing response modes
"""

import time
import json
from typing import Iterator, Dict, Any
from langswarm.core.wrappers.generic import AgentWrapper
from langswarm.core.wrappers.util_mixin import UtilMixin


def demo_streaming_capability_detection():
    """Demo: Detect streaming capabilities across different models"""
    print("🔍 DEMO: Streaming Capability Detection")
    print("=" * 50)
    
    models_to_test = [
        # OpenAI models (full streaming support)
        "gpt-4o",
        "gpt-4o-mini", 
        "chatgpt-4o-latest",
        
        # Claude models (no native streaming)
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest",
        
        # Gemini models (streaming support)
        "gemini-2.0",
        "gemini-2.0-flash", 
        "gemini-2.0-flash-live",  # Special: WebSocket streaming
        "gemini-1.5-flash",
        
        # Mistral models (streaming support)
        "mistral-large-latest",
        "mistral-large-2",
        
        # Cohere models (streaming support)
        "command-r-plus",
        "command-r-plus-08-2024",
        
        # Other models (no streaming)
        "deepseek-r1",
        "llama-3.3"
    ]
    
    util = UtilMixin()
    
    print("Model                          | Streaming | Type       | Structured")
    print("-" * 70)
    
    for model in models_to_test:
        util.model = model
        util.model_details = util._get_model_details(model)
        
        streaming_support = "✅" if util.supports_native_streaming() else "❌"
        streaming_type = util.get_streaming_type()
        structured_streaming = "✅" if util.supports_structured_streaming() else "❌"
        
        print(f"{model:<30} | {streaming_support:^9} | {streaming_type:<10} | {structured_streaming:^10}")
    
    print()


def demo_streaming_configuration():
    """Demo: Different streaming configuration options"""
    print("⚙️  DEMO: Streaming Configuration Options")
    print("=" * 50)
    
    util = UtilMixin()
    
    # Default configuration
    print("1. Default Configuration:")
    default_config = util.get_streaming_config()
    print(f"   {json.dumps(default_config, indent=4)}")
    print()
    
    # Custom configuration
    print("2. Custom Configuration:")
    custom_config = {
        "streaming": {
            "enabled": True,
            "mode": "immediate",
            "chunk_size": "sentence",
            "buffer_timeout": 100
            # fallback_mode will use default
        }
    }
    merged_config = util.get_streaming_config(custom_config)
    print(f"   Input: {json.dumps(custom_config['streaming'], indent=4)}")
    print(f"   Merged: {json.dumps(merged_config, indent=4)}")
    print()
    
    # Disabled configuration
    print("3. Streaming Disabled:")
    disabled_config = {"streaming": {"enabled": False}}
    disabled_merged = util.get_streaming_config(disabled_config)
    print(f"   {json.dumps(disabled_merged, indent=4)}")
    print()


def demo_streaming_parameters():
    """Demo: Provider-specific streaming parameters"""
    print("🌐 DEMO: Provider-Specific Streaming Parameters")
    print("=" * 50)
    
    util = UtilMixin()
    
    providers = [
        ("OpenAI GPT-4o", "gpt-4o"),
        ("Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022"),
        ("Gemini 2.0", "gemini-2.0"),
        ("Gemini Live API", "gemini-2.0-flash-live"),
        ("Mistral Large", "mistral-large-latest"),
        ("Cohere Command R+", "command-r-plus")
    ]
    
    for provider_name, model in providers:
        util.model = model
        util.model_details = util._get_model_details(model)
        
        params = util.get_streaming_parameters()
        
        print(f"{provider_name}:")
        if params:
            print(f"   Parameters: {json.dumps(params, indent=6)}")
        else:
            print("   No streaming parameters (client-side fallback)")
        print()


def demo_stream_chunk_parsing():
    """Demo: Parse streaming chunks from different providers"""
    print("📡 DEMO: Stream Chunk Parsing")
    print("=" * 50)
    
    util = UtilMixin()
    
    # Mock OpenAI chunk
    print("1. OpenAI Streaming Chunk:")
    util.model = "gpt-4o"
    
    # Simulate OpenAI chunk structure
    class MockOpenAIChunk:
        def __init__(self, content, finish_reason=None):
            self.choices = [type('Choice', (), {
                'delta': type('Delta', (), {'content': content})(),
                'finish_reason': finish_reason
            })()]
    
    openai_chunk = MockOpenAIChunk("Hello", None)
    parsed = util.parse_stream_chunk(openai_chunk)
    print(f"   Raw chunk: content='Hello', finish_reason=None")
    print(f"   Parsed: {json.dumps(parsed, indent=6)}")
    print()
    
    # Mock completion chunk
    print("2. OpenAI Completion Chunk:")
    completion_chunk = MockOpenAIChunk("", "stop")
    completion_parsed = util.parse_stream_chunk(completion_chunk)
    print(f"   Raw chunk: content='', finish_reason='stop'")
    print(f"   Parsed: {json.dumps(completion_parsed, indent=6)}")
    print()
    
    # Claude fallback chunk
    print("3. Claude Fallback Chunk:")
    util.model = "claude-3-5-sonnet-20241022"
    claude_chunk = "This is a Claude response chunk"
    claude_parsed = util.parse_stream_chunk(claude_chunk)
    print(f"   Raw chunk: '{claude_chunk}'")
    print(f"   Parsed: {json.dumps(claude_parsed, indent=6)}")
    print()
    
    # Chunk aggregation
    print("4. Chunk Aggregation:")
    chunks = [
        {"content": "The ", "metadata": {"provider": "openai"}},
        {"content": "quick ", "metadata": {"provider": "openai"}}, 
        {"content": "brown ", "metadata": {"provider": "openai"}},
        {"content": "fox", "metadata": {"provider": "openai"}}
    ]
    
    aggregated = util.aggregate_stream_chunks(chunks)
    print(f"   Input chunks: {len(chunks)} pieces")
    print(f"   Aggregated: {json.dumps(aggregated, indent=6)}")
    print()


def demo_configuration_scenarios():
    """Demo: Different workflow configuration scenarios"""
    print("🔧 DEMO: Configuration Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "Real-time Chat Application",
            "description": "Interactive chat with immediate token streaming",
            "config": {
                "streaming": {
                    "enabled": True,
                    "mode": "real_time",
                    "chunk_size": "word",
                    "buffer_timeout": 25
                }
            }
        },
        {
            "name": "Content Generation Platform", 
            "description": "Smooth content delivery with sentence-based chunks",
            "config": {
                "streaming": {
                    "enabled": True,
                    "mode": "immediate",
                    "chunk_size": "sentence",
                    "buffer_timeout": 100
                }
            }
        },
        {
            "name": "Production API",
            "description": "Efficient processing with integrated responses",
            "config": {
                "streaming": {
                    "enabled": False,
                    "fallback_mode": "integrated"
                }
            }
        },
        {
            "name": "Development/Debugging",
            "description": "Verbose streaming for development purposes", 
            "config": {
                "streaming": {
                    "enabled": True,
                    "mode": "real_time",
                    "chunk_size": "character",
                    "buffer_timeout": 10
                }
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"📋 {scenario['name']}")
        print(f"   Use case: {scenario['description']}")
        print(f"   Configuration:")
        print(f"   {json.dumps(scenario['config'], indent=6)}")
        print()


def demo_agent_configuration():
    """Demo: Agent configuration examples with streaming"""
    print("🤖 DEMO: Agent Configuration Examples")
    print("=" * 50)
    
    print("1. agents.yaml - Real-time Streaming Agent:")
    agents_yaml = '''
agents:
  - id: realtime_assistant
    type: openai
    model: gpt-4o
    response_mode: "integrated"  # Existing response mode
    streaming_config:            # NEW: Native streaming config
      enabled: true
      mode: "real_time"
      chunk_size: "word"
      buffer_timeout: 50
    system_prompt: |
      You are a helpful assistant optimized for real-time conversations.
      Provide clear, concise responses that work well with streaming.
'''
    print(agents_yaml)
    
    print("2. agents.yaml - Content Generation Agent:")
    content_yaml = '''
  - id: content_generator
    type: openai  
    model: gpt-4o-mini
    streaming_config:
      enabled: true
      mode: "immediate"
      chunk_size: "sentence"
      buffer_timeout: 100
    system_prompt: |
      You are a content generation assistant.
      Create well-structured content with clear sentence breaks.
'''
    print(content_yaml)
    
    print("3. agents.yaml - Claude Fallback Agent:")
    claude_yaml = '''
  - id: claude_assistant
    type: anthropic
    model: claude-3-5-sonnet-20241022
    streaming_config:
      enabled: true  # Will use client-side simulation
      mode: "immediate"
      chunk_size: "word"
      fallback_mode: "immediate"
    system_prompt: |
      You are Claude, optimized for simulated streaming.
      Your responses will be chunked client-side for consistent UX.
'''
    print(claude_yaml)
    
    print("4. workflows.yaml - Streaming Workflow:")
    workflow_yaml = '''
workflows:
  main_workflow:
    - id: streaming_conversation
      steps:
        - id: streaming_response
          agent: realtime_assistant
          input: ${context.user_input}
          streaming:               # Workflow-level streaming config  
            enabled: true
            mode: "real_time"
          output:
            to: user
'''
    print(workflow_yaml)


def simulate_streaming_chat():
    """Demo: Simulate a streaming chat session"""
    print("💬 DEMO: Simulated Streaming Chat Session")
    print("=" * 50)
    
    print("Simulating real-time streaming for different providers...\n")
    
    # Simulate different response types
    responses = [
        ("OpenAI GPT-4o", "Hello! I'm an AI assistant powered by OpenAI. How can I help you today?"),
        ("Claude 3.5", "Hi there! I'm Claude, created by Anthropic. I'm here to assist you with any questions."),
        ("Gemini 2.0", "Greetings! I'm Gemini from Google. What would you like to explore together?")
    ]
    
    for provider, response in responses:
        print(f"🤖 {provider} (streaming):")
        print("   ", end="", flush=True)
        
        # Simulate word-by-word streaming
        words = response.split()
        for i, word in enumerate(words):
            print(word, end="", flush=True)
            if i < len(words) - 1:
                print(" ", end="", flush=True)
            time.sleep(0.1)  # Simulate network delay
        
        print()  # New line after complete response
        print()


def demo_integration_examples():
    """Demo: Integration with existing LangSwarm features"""
    print("🔗 DEMO: Integration Examples")
    print("=" * 50)
    
    print("1. Streaming + Structured Responses:")
    structured_example = '''
# Stream chunks that eventually form structured JSON
Chunk 1: '{"response": "I\\'ll '
Chunk 2: 'check that file '
Chunk 3: 'for you", "mcp": '
Chunk 4: '{"tool": "filesystem", '
Chunk 5: '"method": "read_file", '
Chunk 6: '"params": {"path": "/tmp/config.json"}}}'

# Final aggregated response:
{
  "response": "I'll check that file for you",
  "mcp": {
    "tool": "filesystem",
    "method": "read_file", 
    "params": {"path": "/tmp/config.json"}
  }
}
'''
    print(structured_example)
    
    print("2. Streaming + Tool Calling:")
    tool_example = '''
# Native tool calling with streaming
Agent streams: "I'll help you search for that information..."
Tool executes: search_web(query="LangSwarm features")
Final response: "Based on my search, LangSwarm offers..."

# User sees immediate feedback, then complete result
'''
    print(tool_example)
    
    print("3. Streaming + Response Modes:")
    modes_example = '''
# Streaming Mode (new native streaming)
stream_chunks = agent.chat_stream("Hello")
for chunk in stream_chunks:
    print(chunk["content"], end="", flush=True)

# Integrated Mode (existing behavior)  
response = agent.chat("Hello")  # Complete response at once
print(response)

# Legacy Streaming Mode (immediate + tool results)
# Shows immediate response, then tool execution separately
'''
    print(modes_example)


def demo_performance_benefits():
    """Demo: Performance benefits of streaming"""
    print("⚡ DEMO: Performance Benefits")
    print("=" * 50)
    
    benefits = [
        {
            "metric": "Time to First Token (TTFT)",
            "traditional": "2-5 seconds",
            "streaming": "200-500ms",
            "improvement": "4-10x faster"
        },
        {
            "metric": "Perceived Response Time",
            "traditional": "Full response delay",
            "streaming": "Immediate feedback", 
            "improvement": "Instant engagement"
        },
        {
            "metric": "User Experience",
            "traditional": "Loading spinner",
            "streaming": "Real-time conversation",
            "improvement": "Natural interaction"
        },
        {
            "metric": "Resource Usage",
            "traditional": "Buffer full response",
            "streaming": "Process incrementally",
            "improvement": "Lower memory usage"
        }
    ]
    
    print("Metric                    | Traditional      | Streaming         | Improvement")
    print("-" * 80)
    
    for benefit in benefits:
        print(f"{benefit['metric']:<25} | {benefit['traditional']:<16} | {benefit['streaming']:<17} | {benefit['improvement']}")
    
    print()


def demo_error_handling():
    """Demo: Error handling and fallback mechanisms"""
    print("🛡️  DEMO: Error Handling & Fallbacks")
    print("=" * 50)
    
    print("1. Model Without Native Streaming:")
    print("   Model: claude-3-5-sonnet-20241022")
    print("   Behavior: Automatically falls back to client-side simulation")
    print("   Result: Consistent streaming UX across all models")
    print()
    
    print("2. Network Error During Streaming:")
    print("   Error: Connection timeout after 3 chunks")
    print("   Fallback: Return partial response + error metadata")
    print("   Recovery: Resume from last successful chunk")
    print()
    
    print("3. Streaming Configuration Disabled:")
    print("   Config: {'streaming': {'enabled': False}}")
    print("   Behavior: Use traditional non-streaming mode")
    print("   Benefit: Backward compatibility maintained")
    print()
    
    print("4. Provider-Specific Error:")
    print("   OpenAI: Rate limit → Switch to fallback mode")
    print("   Claude: No streaming → Client-side simulation")
    print("   Gemini: WebSocket fail → HTTP streaming fallback")
    print()


def main():
    """Run all streaming demonstrations"""
    print("🚀 LangSwarm Priority 3: Native Streaming Support Demo")
    print("=" * 60)
    print()
    
    demos = [
        demo_streaming_capability_detection,
        demo_streaming_configuration, 
        demo_streaming_parameters,
        demo_stream_chunk_parsing,
        demo_configuration_scenarios,
        demo_agent_configuration,
        simulate_streaming_chat,
        demo_integration_examples,
        demo_performance_benefits,
        demo_error_handling
    ]
    
    for i, demo_func in enumerate(demos, 1):
        print(f"Demo {i}/{len(demos)}: {demo_func.__doc__.split(':')[1].strip()}")
        demo_func()
        
        if i < len(demos):
            print("\n" + "─" * 60 + "\n")
    
    print()
    print("🎉 Priority 3 Native Streaming Demo Complete!")
    print("=" * 60)
    print()
    print("📋 Key Features Demonstrated:")
    print("   ✅ Native streaming support for OpenAI, Gemini, Mistral, Cohere")
    print("   ✅ Client-side streaming simulation for Claude and other models")
    print("   ✅ Configurable streaming modes and parameters")
    print("   ✅ Stream chunk parsing and aggregation") 
    print("   ✅ Integration with structured responses and tool calling")
    print("   ✅ Comprehensive error handling and fallbacks")
    print("   ✅ Backward compatibility with existing features")
    print("   ✅ Performance benefits and improved user experience")
    print()
    print("🔧 Next Steps:")
    print("   1. Configure streaming in your agents.yaml")
    print("   2. Use chat_stream() for real-time streaming")
    print("   3. Set streaming configs in workflows.yaml")
    print("   4. Test with different models and fallbacks")
    print()
    print("📚 Learn More:")
    print("   • Check tests/core/wrappers/test_native_streaming.py")
    print("   • Review langswarm/core/wrappers/util_mixin.py")
    print("   • See example_mcp_config/ for configuration examples")


if __name__ == "__main__":
    main() 