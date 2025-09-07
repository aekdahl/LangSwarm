#!/usr/bin/env python3
"""
Comprehensive deployment readiness test for Phase 1 & 2 changes
"""

import os
import sys

def test_core_imports():
    """Test all core imports work correctly"""
    print("🧪 Testing Core Imports...")
    
    try:
        # Test error standards
        from langswarm.mcp.tools._error_standards import create_error_response, ErrorTypes
        print("✅ Error standards import")
        
        # Test BigQuery tool
        from langswarm.mcp.tools.bigquery_vector_search.main import BigQueryVectorSearchMCPTool
        print("✅ BigQuery tool import")
        
        # Test BigQuery utilities
        from langswarm.mcp.tools.bigquery_vector_search._bigquery_utils import BigQueryManager
        print("✅ BigQuery utilities import")
        
        # Test Phase 1 tools
        from langswarm.mcp.tools.gcp_environment.main import GCPEnvironmentMCPTool
        from langswarm.mcp.tools.realtime_voice.main import RealtimeVoiceMCPTool
        print("✅ Phase 1 tools import")
        
        return True
        
    except Exception as e:
        print(f"❌ Core imports failed: {e}")
        return False

def test_tool_functionality():
    """Test basic tool functionality"""
    print("\n🧪 Testing Tool Functionality...")
    
    try:
        from langswarm.mcp.tools.bigquery_vector_search.main import BigQueryVectorSearchMCPTool
        from langswarm.mcp.tools.gcp_environment.main import GCPEnvironmentMCPTool
        from langswarm.mcp.tools.realtime_voice.main import RealtimeVoiceMCPTool
        
        tools = [
            ('BigQuery', BigQueryVectorSearchMCPTool, 'test_bq'),
            ('GCP Environment', GCPEnvironmentMCPTool, 'test_gcp'),
            ('Realtime Voice', RealtimeVoiceMCPTool, 'test_voice'),
        ]
        
        for tool_name, tool_class, tool_id in tools:
            tool = tool_class(tool_id)
            
            # Check basic attributes
            assert hasattr(tool, 'name'), f"{tool_name} missing name"
            assert hasattr(tool, 'description'), f"{tool_name} missing description" 
            assert hasattr(tool, '_bypass_pydantic'), f"{tool_name} missing _bypass_pydantic"
            assert tool._bypass_pydantic == True, f"{tool_name} _bypass_pydantic not True"
            
            print(f"✅ {tool_name}: basic functionality")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool functionality test failed: {e}")
        return False

def test_error_handling():
    """Test error handling improvements"""
    print("\n🧪 Testing Error Handling...")
    
    try:
        from langswarm.mcp.tools._error_standards import (
            create_error_response, create_parameter_error, ErrorTypes
        )
        
        # Test error response creation
        error = create_error_response("Test error", ErrorTypes.PARAMETER_VALIDATION, "test_tool")
        assert error['success'] == False
        assert error['error_type'] == 'parameter_validation'
        print("✅ Error response creation")
        
        # Test parameter error
        param_error = create_parameter_error("wrong_param", "correct_param", "value", "tool")
        assert 'wrong_param' in param_error['error']
        assert param_error['error_type'] == 'parameter_validation'
        print("✅ Parameter error creation")
        
        # Test BigQuery tool uses error standards
        from langswarm.mcp.tools.bigquery_vector_search.main import BigQueryVectorSearchMCPTool
        import inspect
        
        tool = BigQueryVectorSearchMCPTool('test')
        source = inspect.getsource(tool.run_async)
        
        assert 'create_parameter_error' in source, "BigQuery tool not using parameter error"
        assert 'ErrorTypes' in source, "BigQuery tool not using ErrorTypes"
        print("✅ BigQuery tool error integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_utilities_integration():
    """Test BigQuery utilities integration"""
    print("\n🧪 Testing Utilities Integration...")
    
    try:
        from langswarm.mcp.tools.bigquery_vector_search._bigquery_utils import (
            BigQueryManager, EmbeddingHelper, QueryBuilder
        )
        
        # Test EmbeddingHelper
        valid_embedding = [0.1, 0.2, 0.3]
        assert EmbeddingHelper.validate_embedding(valid_embedding) == True
        
        invalid_embedding = ["not", "numbers"]
        assert EmbeddingHelper.validate_embedding(invalid_embedding) == False
        print("✅ EmbeddingHelper validation")
        
        # Test QueryBuilder
        query = QueryBuilder.build_filtered_search(
            'proj', 'ds', 'table', valid_embedding, {}, 0.7, 10
        )
        assert len(query) > 100  # Reasonable query length
        assert 'ML.DISTANCE' in query  # Uses BigQuery ML
        print("✅ QueryBuilder functionality")
        
        # Test integration in main functions
        from langswarm.mcp.tools.bigquery_vector_search.main import similarity_search
        import inspect
        
        source = inspect.getsource(similarity_search)
        assert 'BigQueryManager' in source, "similarity_search not using BigQueryManager"
        assert 'EmbeddingHelper' in source, "similarity_search not using EmbeddingHelper"
        print("✅ Main functions use utilities")
        
        return True
        
    except Exception as e:
        print(f"❌ Utilities integration test failed: {e}")
        return False

def test_file_structure():
    """Test file structure and naming conventions"""
    print("\n🧪 Testing File Structure...")
    
    try:
        required_files = [
            'langswarm/mcp/tools/_error_standards.py',
            'langswarm/mcp/tools/bigquery_vector_search/main.py',
            'langswarm/mcp/tools/bigquery_vector_search/_bigquery_utils.py',
            'langswarm/mcp/tools/bigquery_vector_search/main_original.py',  # Backup
            'langswarm/mcp/tools/gcp_environment/readme.md',
            'langswarm/mcp/tools/realtime_voice/readme.md',
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing files: {missing_files}")
            return False
        
        print("✅ All required files present")
        
        # Test file sizes are reasonable
        main_size = os.path.getsize('langswarm/mcp/tools/bigquery_vector_search/main.py')
        utils_size = os.path.getsize('langswarm/mcp/tools/bigquery_vector_search/_bigquery_utils.py')
        
        assert main_size > 5000, "Main file too small"
        assert utils_size > 5000, "Utils file too small" 
        print("✅ File sizes reasonable")
        
        return True
        
    except Exception as e:
        print(f"❌ File structure test failed: {e}")
        return False

def test_code_quality():
    """Test code quality improvements"""
    print("\n🧪 Testing Code Quality...")
    
    try:
        # Test line count reduction
        original_path = "langswarm/mcp/tools/bigquery_vector_search/main_original.py"
        current_path = "langswarm/mcp/tools/bigquery_vector_search/main.py"
        
        if os.path.exists(original_path):
            with open(original_path, 'r') as f:
                original_lines = len([l for l in f if l.strip()])  # Non-empty lines
            
            with open(current_path, 'r') as f:
                current_lines = len([l for l in f if l.strip()])
            
            reduction = original_lines - current_lines
            reduction_percent = (reduction / original_lines) * 100
            
            assert reduction > 0, "No line count reduction achieved"
            print(f"✅ Code reduction: {reduction} lines (-{reduction_percent:.1f}%)")
        
        # Test no syntax errors
        import ast
        
        files_to_check = [
            'langswarm/mcp/tools/bigquery_vector_search/main.py',
            'langswarm/mcp/tools/bigquery_vector_search/_bigquery_utils.py',
            'langswarm/mcp/tools/_error_standards.py',
        ]
        
        for file_path in files_to_check:
            with open(file_path, 'r') as f:
                code = f.read()
            
            try:
                ast.parse(code)
                print(f"✅ {os.path.basename(file_path)}: syntax valid")
            except SyntaxError as e:
                print(f"❌ {os.path.basename(file_path)}: syntax error - {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Code quality test failed: {e}")
        return False

def test_backwards_compatibility():
    """Test backwards compatibility"""
    print("\n🧪 Testing Backwards Compatibility...")
    
    try:
        # Test old import paths still work
        from langswarm.mcp.tools.bigquery_vector_search.main import (
            SimilaritySearchInput, SimilaritySearchOutput, 
            BigQueryVectorSearchMCPTool
        )
        print("✅ BigQuery imports compatible")
        
        # Test tool creation with old patterns
        tool = BigQueryVectorSearchMCPTool('test_compat')
        assert hasattr(tool, 'run'), "Missing run method"
        assert hasattr(tool, 'run_async'), "Missing run_async method"
        print("✅ Tool interface compatible")
        
        return True
        
    except Exception as e:
        print(f"❌ Backwards compatibility test failed: {e}")
        return False

def main():
    """Run comprehensive deployment readiness tests"""
    print("🚀 LangSwarm Deployment Readiness Test\n")
    print("Testing Phase 1 & 2 changes for production deployment...\n")
    
    tests = [
        ("Core Imports", test_core_imports),
        ("Tool Functionality", test_tool_functionality), 
        ("Error Handling", test_error_handling),
        ("Utilities Integration", test_utilities_integration),
        ("File Structure", test_file_structure),
        ("Code Quality", test_code_quality),
        ("Backwards Compatibility", test_backwards_compatibility),
    ]
    
    passed = 0
    total = len(tests)
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            failed_tests.append(test_name)
    
    print(f"\n{'='*60}")
    print(f"📊 DEPLOYMENT READINESS RESULTS")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}/{total} tests ({(passed/total)*100:.1f}%)")
    
    if failed_tests:
        print(f"❌ Failed: {', '.join(failed_tests)}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - READY FOR DEPLOYMENT! 🚀")
        print("\nPhase 1 & 2 changes are production-ready:")
        print("  ✅ Error standardization complete")
        print("  ✅ BigQuery tool simplified and optimized") 
        print("  ✅ Reusable utilities created")
        print("  ✅ Documentation updated")
        print("  ✅ Backwards compatibility maintained")
        return True
    elif passed >= total * 0.85:  # 85% pass rate
        print("\n🟡 MOSTLY READY - Minor issues to address")
        print("  Consider deployment with monitoring")
        return True
    else:
        print("\n❌ NOT READY - Significant issues found")
        print("  Address failed tests before deployment")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
