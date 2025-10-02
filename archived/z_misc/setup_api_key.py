#!/usr/bin/env python3
"""
Helper script to easily set API keys and run LangSwarm debug tests.

This script provides an interactive way to set API keys and run test cases
without having to manually export environment variables.
"""

import os
import asyncio
import sys
from pathlib import Path


def set_api_key_interactive():
    """Interactively set the OpenAI API key"""
    current_key = os.environ.get('OPENAI_API_KEY')
    
    if current_key:
        print(f"✅ OPENAI_API_KEY is already set (ends with: ...{current_key[-8:]})")
        use_existing = input("Use existing key? (y/n): ").lower().strip()
        if use_existing in ['y', 'yes', '']:
            return current_key
    
    print("\n🔑 Please enter your OpenAI API key:")
    print("   (You can find this at https://platform.openai.com/api-keys)")
    
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return None
    
    if not api_key.startswith('sk-'):
        print("⚠️  Warning: OpenAI API keys typically start with 'sk-'")
        continue_anyway = input("Continue anyway? (y/n): ").lower().strip()
        if continue_anyway not in ['y', 'yes']:
            return None
    
    # Set the environment variable for this session
    os.environ['OPENAI_API_KEY'] = api_key
    print("✅ API key set for this session")
    
    return api_key


def save_to_env_file(api_key):
    """Save API key to .env file for future use"""
    env_file = Path('.env')
    
    if env_file.exists():
        print(f"📄 .env file already exists")
        overwrite = input("Update the .env file? (y/n): ").lower().strip()
        if overwrite not in ['y', 'yes']:
            return
    
    try:
        with open('.env', 'w') as f:
            f.write(f"# LangSwarm Environment Variables\n")
            f.write(f"OPENAI_API_KEY={api_key}\n")
            f.write(f"\n# Optional: Other API keys\n")
            f.write(f"# ANTHROPIC_API_KEY=your-anthropic-key\n")
            f.write(f"# COHERE_API_KEY=your-cohere-key\n")
        
        print(f"✅ API key saved to .env file")
        print(f"💡 You can load it in future sessions with: source .env")
        
    except Exception as e:
        print(f"❌ Failed to save .env file: {e}")


async def run_test_cases():
    """Run the debug test cases"""
    try:
        from langswarm.core.debug import run_case_1, run_all_basic_cases
        
        print("\n🧪 Choose test case to run:")
        print("1. Run Case 1 only (Simple Agent)")
        print("2. Run all basic cases (1, 2, 3)")
        print("3. Skip tests")
        
        choice = input("Choice (1-3): ").strip()
        
        if choice == '1':
            print("\n🚀 Running Case 1: Simple Agent")
            result = await run_case_1()
            print(f"\n📊 Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
            if result.error_message:
                print(f"Error: {result.error_message}")
            
        elif choice == '2':
            print("\n🚀 Running all basic test cases")
            results = await run_all_basic_cases()
            passed = sum(1 for r in results if r.success)
            print(f"\n📊 Summary: {passed}/{len(results)} tests passed")
            
        elif choice == '3':
            print("✅ Skipping tests")
            
        else:
            print("❌ Invalid choice")
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")


def show_usage_options():
    """Show different ways to use the API key"""
    print("\n📚 Ways to use your API key:")
    print("=" * 50)
    
    print("🔧 Option 1: Export in terminal")
    print("   export OPENAI_API_KEY='your-key-here'")
    print("   python -m langswarm.core.debug.cli run-case-1")
    
    print("\n🔧 Option 2: One-line command")
    print("   OPENAI_API_KEY='your-key-here' python -m langswarm.core.debug.cli run-case-1")
    
    print("\n🔧 Option 3: Use this helper script")
    print("   python setup_api_key.py")
    
    print("\n🔧 Option 4: Load from .env file")
    print("   source .env  # if you saved to .env")
    print("   python -m langswarm.core.debug.cli run-case-1")


async def main():
    """Main interactive setup"""
    print("🎯 LangSwarm API Key Setup & Test Runner")
    print("=" * 50)
    
    # Check current status
    current_key = os.environ.get('OPENAI_API_KEY')
    if current_key:
        print(f"✅ OPENAI_API_KEY is currently set")
        print(f"   Key ends with: ...{current_key[-8:]}")
    else:
        print("❌ OPENAI_API_KEY is not set")
    
    # Set API key
    api_key = set_api_key_interactive()
    
    if not api_key:
        print("\n❌ No API key configured. Exiting.")
        show_usage_options()
        return
    
    # Offer to save to .env file
    save_env = input("\n💾 Save API key to .env file for future use? (y/n): ").lower().strip()
    if save_env in ['y', 'yes']:
        save_to_env_file(api_key)
    
    # Run tests
    await run_test_cases()
    
    print("\n🎉 Setup complete!")
    print("💡 Your API key is now set for this terminal session.")
    print("💡 Run 'python -m langswarm.core.debug.cli run-case-1' to test anytime.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
