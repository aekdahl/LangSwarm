#!/usr/bin/env python3
"""
LangSwarm Interactive Workflow Demo
===================================

This script demonstrates the new interactive workflow system.
Run this to see how the make commands work in practice.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and show its output"""
    print(f"\n{'='*60}")
    print(f"🎯 {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings/Errors: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    print("""
🚀 LangSwarm Interactive Workflow System Demo
==============================================

This demo shows the new make commands for interactive workflow management.
""")
    
    # Demo commands
    demos = [
        ("make help", "Show all available make commands"),
        ("make list-workflows", "Discover and list all available workflows"), 
        ("echo 'q' | make run-workflow", "Launch interactive workflow runner (quit immediately)")
    ]
    
    print("\n📋 Available Demos:")
    for i, (cmd, desc) in enumerate(demos, 1):
        print(f"  {i}. {desc}")
    
    print(f"\n🎮 Interactive Commands You Can Try:")
    print("  • make run-workflow      - Full interactive experience")
    print("  • make debug-workflow    - Run with debug tracing")
    print("  • make create-workflow   - AI-powered workflow creation")
    print("  • make setup             - Environment setup")
    
    choice = input(f"\nSelect demo to run (1-{len(demos)}, or 'all'): ").strip().lower()
    
    if choice == 'all':
        print("\n🚀 Running all demos...")
        for cmd, desc in demos:
            if not run_command(cmd, desc):
                print(f"❌ Demo failed: {desc}")
                break
            input("\nPress Enter to continue to next demo...")
    elif choice.isdigit() and 1 <= int(choice) <= len(demos):
        cmd, desc = demos[int(choice) - 1]
        run_command(cmd, desc)
    else:
        print("❌ Invalid choice")
        return
    
    print(f"""
🎉 Demo Complete!

🎯 Next Steps:
1. Run 'make run-workflow' for the full interactive experience
2. Try 'make create-workflow' to generate workflows with AI
3. Use 'make debug-workflow' for development and troubleshooting

📚 Documentation:
• docs/interactive-workflow-system.md - Complete guide
• examples/ - 77 discovered workflow examples
• make help - All available commands

Happy workflow orchestration! 🚀
""")

if __name__ == "__main__":
    main()
