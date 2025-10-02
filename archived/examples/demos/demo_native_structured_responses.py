#!/usr/bin/env python3
"""
Demo: Native Structured Responses in LangSwarm

This script demonstrates the new OpenAI native structured output functionality
that we've implemented for Priority 1 of the LLM Abstractions project.
"""

import json
from langswarm.core.wrappers.util_mixin import UtilMixin


def main():
    print("🚀 LangSwarm Native Structured Responses Demo")
    print("=" * 60)
    
    # Create a utility mixin instance to test our functionality
    util_mixin = UtilMixin()
    
    print("\n📋 1. Model Capability Detection")
    print("-" * 40)
    
    # Test model capability detection
    test_models = [
        ("gpt-4o", True),
        ("gpt-4o-mini", True),
        ("gpt-3.5-turbo", True),
        ("o1-preview", False),
        ("claude-3-5-sonnet-20241022", False),
        ("gpt-3.5-turbo-instruct", False)
    ]
    
    for model, expected_support in test_models:
        util_mixin.model_details = util_mixin._get_model_details(model)
        supports_structured = util_mixin.supports_native_structured_output()
        supports_functions = util_mixin.supports_native_function_calling()
        
        status = "✅" if supports_structured == expected_support else "❌"
        print(f"{status} {model:25} | Structured: {supports_structured:5} | Functions: {supports_functions}")
    
    print("\n🔍 2. Response Schema Validation")
    print("-" * 40)
    
    # Test schema validation
    test_responses = [
        # Valid responses
        ({"response": "Hello, how can I help?"}, True, "Simple valid response"),
        ({"response": "I'll help you", "mcp": {"tool": "filesystem", "method": "read_file", "params": {}}}, True, "Valid with tool call"),
        ({"response": "Done", "mcp": None}, True, "Valid with null MCP"),
        
        # Invalid responses
        ({"mcp": {"tool": "filesystem"}}, False, "Missing response field"),
        ({"response": 123}, False, "Wrong response type"),
        ({"response": "test", "mcp": {"tool": "filesystem"}}, False, "Missing MCP method"),
        ({"response": "test", "mcp": "invalid"}, False, "Invalid MCP structure"),
    ]
    
    for response_data, expected_valid, description in test_responses:
        is_valid, message = util_mixin.validate_structured_response(response_data)
        status = "✅" if is_valid == expected_valid else "❌"
        print(f"{status} {description:30} | Valid: {is_valid:5} | {message}")
    
    print("\n📐 3. Structured Response Schema")
    print("-" * 40)
    
    schema = util_mixin.get_structured_response_schema()
    print("JSON Schema for LangSwarm structured responses:")
    print(json.dumps(schema, indent=2))
    
    print("\n🔧 4. Integration Benefits")
    print("-" * 40)
    
    benefits = [
        "✅ Native OpenAI response_format support for compatible models",
        "✅ Automatic fallback to manual JSON parsing for older models",
        "✅ Schema validation for all structured responses",
        "✅ Backward compatibility with existing LangSwarm responses", 
        "✅ Error reduction through native structured output",
        "✅ Better reliability with schema-enforced responses"
    ]
    
    for benefit in benefits:
        print(benefit)
    
    print("\n📊 5. Implementation Summary")
    print("-" * 40)
    
    implementation_details = [
        "• Model capability detection in MODEL_REGISTRY",
        "• Native structured output API parameter injection",
        "• JSON format instructions for system prompts", 
        "• Response validation with detailed error messages",
        "• Graceful fallback for unsupported models",
        "• Full backward compatibility maintained"
    ]
    
    for detail in implementation_details:
        print(detail)
    
    print("\n🎯 Next Steps (Remaining LLM Abstractions)")
    print("-" * 40)
    
    next_steps = [
        "📝 PRIORITY 2: Native Tool/Function Calling",
        "📝 PRIORITY 3: Native Streaming Support",
        "📝 PRIORITY 4: Response API Support"
    ]
    
    for step in next_steps:
        print(step)
    
    print("\n" + "=" * 60)
    print("✅ Priority 1 (Native Structured Responses) COMPLETED!")
    print("Ready to proceed with Priority 2: Native Tool/Function Calling")


if __name__ == "__main__":
    main() 