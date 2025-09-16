#!/usr/bin/env python3
"""
Quick LangSwarm Installation Verification Script
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Success")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
        else:
            print("❌ Failed")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚀 LangSwarm Installation Verification")
    print("="*50)
    
    # Check if we're in the right directory
    if not os.path.exists('pyproject.toml'):
        print("❌ pyproject.toml not found. Please run this from the LangSwarm root directory.")
        return
    
    # Check pip version
    run_command("pip --version", "Checking pip version")
    
    # Check current LangSwarm installation
    run_command("pip show langswarm", "Checking current LangSwarm installation")
    
    # Uninstall existing version
    print("\n🗑️  Uninstalling existing LangSwarm...")
    run_command("pip uninstall langswarm -y", "Uninstalling LangSwarm")
    
    # Install in development mode
    print("\n📦 Installing LangSwarm in development mode...")
    success = run_command("pip install -e .", "Installing LangSwarm from source")
    
    if success:
        # Verify installation
        run_command("pip show langswarm", "Verifying new installation")
        
        # Test import
        print("\n🧪 Testing import...")
        try:
            import langswarm
            print("✅ LangSwarm import successful")
            print(f"📍 Location: {langswarm.__file__}")
        except ImportError as e:
            print(f"❌ Import failed: {e}")
    
    print("\n" + "="*50)
    print("✅ Installation verification completed")
    print("🔧 Run: python diagnostic_script.py to test BigQuery functionality")

if __name__ == "__main__":
    main()
