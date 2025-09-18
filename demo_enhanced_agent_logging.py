#!/usr/bin/env python3
"""
Demo script showing the enhanced agent configuration logging.
This demonstrates the difference between old and new logging formats.

Usage:
    python demo_enhanced_agent_logging.py

This script loads a test agent configuration and shows the difference
between the old minimal logging format and the new enhanced format
that captures comprehensive agent configuration details.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from langswarm.core.debug.integration import serialize_agent_config
from langswarm.core.config import LangSwarmConfigLoader

def demo_enhanced_agent_logging():
    """Demo the enhanced agent logging functionality"""
    
    # Set API key for testing
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not found in environment")
        print("💡 Setting a dummy API key for testing purposes")
        os.environ['OPENAI_API_KEY'] = 'sk-dummy-key-for-testing'
    
    print("🚀 Enhanced Agent Configuration Logging Demo")
    print("=" * 60)
    
    try:
        # Load the bigquery debug configuration
        config_file = "langswarm/core/debug/test_configs/bigquery_debug.yaml"
        print(f"📂 Loading configuration from: {config_file}")
        
        loader = LangSwarmConfigLoader(config_path=config_file)
        loader.load()
        
        print(f"✅ Configuration loaded successfully")
        print(f"🤖 Found {len(loader.agents)} agents")
        
        # Get the agent
        if 'bigquery_test_agent' in loader.agents:
            agent = loader.agents['bigquery_test_agent']
            
            print("\n" + "=" * 60)
            print("📊 OLD LOGGING FORMAT (before enhancement):")
            print("=" * 60)
            
            # Show old format
            old_format = {
                "agent_name": getattr(agent, 'name', None),
                "agent_type": type(agent).__name__,
                "agent_id_attr": getattr(agent, 'agent_id', None),
                "agent_id_attr_alt": getattr(agent, 'id', None),
                "has_name_attr": hasattr(agent, 'name'),
                "name_value": getattr(agent, 'name', 'MISSING'),
                "agent_repr": repr(agent)[:200]
            }
            
            print(json.dumps(old_format, indent=2))
            
            print("\n" + "=" * 60)
            print("🚀 NEW ENHANCED LOGGING FORMAT (after enhancement):")
            print("=" * 60)
            
            # Show new enhanced format
            enhanced_format = serialize_agent_config(agent)
            print(json.dumps(enhanced_format, indent=2))
            
            print("\n" + "=" * 60)
            print("📈 ENHANCEMENT SUMMARY:")
            print("=" * 60)
            print("✅ The enhanced logging now includes:")
            print("   • Complete model configuration details")
            print("   • Memory configuration and current state") 
            print("   • Tool registry information with tool counts and names")
            print("   • Session management settings")
            print("   • Agent-specific settings (timeouts, limits, etc.)")
            print("   • Plugin and RAG configuration status")
            print("   • Complete system prompt (full content for debugging dynamic injection)")
            print("   • Safe serialization with circular reference protection")
            
            print(f"\n🔍 Data size comparison:")
            print(f"   Old format: {len(json.dumps(old_format))} characters")
            print(f"   New format: {len(json.dumps(enhanced_format))} characters")
            print(f"   Enhancement factor: {len(json.dumps(enhanced_format)) / len(json.dumps(old_format)):.1f}x more detailed")
            
        else:
            print("❌ Agent 'bigquery_test_agent' not found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_enhanced_agent_logging()
    exit(0 if success else 1)
