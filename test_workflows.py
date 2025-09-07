#!/usr/bin/env python3
"""
Test workflow functionality for Phase 1 & 2 changes
"""

import os
import yaml

def test_bigquery_workflow_structure():
    """Test BigQuery workflow YAML structure"""
    print("🧪 Testing BigQuery Workflow Structure...")
    
    try:
        workflow_path = "langswarm/mcp/tools/bigquery_vector_search/workflows.yaml"
        
        if not os.path.exists(workflow_path):
            print("❌ BigQuery workflows.yaml not found")
            return False
        
        with open(workflow_path, 'r') as f:
            workflows = yaml.safe_load(f)
        
        print("✅ BigQuery workflows.yaml loaded successfully")
        
        # Check workflow structure
        if 'workflows' in workflows:
            workflow_names = list(workflows['workflows'].keys())
            print(f"   Available workflows: {workflow_names}")
            
            # Check for key workflows
            expected_workflows = ['similarity_search', 'knowledge_retrieval']
            found_workflows = [w for w in expected_workflows if w in workflow_names]
            print(f"   Expected workflows found: {found_workflows}")
            
            return len(found_workflows) > 0
        else:
            print("❌ No workflows section found")
            return False
            
    except Exception as e:
        print(f"❌ BigQuery workflow test failed: {e}")
        return False

def test_workflow_schemas():
    """Test workflow schemas and documentation"""
    print("\n🧪 Testing Workflow Schemas...")
    
    try:
        # Test BigQuery workflow schemas
        workflow_path = "langswarm/mcp/tools/bigquery_vector_search/workflows.yaml"
        
        with open(workflow_path, 'r') as f:
            workflows = yaml.safe_load(f)
        
        if 'workflows' not in workflows:
            print("❌ No workflows section")
            return False
        
        workflow_count = 0
        valid_workflows = 0
        
        for workflow_name, workflow_config in workflows['workflows'].items():
            workflow_count += 1
            
            # Check required fields
            required_fields = ['description', 'steps']
            has_required = all(field in workflow_config for field in required_fields)
            
            if has_required:
                valid_workflows += 1
                print(f"✅ {workflow_name}: valid structure")
                
                # Check if steps use BigQuery tool
                steps = workflow_config.get('steps', [])
                uses_bigquery = any(
                    step.get('tool') in ['bigquery_vector_search', 'mcpbigquery_vector_search'] 
                    for step in steps if isinstance(step, dict)
                )
                
                if uses_bigquery:
                    print(f"   └─ Uses BigQuery tool: ✅")
                else:
                    print(f"   └─ Uses BigQuery tool: ❌")
            else:
                print(f"❌ {workflow_name}: missing required fields")
        
        print(f"\n   Valid workflows: {valid_workflows}/{workflow_count}")
        return valid_workflows > 0
        
    except Exception as e:
        print(f"❌ Workflow schema test failed: {e}")
        return False

def test_template_documentation():
    """Test template.md files for Phase 1 tools"""
    print("\n🧪 Testing Template Documentation...")
    
    tools_to_check = [
        'bigquery_vector_search',
        'gcp_environment',
        'mcpgithubtool',
        'tasklist'
    ]
    
    passed = 0
    total = len(tools_to_check)
    
    for tool_name in tools_to_check:
        try:
            template_path = f"langswarm/mcp/tools/{tool_name}/template.md"
            
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    content = f.read()
                
                # Check for key sections
                has_usage = 'usage' in content.lower() or 'example' in content.lower()
                has_description = len(content) > 100  # Reasonable content length
                
                if has_usage and has_description:
                    print(f"✅ {tool_name}: template.md complete")
                    passed += 1
                else:
                    print(f"❌ {tool_name}: template.md incomplete")
            else:
                print(f"❌ {tool_name}: template.md missing")
                
        except Exception as e:
            print(f"❌ {tool_name}: template check failed - {e}")
    
    print(f"\n   Template docs: {passed}/{total} complete")
    return passed >= total * 0.8  # 80% success rate acceptable

def test_readme_documentation():
    """Test readme.md files for Phase 1 tools"""
    print("\n🧪 Testing README Documentation...")
    
    tools_to_check = [
        'bigquery_vector_search',
        'gcp_environment', 
        'realtime_voice',
        'mcpgithubtool',
        'tasklist'
    ]
    
    passed = 0
    total = len(tools_to_check)
    
    for tool_name in tools_to_check:
        try:
            readme_path = f"langswarm/mcp/tools/{tool_name}/readme.md"
            
            if os.path.exists(readme_path):
                with open(readme_path, 'r') as f:
                    content = f.read()
                
                # Check for comprehensive content
                has_setup = 'setup' in content.lower() or 'installation' in content.lower()
                has_examples = 'example' in content.lower()
                has_comprehensive_content = len(content) > 500  # Substantial documentation
                
                if has_setup and has_examples and has_comprehensive_content:
                    print(f"✅ {tool_name}: readme.md comprehensive")
                    passed += 1
                elif len(content) > 100:
                    print(f"🟡 {tool_name}: readme.md basic")
                    passed += 0.5
                else:
                    print(f"❌ {tool_name}: readme.md minimal")
            else:
                print(f"❌ {tool_name}: readme.md missing")
                
        except Exception as e:
            print(f"❌ {tool_name}: readme check failed - {e}")
    
    print(f"\n   README docs: {passed}/{total} adequate")
    return passed >= total * 0.7  # 70% success rate acceptable

def test_phase2_improvements():
    """Test Phase 2 specific improvements"""
    print("\n🧪 Testing Phase 2 Improvements...")
    
    try:
        # Test line count reduction
        original_path = "langswarm/mcp/tools/bigquery_vector_search/main_original.py"
        current_path = "langswarm/mcp/tools/bigquery_vector_search/main.py"
        utils_path = "langswarm/mcp/tools/bigquery_vector_search/_bigquery_utils.py"
        
        if os.path.exists(original_path) and os.path.exists(current_path):
            with open(original_path, 'r') as f:
                original_lines = len(f.readlines())
            
            with open(current_path, 'r') as f:
                current_lines = len(f.readlines())
            
            reduction = original_lines - current_lines
            reduction_percent = (reduction / original_lines) * 100
            
            print(f"✅ Line count reduction: {original_lines} → {current_lines} (-{reduction} lines, -{reduction_percent:.1f}%)")
            
            # Check utilities exist
            if os.path.exists(utils_path):
                with open(utils_path, 'r') as f:
                    utils_lines = len(f.readlines())
                print(f"✅ Utilities module: {utils_lines} lines of reusable code")
                
                return reduction > 0 and utils_lines > 300
            else:
                print("❌ Utilities module missing")
                return False
        else:
            print("❌ Cannot compare - original backup not found")
            return False
            
    except Exception as e:
        print(f"❌ Phase 2 improvements test failed: {e}")
        return False

def main():
    """Run all workflow and documentation tests"""
    print("🚀 Testing LangSwarm Workflows & Documentation\n")
    
    tests = [
        test_bigquery_workflow_structure,
        test_workflow_schemas,
        test_template_documentation,
        test_readme_documentation,
        test_phase2_improvements,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Workflow & Documentation Test Results: {passed}/{total} tests passed")
    
    if passed >= total * 0.8:  # 80% success rate
        print("🎉 Workflow & documentation tests largely successful!")
        return True
    else:
        print("❌ Workflow & documentation tests need attention.")
        return False

if __name__ == "__main__":
    main()
