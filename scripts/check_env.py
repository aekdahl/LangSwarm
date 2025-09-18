#!/usr/bin/env python3
"""
Environment Variables Checker
=============================

Simple script to check if the .env file exists and if OPENAI_API_KEY is available.
"""

import os
from pathlib import Path

def main():
    print("🔍 Environment Variables Check")
    print("=================================")
    
    # Check if .env file exists
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file exists")
        
        # Try to load the .env file
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print("✅ python-dotenv loaded .env file")
        except ImportError:
            print("⚠️  python-dotenv not installed - run: pip install python-dotenv")
    else:
        print("❌ .env file missing")
    
    # Check if OPENAI_API_KEY is available
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        masked_key = f"...{api_key[-8:]}" if len(api_key) > 8 else "***"
        print(f"✅ OPENAI_API_KEY found: {masked_key}")
    else:
        print("❌ OPENAI_API_KEY missing")
    
    print()
    if env_file.exists() and api_key:
        print("🎉 Environment setup is ready!")
    else:
        print("💡 Run 'make setup' to configure your environment")

if __name__ == "__main__":
    main()
