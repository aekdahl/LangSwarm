#!/usr/bin/env python3
"""
Fixed integration test for BigQuery tool with correct tool type names
"""

import os
import tempfile
import yaml

def test_correct_tool_types():
    """Test with correct MCP tool type names"""
    print("🧪 Testing Correct Tool Type Names...")
    
    try:
        # Create a config with correct tool type names
        test_config = {
            'agents': {
                'test_agent': {
                    'model': 'gpt-4',
                    'tools': ['mcpbigquery_vector_search', 'mcpfilesystem']
                }
            },
            'tools': {
                'mcpbigquery_vector_search': {
                    'type': 'mcpbigquery_vector_search'
                },
                'mcpfilesystem': {
                    'type': 'mcpfilesystem'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name
        
        try:
            from langswarm.core.config import LangSwarmConfigLoader
            config_loader = LangSwarmConfigLoader(config_path)
            print("✅ Config loader initialization successful")
            
            # Test loading
            result = config_loader.load()
            if result:
                agents, tools, memory_adapters, sessions, workflows = result
                print("✅ Configuration load successful")
                
                # Check tools
                print(f"   Loaded tools: {list(tools.keys()) if tools else 'None'}")
                
                # Check BigQuery tool specifically
                if tools and 'mcpbigquery_vector_search' in tools:
                    tool = tools['mcpbigquery_vector_search']
                    print(f"✅ BigQuery tool loaded: {type(tool).__name__}")
                    
                    if hasattr(tool, '_bypass_pydantic'):
                        print(f"   └─ _bypass_pydantic: {tool._bypass_pydantic}")
                    
                    # Check agents
                    if agents and 'test_agent' in agents:
                        agent = agents['test_agent']
                        print(f"✅ Test agent loaded: {type(agent).__name__}")
                        
                        # Check if agent has tools
                        if hasattr(agent, 'has_tools') and agent.has_tools():
                            print("✅ Agent has tools configured")
                        else:
                            print("❌ Agent does not have tools configured")
                    
                    return True
                else:
                    print("❌ BigQuery tool not found in loaded tools")
                    return False
            else:
                print("❌ Configuration load failed")
                return False
                
        finally:
            os.unlink(config_path)
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_available_tool_types():
    """Test what tool types are actually available"""
    print("\n🧪 Testing Available Tool Types...")
    
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        
        # Create a minimal config to trigger tool discovery
        test_config = {
            'agents': {
                'minimal_agent': {
                    'model': 'gpt-4'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name
        
        try:
            config_loader = LangSwarmConfigLoader(config_path)
            
            # This should trigger tool discovery and show available types
            result = config_loader.load()
            print("✅ Tool type discovery completed")
            return True
            
        finally:
            os.unlink(config_path)
            
    except Exception as e:
        print(f"❌ Tool type test failed: {e}")
        return False

def test_specific_tools():
    """Test specific tools with Phase 1 changes"""
    print("\n🧪 Testing Phase 1 Standardized Tools...")
    
    tools_to_test = [
        ('mcpbigquery_vector_search', 'BigQuery Vector Search'),
        ('mcpgcp_environment', 'GCP Environment'),
        ('mcpfilesystem', 'Filesystem'),
    ]
    
    passed = 0
    total = len(tools_to_test)
    
    for tool_type, tool_name in tools_to_test:
        try:
            test_config = {
                'agents': {
                    'test_agent': {
                        'model': 'gpt-4',
                        'tools': [tool_type]
                    }
                },
                'tools': {
                    tool_type: {
                        'type': tool_type
                    }
                }
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(test_config, f)
                config_path = f.name
            
            try:
                from langswarm.core.config import LangSwarmConfigLoader
                config_loader = LangSwarmConfigLoader(config_path)
                result = config_loader.load()
                
                if result:
                    agents, tools, memory_adapters, sessions, workflows = result
                    if tools and tool_type in tools:
                        tool = tools[tool_type]
                        print(f"✅ {tool_name} ({tool_type}): loaded successfully")
                        
                        # Check _bypass_pydantic for our Phase 1 tools
                        if tool_type in ['mcpbigquery_vector_search', 'mcpgcp_environment']:
                            if hasattr(tool, '_bypass_pydantic') and tool._bypass_pydantic:
                                print(f"   └─ _bypass_pydantic: ✅")
                            else:
                                print(f"   └─ _bypass_pydantic: ❌")
                        
                        passed += 1
                    else:
                        print(f"❌ {tool_name} ({tool_type}): not loaded")
                else:
                    print(f"❌ {tool_name} ({tool_type}): config load failed")
                    
            finally:
                os.unlink(config_path)
                
        except Exception as e:
            print(f"❌ {tool_name} ({tool_type}): error - {e}")
    
    print(f"\n   Tool loading: {passed}/{total} successful")
    return passed == total

if __name__ == "__main__":
    print("🚀 Testing LangSwarm Integration with Correct Tool Names\n")
    
    tests = [
        test_available_tool_types,
        test_correct_tool_types,
        test_specific_tools,
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Integration Test Results: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 All integration tests passed!")
    else:
        print("❌ Some integration tests failed.")
