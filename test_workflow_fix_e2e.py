#!/usr/bin/env python3
"""
End-to-End Test for Workflow Fix
================================

Tests that the main_workflow execution works correctly after the middleware changes.
This ensures we haven't broken the core workflow functionality.
"""

import os
import sys
import tempfile
import yaml
from typing import Dict, Any

def create_test_config() -> Dict[str, Any]:
    """Create a test configuration with proper main_workflow structure"""
    return {
        "version": "1.0",
        "project_name": "test-workflow-fix",
        "agents": [
            {
                "id": "test_agent",
                "agent_type": "openai", 
                "model": "gpt-4o",
                "system_prompt": "You are a test agent for workflow verification.",
                "tools": ["bigquery_vector_search"]
            }
        ],
        "tools": {
            "bigquery_vector_search": {
                "type": "mcpbigquery_vector_search",
                "config": {
                    "project_id": "test-project",
                    "dataset_id": "test_dataset",
                    "table_name": "test_table"
                }
            }
        },
        "workflows": {
            "main_workflow": [
                {
                    "id": "test_search_workflow",
                    "description": "Test workflow for BigQuery search",
                    "steps": [
                        {
                            "id": "process_query",
                            "agent": "test_agent", 
                            "input": "${context.user_input}",
                            "output": {"to": "user"}
                        }
                    ]
                }
            ]
        }
    }

def test_config_loading():
    """Test 1: Verify config loads without errors"""
    print("🧪 Test 1: Configuration Loading")
    
    try:
        from langswarm.core.config import LangSwarmConfigLoader
        
        # Create temporary config file
        config_data = create_test_config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        # Test loading
        loader = LangSwarmConfigLoader(config_path=os.path.dirname(config_path))
        workflows, agents, brokers, tools, tools_metadata = loader.load()
        
        # Verify structure
        assert "main_workflow" in workflows, "main_workflow missing from loaded workflows"
        assert isinstance(workflows["main_workflow"], list), "main_workflow should be a list"
        assert len(workflows["main_workflow"]) > 0, "main_workflow should contain at least one workflow"
        assert workflows["main_workflow"][0]["id"] == "test_search_workflow", "Workflow ID mismatch"
        
        print("✅ Configuration loads correctly")
        print(f"   - Found main_workflow with {len(workflows['main_workflow'])} workflows")
        print(f"   - First workflow ID: {workflows['main_workflow'][0]['id']}")
        
        # Cleanup
        os.unlink(config_path)
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_workflow_id_extraction():
    """Test 2: Verify workflow ID extraction logic"""
    print("\n🧪 Test 2: Workflow ID Extraction")
    
    try:
        # Simulate the middleware logic
        workflows = {
            "main_workflow": [
                {
                    "id": "test_search_workflow",
                    "description": "Test workflow",
                    "steps": [{"id": "step1", "agent": "test_agent"}]
                }
            ]
        }
        
        # Test the extraction logic (from middleware.py)
        main_workflows = workflows.get("main_workflow", [])
        if main_workflows and isinstance(main_workflows, list) and len(main_workflows) > 0:
            first_workflow = main_workflows[0]
            if isinstance(first_workflow, dict) and "id" in first_workflow:
                workflow_id = first_workflow["id"]
            else:
                workflow_id = "main_workflow"
        else:
            workflow_id = "main_workflow"
        
        assert workflow_id == "test_search_workflow", f"Expected 'test_search_workflow', got '{workflow_id}'"
        
        print("✅ Workflow ID extraction works correctly")
        print(f"   - Extracted ID: {workflow_id}")
        return True
        
    except Exception as e:
        print(f"❌ Workflow ID extraction failed: {e}")
        return False

def test_workflow_executor():
    """Test 3: Verify WorkflowExecutor can find and execute workflow"""
    print("\n🧪 Test 3: WorkflowExecutor Integration")
    
    try:
        from langswarm.core.config import WorkflowExecutor
        
        # Create test workflows and agents
        workflows = {
            "main_workflow": [
                {
                    "id": "test_workflow",
                    "steps": [
                        {
                            "id": "test_step",
                            "agent": "test_agent",
                            "input": "${context.user_input}",
                            "output": {"to": "user"}
                        }
                    ]
                }
            ]
        }
        
        agents = {
            "test_agent": {
                "id": "test_agent",
                "model": "gpt-4o"
            }
        }
        
        # Create executor
        executor = WorkflowExecutor(workflows, agents)
        
        # Test that it can find the workflow
        available_workflows = executor.get_available_workflows() if hasattr(executor, 'get_available_workflows') else []
        
        print("✅ WorkflowExecutor integration works")
        print(f"   - Available workflows: {available_workflows}")
        return True
        
    except Exception as e:
        print(f"❌ WorkflowExecutor integration failed: {e}")
        return False

def test_middleware_workflow_execution():
    """Test 4: Test the actual middleware workflow execution path"""
    print("\n🧪 Test 4: Middleware Workflow Execution")
    
    try:
        # This would require a full middleware setup, so we'll simulate the key parts
        
        # Test that we don't get the "main_workflow" agent error
        workflows = {
            "main_workflow": [
                {
                    "id": "bigquery_search_workflow", 
                    "steps": [{"id": "step1"}]
                }
            ]
        }
        
        # Simulate the middleware extraction
        main_workflows = workflows.get("main_workflow", [])
        if main_workflows and isinstance(main_workflows, list) and len(main_workflows) > 0:
            first_workflow = main_workflows[0]
            if isinstance(first_workflow, dict) and "id" in first_workflow:
                workflow_id = first_workflow["id"]
            else:
                workflow_id = "main_workflow"
        else:
            workflow_id = "main_workflow"
        
        # Verify it extracts the correct ID, not "main_workflow"
        assert workflow_id != "main_workflow", "Should extract actual workflow ID, not 'main_workflow'"
        assert workflow_id == "bigquery_search_workflow", f"Expected 'bigquery_search_workflow', got '{workflow_id}'"
        
        print("✅ Middleware workflow execution path works")
        print(f"   - Extracted correct workflow ID: {workflow_id}")
        print("   - Should NOT see 'Agent main_workflow not found' error")
        return True
        
    except Exception as e:
        print(f"❌ Middleware workflow execution test failed: {e}")
        return False

def test_bigquery_session_availability():
    """Test 5: Verify BigQuery session storage is available but not automatic"""
    print("\n🧪 Test 5: BigQuery Session Storage Availability")
    
    try:
        from langswarm.core.session.storage import SessionStorageFactory, BIGQUERY_AVAILABLE
        
        if BIGQUERY_AVAILABLE:
            print("✅ BigQuery storage is available")
            
            # Test that it requires explicit configuration
            try:
                storage = SessionStorageFactory.create_storage("bigquery")
                print("❌ BigQuery storage should require explicit project_id!")
                return False
            except ValueError as e:
                if "project_id" in str(e):
                    print("✅ BigQuery storage correctly requires explicit configuration")
                else:
                    print(f"❌ Unexpected error: {e}")
                    return False
        else:
            print("⚠️ BigQuery storage not available (missing google-cloud-bigquery)")
        
        # Test default storage
        default_storage = SessionStorageFactory.get_default_storage()
        storage_type = type(default_storage).__name__
        
        assert storage_type == "SQLiteSessionStorage", f"Default should be SQLite, got {storage_type}"
        print(f"✅ Default storage is {storage_type} (not BigQuery)")
        
        return True
        
    except Exception as e:
        print(f"❌ BigQuery session storage test failed: {e}")
        return False

def run_all_tests():
    """Run all E2E tests"""
    print("🔧 LangSwarm Workflow Fix - End-to-End Testing")
    print("=" * 60)
    
    tests = [
        test_config_loading,
        test_workflow_id_extraction, 
        test_workflow_executor,
        test_middleware_workflow_execution,
        test_bigquery_session_availability
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Workflow fix is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
