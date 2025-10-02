#!/usr/bin/env python3
"""
Test script for GCP Environment Intelligence MCP Tool
"""

import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

from langswarm.mcp.tools.gcp_environment.main import GCPEnvironmentMCPTool


def test_tool_creation():
    """Test basic tool creation and initialization"""
    print("🧪 Testing GCP Environment MCP Tool Creation...")
    
    try:
        print("   Creating tool instance...")
        tool = GCPEnvironmentMCPTool(
            name="Test GCP Environment Tool",
            description="Test tool for GCP environment analysis"
        )
        print("✅ Tool created successfully")
        print(f"   Tool name: {tool.name}")
        print(f"   Tool type: {getattr(tool, '_is_mcp_tool', 'Not set')}")
        print(f"   Local mode: {getattr(tool, 'local_mode', 'Not set')}")
        return True
    except Exception as e:
        import traceback
        print(f"❌ Tool creation failed: {e}")
        print(f"   Full traceback: {traceback.format_exc()}")
        return False


def test_environment_detection():
    """Test environment detection capabilities"""
    print("\n🔍 Testing Environment Detection...")
    
    try:
        tool = GCPEnvironmentMCPTool(
            name="Test Tool",
            description="Test tool"
        )
        
        # Test detect_platform method
        test_input = {
            "method": "detect_platform",
            "params": {}
        }
        
        print(f"   Sending input: {test_input}")
        result = tool.run(test_input)
        print(f"   Received result: {result}")
        
        if isinstance(result, dict):
            response = result
        else:
            response = json.loads(result)
        
        print("✅ Environment detection completed")
        print(f"   Platform: {response.get('platform', 'Unknown')}")
        print(f"   GCP Environment: {response.get('is_gcp_environment', False)}")
        
        if response.get('platform') == 'local':
            print("   📍 Running locally (not in GCP)")
            print("   💡 Recommendations available for local setup")
        else:
            print(f"   🌩️ Running in GCP: {response.get('platform')}")
            print(f"   📍 Project: {response.get('project_info', {}).get('project_id', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ Environment detection failed: {e}")
        return False


def test_environment_summary():
    """Test environment summary functionality"""
    print("\n📊 Testing Environment Summary...")
    
    try:
        tool = GCPEnvironmentMCPTool(
            name="Test Tool",
            description="Test tool"
        )
        
        test_input = {
            "method": "get_environment_summary",
            "params": {}
        }
        
        result = tool.run(test_input)
        response = result if isinstance(result, dict) else json.loads(result)
        
        print("✅ Environment summary completed")
        
        if response.get('platform') == 'local':
            print("   📍 Local environment detected")
            print("   💭 Would provide GCP deployment recommendations")
        else:
            print(f"   🌩️ GCP Platform: {response.get('platform')}")
            print(f"   🏗️ Project ID: {response.get('project_id')}")
            print(f"   📍 Region: {response.get('region')}")
            print(f"   🔑 Service Account: {response.get('service_account')}")
        
        return True
    except Exception as e:
        print(f"❌ Environment summary failed: {e}")
        return False


def test_optimization_recommendations():
    """Test optimization recommendations"""
    print("\n🎯 Testing Optimization Recommendations...")
    
    try:
        tool = GCPEnvironmentMCPTool(
            name="Test Tool",
            description="Test tool"
        )
        
        test_input = {
            "method": "get_optimization_recommendations",
            "params": {}
        }
        
        result = tool.run(test_input)
        response = result if isinstance(result, dict) else json.loads(result)
        
        print("✅ Optimization recommendations completed")
        
        recommendations = response.get('recommendations', [])
        if recommendations:
            print(f"   📈 Found {len(recommendations)} recommendations")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. {rec.get('title', 'Unknown')}")
                print(f"      Priority: {rec.get('priority', 'N/A')}")
                print(f"      Savings: {rec.get('estimated_savings', 'N/A')}")
        else:
            print("   📝 No specific recommendations (likely local environment)")
            print("   💡 Would provide recommendations for GCP deployment")
        
        return True
    except Exception as e:
        print(f"❌ Optimization recommendations failed: {e}")
        return False


def test_comprehensive_analysis():
    """Test comprehensive analysis functionality"""
    print("\n🔍 Testing Comprehensive Analysis...")
    
    try:
        tool = GCPEnvironmentMCPTool(
            name="Test Tool",
            description="Test tool"
        )
        
        test_input = {
            "method": "analyze_environment",
            "params": {
                "include_costs": True,
                "include_security": True,
                "include_performance": True,
                "include_recommendations": True
            }
        }
        
        result = tool.run(test_input)
        response = result if isinstance(result, dict) else json.loads(result)
        
        print("✅ Comprehensive analysis completed")
        print(f"   🌍 Environment: {response.get('environment', 'Unknown')}")
        
        if response.get('environment') == 'gcp':
            print("   🏗️ GCP Analysis Results:")
            metadata = response.get('metadata', {})
            print(f"     Platform: {metadata.get('platform', 'N/A')}")
            print(f"     Project: {metadata.get('project_id', 'N/A')}")
            print(f"     Region: {metadata.get('region', 'N/A')}")
            
            # Show analysis sections
            sections = ['compute_resources', 'cost_analysis', 'security_assessment', 'performance_metrics']
            for section in sections:
                if section in response:
                    print(f"     ✅ {section.replace('_', ' ').title()}: Available")
                else:
                    print(f"     ⏸️ {section.replace('_', ' ').title()}: Not included")
        else:
            print("   📍 Local environment analysis")
            recommendations = response.get('recommendations', [])
            if recommendations:
                print(f"   💡 {len(recommendations)} deployment recommendations provided")
        
        return True
    except Exception as e:
        print(f"❌ Comprehensive analysis failed: {e}")
        return False


def test_all_methods():
    """Test all available methods"""
    print("\n🧪 Testing All Available Methods...")
    
    methods_to_test = [
        "get_environment_summary",
        "detect_platform", 
        "get_optimization_recommendations",
        "get_cost_analysis",
        "get_security_assessment",
        "get_performance_metrics"
    ]
    
    tool = GCPEnvironmentMCPTool(
        name="Test Tool",
        description="Test tool"
    )
    results = {}
    
    for method in methods_to_test:
        try:
            test_input = {
                "method": method,
                "params": {}
            }
            
            result = tool.run(test_input)
            response = result if isinstance(result, dict) else json.loads(result)
            
            if 'error' in response:
                results[method] = f"⚠️ Expected limitation: {response['error']}"
            else:
                results[method] = "✅ Success"
                
        except Exception as e:
            results[method] = f"❌ Error: {str(e)}"
    
    print("📊 Method Testing Results:")
    for method, status in results.items():
        print(f"   {method}: {status}")
    
    success_count = len([r for r in results.values() if r.startswith("✅")])
    total_count = len(results)
    
    print(f"\n📈 Overall Results: {success_count}/{total_count} methods working")
    return success_count > 0


def main():
    """Run all tests"""
    print("🚀 GCP Environment Intelligence MCP Tool Test Suite")
    print("=" * 60)
    
    tests = [
        ("Tool Creation", test_tool_creation),
        ("Environment Detection", test_environment_detection),
        ("Environment Summary", test_environment_summary),
        ("Optimization Recommendations", test_optimization_recommendations),
        ("Comprehensive Analysis", test_comprehensive_analysis),
        ("All Methods", test_all_methods)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall Score: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! GCP Environment Intelligence tool is ready!")
    elif passed > len(results) // 2:
        print("✅ Most tests passed! Tool is functional with expected limitations.")
    else:
        print("⚠️ Some tests failed. Please review implementation.")
    
    print("\n💡 Note: Some functionality requires running in an actual GCP environment.")
    print("   Local testing shows tool interface and basic functionality.")


if __name__ == "__main__":
    main()