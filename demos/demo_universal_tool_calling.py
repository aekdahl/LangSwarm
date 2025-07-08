#!/usr/bin/env python3
"""
Demo: Priority 2 - Universal Tool Calling (Native + MCP)

This demo showcases how LangSwarm's universal tool calling system works:
1. LLMs can use either native tool calls OR MCP format
2. Both get translated to our internal MCP format
3. Our middleware processes all tool calls universally

This makes LangSwarm compatible with:
- OpenAI native function calling
- Claude tool use
- Gemini function calling  
- Mistral function calling
- Cohere function calling
- Plus our existing MCP format

The result: Universal tool calling across all providers!
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langswarm.core.wrappers.generic import AgentWrapper
from unittest.mock import Mock
import json

def demo_header(title):
    """Print a formatted demo section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def demo_section(title):
    """Print a formatted demo subsection"""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")

def main():
    print("🚀 LangSwarm Priority 2: Universal Tool Calling Demo")
    print("Making tool calling universal across all AI providers!")
    
    # Sample tools in LangSwarm MCP format
    sample_tools = [
        {
            "tool": "weather_api",
            "description": "Get current weather information for any location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string", 
                        "description": "City name or coordinates"
                    },
                    "units": {
                        "type": "string", 
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature units"
                    }
                },
                "required": ["location"]
            }
        },
        {
            "tool": "code_executor",
            "description": "Execute Python code and return results",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    },
                    "language": {
                        "type": "string",
                        "default": "python"
                    }
                },
                "required": ["code"]
            }
        }
    ]
    
    # Create mock tool registry
    mock_tool_registry = Mock()
    mock_tool_registry.get_tools.return_value = sample_tools
    
    # Create mock agent
    mock_agent = Mock()
    
    demo_header("1. Model Capability Detection")
    
    print("Testing which models support native tool calling...")
    
    test_models = [
        ("gpt-4", "OpenAI GPT-4"),
        ("gpt-4.1", "OpenAI GPT-4.1"),
        ("claude-3-opus", "Anthropic Claude 3 Opus"),
        ("claude-4-sonnet", "Anthropic Claude 4 Sonnet"),
        ("gemini-1.5-pro", "Google Gemini 1.5 Pro"),
        ("gemini-2.5-flash", "Google Gemini 2.5 Flash"),
        ("mistral-large", "Mistral Large"),
        ("magistral-medium", "Mistral Magistral Medium"),
        ("command-r", "Cohere Command R"),
        ("llama-3", "Meta Llama 3 (unsupported)"),
        ("deepseek-r1", "DeepSeek R1 (unsupported)")
    ]
    
    for model_id, model_name in test_models:
        wrapper = AgentWrapper(
            name="test_agent",
            agent=mock_agent,
            model=model_id,
            tool_registry=mock_tool_registry
        )
        
        supports = wrapper.supports_native_tool_calling()
        status = "✅ Supported" if supports else "❌ Not supported"
        print(f"  {model_name}: {status}")
    
    demo_header("2. Native Tool Format Conversion")
    
    print("Converting MCP tools to native formats for different providers...")
    
    # Test OpenAI format conversion
    demo_section("OpenAI Function Calling Format")
    openai_wrapper = AgentWrapper(
        name="openai_agent", 
        agent=mock_agent, 
        model="gpt-4",
        tool_registry=mock_tool_registry
    )
    
    openai_tools = openai_wrapper.get_native_tool_format_schema(sample_tools)
    print("MCP Tools → OpenAI Format:")
    print(json.dumps(openai_tools[0], indent=2))
    
    # Test Claude format conversion
    demo_section("Anthropic Claude Tool Use Format")
    claude_wrapper = AgentWrapper(
        name="claude_agent",
        agent=mock_agent,
        model="claude-3-opus", 
        tool_registry=mock_tool_registry
    )
    
    claude_tools = claude_wrapper._convert_to_anthropic_tools(sample_tools)
    print("MCP Tools → Claude Format:")
    print(json.dumps(claude_tools[0], indent=2))
    
    # Test Gemini format conversion
    demo_section("Google Gemini Function Calling Format")
    gemini_wrapper = AgentWrapper(
        name="gemini_agent",
        agent=mock_agent,
        model="gemini-1.5-pro",
        tool_registry=mock_tool_registry
    )
    
    gemini_tools = gemini_wrapper._convert_to_gemini_tools(sample_tools)
    print("MCP Tools → Gemini Format:")
    print(json.dumps(gemini_tools[0], indent=2))
    
    demo_header("3. Native Tool Call Translation to MCP")
    
    print("Demonstrating how native tool calls from different providers")
    print("get translated back to our universal MCP format...")
    
    # Test OpenAI → MCP translation
    demo_section("OpenAI Function Call → MCP Translation")
    
    # Mock OpenAI response with function call
    mock_openai_response = Mock()
    mock_openai_response.choices = [Mock()]
    mock_openai_response.choices[0].message = Mock()
    mock_openai_response.choices[0].message.content = "I'll get the current weather for you."
    mock_openai_response.choices[0].message.tool_calls = [Mock()]
    mock_openai_response.choices[0].message.tool_calls[0].function = Mock()
    mock_openai_response.choices[0].message.tool_calls[0].function.name = "weather_api"
    mock_openai_response.choices[0].message.tool_calls[0].function.arguments = '{"location": "New York", "units": "celsius"}'
    
    print("Original OpenAI Function Call:")
    print(f"  Function: {mock_openai_response.choices[0].message.tool_calls[0].function.name}")
    print(f"  Arguments: {mock_openai_response.choices[0].message.tool_calls[0].function.arguments}")
    
    mcp_result = openai_wrapper._translate_openai_to_mcp(mock_openai_response)
    print("\nTranslated to Universal MCP Format:")
    print(json.dumps(mcp_result, indent=2))
    
    # Test Claude → MCP translation  
    demo_section("Claude Tool Use → MCP Translation")
    
    # Mock Claude response with tool use
    mock_claude_response = Mock()
    mock_claude_response.text = "Let me execute that code for you."
    mock_claude_response.content = [Mock()]
    mock_claude_response.content[0].type = "tool_use"
    mock_claude_response.content[0].name = "code_executor"
    mock_claude_response.content[0].input = {
        "code": "print('Hello, Universal Tool Calling!')",
        "language": "python"
    }
    
    print("Original Claude Tool Use:")
    print(f"  Tool: {mock_claude_response.content[0].name}")
    print(f"  Input: {mock_claude_response.content[0].input}")
    
    mcp_result = claude_wrapper._translate_anthropic_to_mcp(mock_claude_response)
    print("\nTranslated to Universal MCP Format:")
    print(json.dumps(mcp_result, indent=2))
    
    # Test Gemini → MCP translation
    demo_section("Gemini Function Call → MCP Translation")
    
    # Mock Gemini response with function call
    mock_gemini_response = Mock()
    mock_gemini_response.text = "I'll check the weather for that location."
    mock_gemini_response.candidates = [Mock()]
    mock_gemini_response.candidates[0].content = Mock()
    mock_gemini_response.candidates[0].content.parts = [Mock()]
    mock_gemini_response.candidates[0].content.parts[0].function_call = Mock()
    mock_gemini_response.candidates[0].content.parts[0].function_call.name = "weather_api"
    mock_gemini_response.candidates[0].content.parts[0].function_call.args = {
        "location": "San Francisco",
        "units": "fahrenheit"
    }
    
    print("Original Gemini Function Call:")
    print(f"  Function: {mock_gemini_response.candidates[0].content.parts[0].function_call.name}")
    print(f"  Args: {dict(mock_gemini_response.candidates[0].content.parts[0].function_call.args)}")
    
    mcp_result = gemini_wrapper._translate_gemini_to_mcp(mock_gemini_response)
    print("\nTranslated to Universal MCP Format:")
    print(json.dumps(mcp_result, indent=2))
    
    demo_header("4. Universal Processing Benefits")
    
    print("🎯 Key Benefits of Universal Tool Calling:")
    print()
    print("✅ Provider Agnostic:")
    print("   • LLMs can use their native tool calling format")
    print("   • All get processed by the same middleware")
    print("   • No need to change existing tool implementations")
    print()
    print("✅ Backward Compatible:")
    print("   • Existing MCP format continues to work")
    print("   • Legacy agents remain functional")
    print("   • Gradual migration path available")
    print()
    print("✅ Developer Friendly:")
    print("   • Write tools once, work with all providers")
    print("   • Consistent debugging and logging")
    print("   • Unified error handling")
    print()
    print("✅ Future Proof:")
    print("   • Easy to add new providers")
    print("   • Translation layer handles format differences") 
    print("   • Central tool registry for all models")
    
    demo_header("5. Integration Flow")
    
    print("How Universal Tool Calling works in practice:")
    print()
    print("1. 🤖 LLM generates response (native format OR MCP)")
    print("2. 🔄 Translation layer detects the format")
    print("3. 📝 Native calls → converted to MCP format")
    print("4. ⚙️  Middleware processes all calls universally")
    print("5. 📤 Tool execution results returned to LLM")
    print("6. ✨ Final response delivered to user")
    print()
    print("The magic? Your tools work with ANY provider!")
    print("Whether it's OpenAI, Claude, Gemini, Mistral, or Cohere!")
    
    demo_header("Summary: Priority 2 Complete! 🎉")
    
    print("Universal Tool Calling is now implemented:")
    print()
    print("🔧 IMPLEMENTED FEATURES:")
    print("  ✅ Model capability detection")
    print("  ✅ MCP → Native format conversion (5 providers)")
    print("  ✅ Native → MCP translation layer") 
    print("  ✅ Universal middleware processing")
    print("  ✅ Comprehensive error handling")
    print("  ✅ Full backward compatibility")
    print()
    print("🚀 RESULT:")
    print("  LLMs can now use EITHER:")
    print("    • Their native tool calling format, OR")
    print("    • LangSwarm's MCP format")
    print("  Both get processed by our middleware universally!")
    print()
    print("Next up: Priority 3 - Streaming Response Improvements! 🌊")

if __name__ == "__main__":
    main() 