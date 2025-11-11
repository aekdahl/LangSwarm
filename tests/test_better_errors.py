#!/usr/bin/env python3
"""
Test script to demonstrate improved error messages in LangSwarm.

This script intentionally creates various configuration errors to show
how the enhanced error messages help users fix issues quickly.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from langswarm.core.config import ConfigurationLoader
from langswarm.core.config.error_helpers import ConfigErrorHelper
from langswarm.core.errors import ConfigurationError


def test_missing_config_file():
    """Test error message when config file is not found."""
    print("\n" + "="*60)
    print("TEST 1: Missing Configuration File")
    print("="*60)
    
    try:
        loader = ConfigurationLoader()
        config = loader.load("non_existent_file.yaml")
    except ConfigurationError as e:
        print(f"\n{e}")
        print("\n✅ Clear error message with helpful suggestions!")


def test_yaml_syntax_error():
    """Test error message for YAML syntax errors."""
    print("\n" + "="*60)
    print("TEST 2: YAML Syntax Error")
    print("="*60)
    
    # Create a temporary YAML file with syntax error
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
version: "2.0"
agents:
  - id: "assistant"
    provider: openai  # Missing quotes
    model: gpt-3.5-turbo
    system_prompt: "You are helpful  # Unclosed quote
""")
        temp_file = f.name
    
    try:
        loader = ConfigurationLoader()
        config = loader.load(temp_file)
    except ConfigurationError as e:
        print(f"\n{e}")
        print("\n✅ Clear YAML error with line information!")
    finally:
        os.unlink(temp_file)


def test_missing_api_key():
    """Test error message for missing API keys."""
    print("\n" + "="*60)
    print("TEST 3: Missing API Key")
    print("="*60)
    
    # Create a config that requires an API key
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
version: "2.0"
agents:
  - id: "assistant"
    provider: "openai"
    model: "gpt-3.5-turbo"
    system_prompt: "You are a helpful assistant"
""")
        temp_file = f.name
    
    # Temporarily remove API key if set
    old_key = os.environ.pop('OPENAI_API_KEY', None)
    
    try:
        loader = ConfigurationLoader()
        config = loader.load(temp_file)
    except ConfigurationError as e:
        print(f"\n{e}")
        print("\n✅ Helpful API key setup instructions!")
    finally:
        if old_key:
            os.environ['OPENAI_API_KEY'] = old_key
        os.unlink(temp_file)


def test_invalid_model():
    """Test error message for invalid model selection."""
    print("\n" + "="*60)
    print("TEST 4: Invalid Model for Provider")
    print("="*60)
    
    error = ConfigErrorHelper.invalid_model(
        "openai",
        "gpt-5-ultra",  # Non-existent model
        ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
    )
    print(f"\n{error}")
    print("\n✅ Shows valid model options!")


def test_missing_env_variable():
    """Test error message for missing environment variables."""
    print("\n" + "="*60)
    print("TEST 5: Missing Environment Variable")
    print("="*60)
    
    # Create a config with environment variable
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
version: "2.0"
database:
  url: "${DATABASE_URL}"
agents:
  - id: "assistant"
    provider: "openai"
    api_key: "${OPENAI_API_KEY:test-key}"
""")
        temp_file = f.name
    
    try:
        loader = ConfigurationLoader()
        config = loader.load(temp_file)
    except ConfigurationError as e:
        print(f"\n{e}")
        print("\n✅ Clear environment variable error with examples!")
    finally:
        os.unlink(temp_file)


def test_invalid_reference():
    """Test error message for invalid references."""
    print("\n" + "="*60)
    print("TEST 6: Invalid Tool Reference")
    print("="*60)
    
    error = ConfigErrorHelper.invalid_reference(
        "tool",
        "file_system",  # Typo - should be "filesystem"
        ["filesystem", "web_request", "sql_database", "text_processor"]
    )
    print(f"\n{error}")
    print("\n✅ Suggests similar options!")


def test_workflow_syntax_error():
    """Test error message for workflow syntax errors."""
    print("\n" + "="*60)
    print("TEST 7: Workflow Syntax Error")
    print("="*60)
    
    error = ConfigErrorHelper.workflow_syntax_error(
        "my_workflow",
        "agent1 > agent2 > user",  # Wrong operator
        "Invalid operator '>' (use '->' instead)"
    )
    print(f"\n{error}")
    print("\n✅ Shows workflow syntax examples!")


def test_memory_config_error():
    """Test error message for memory configuration issues."""
    print("\n" + "="*60)
    print("TEST 8: Memory Configuration Error")
    print("="*60)
    
    error = ConfigErrorHelper.invalid_memory_config(
        "redis",
        "Redis server not running on localhost:6379"
    )
    print(f"\n{error}")
    print("\n✅ Provides memory backend requirements!")


def main():
    """Run all error message tests."""
    print("🧪 LangSwarm Enhanced Error Messages Demo")
    print("=========================================")
    print("This demo shows how improved error messages help users")
    print("quickly identify and fix configuration issues.")
    
    tests = [
        test_missing_config_file,
        test_yaml_syntax_error,
        test_missing_api_key,
        test_invalid_model,
        test_missing_env_variable,
        test_invalid_reference,
        test_workflow_syntax_error,
        test_memory_config_error
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n❌ Test failed with unexpected error: {e}")
    
    print("\n" + "="*60)
    print("✅ All error message demonstrations complete!")
    print("="*60)
    print("\nKey improvements:")
    print("• Clear, actionable error messages")
    print("• Helpful suggestions for fixing issues")
    print("• Examples and documentation links")
    print("• Context about what went wrong")
    print("• Similar option suggestions for typos")


if __name__ == "__main__":
    main()