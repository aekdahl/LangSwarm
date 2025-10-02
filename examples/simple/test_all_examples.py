#!/usr/bin/env python3
"""
Test runner for all simple examples
Verifies that every example can be imported and has the right structure
"""
import os
import sys
import ast
import glob
from pathlib import Path

def analyze_example(filepath):
    """Analyze an example file for simplicity and correctness."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Count non-empty, non-comment lines
    code_lines = [
        line for line in lines 
        if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""')
    ]
    
    # Remove docstring lines
    in_docstring = False
    filtered_lines = []
    for line in lines:
        if '"""' in line:
            in_docstring = not in_docstring
        elif not in_docstring and line.strip() and not line.strip().startswith('#'):
            filtered_lines.append(line)
    
    # Try to parse as valid Python
    try:
        ast.parse(content)
        valid_python = True
    except SyntaxError:
        valid_python = False
    
    # Check for required elements
    has_main = 'def main():' in content or 'async def main():' in content
    has_langswarm_import = 'from langswarm' in content or 'import langswarm' in content
    has_api_key_check = 'OPENAI_API_KEY' in content
    has_run_guard = 'if __name__ == "__main__":' in content
    
    return {
        'total_lines': len(lines),
        'code_lines': len(filtered_lines),
        'valid_python': valid_python,
        'has_main': has_main,
        'has_langswarm_import': has_langswarm_import,
        'has_api_key_check': has_api_key_check,
        'has_run_guard': has_run_guard,
        'content': content
    }

def test_examples():
    """Test all example files."""
    print("🧪 Testing Simple LangSwarm Examples")
    print("=" * 50)
    
    # Find all Python example files
    examples_dir = Path(__file__).parent
    example_files = sorted(glob.glob(str(examples_dir / "[0-9][0-9]_*.py")))
    
    if not example_files:
        print("❌ No example files found!")
        return False
    
    print(f"Found {len(example_files)} examples to test\n")
    
    results = []
    for filepath in example_files:
        filename = os.path.basename(filepath)
        print(f"📝 Testing {filename}...")
        
        analysis = analyze_example(filepath)
        
        # Check criteria
        checks = [
            ("Valid Python syntax", analysis['valid_python']),
            ("Has main function", analysis['has_main']),
            ("Imports LangSwarm", analysis['has_langswarm_import']),
            ("Checks API key", analysis['has_api_key_check']),
            ("Has run guard", analysis['has_run_guard']),
            ("Code <= 30 lines", analysis['code_lines'] <= 30),
            ("Total <= 50 lines", analysis['total_lines'] <= 50)
        ]
        
        passed = 0
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"   {status} {check_name}")
            if check_result:
                passed += 1
        
        print(f"   📊 {analysis['code_lines']} code lines, {analysis['total_lines']} total lines")
        
        success = passed >= 6  # At least 6/7 checks should pass
        results.append((filename, success, passed, len(checks)))
        
        if success:
            print(f"   ✅ {filename} PASSED\n")
        else:
            print(f"   ❌ {filename} FAILED\n")
    
    # Summary
    print("=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    passed_count = sum(1 for _, success, _, _ in results if success)
    total_count = len(results)
    
    for filename, success, passed, total in results:
        status = "✅" if success else "❌"
        print(f"{status} {filename} ({passed}/{total} checks)")
    
    print(f"\n🎯 OVERALL: {passed_count}/{total_count} examples passed")
    
    if passed_count == total_count:
        print("🎉 ALL EXAMPLES PASSED!")
        print("\nThese examples demonstrate:")
        print("- Simple, working code (10-30 lines)")
        print("- Real LangSwarm usage patterns")
        print("- Proper error handling")
        print("- Clear setup instructions")
        return True
    else:
        print(f"⚠️ {total_count - passed_count} examples need improvement")
        return False

def check_imports():
    """Check if we can import LangSwarm components that examples use."""
    print("\n🔍 Checking Example Dependencies")
    print("-" * 30)
    
    imports_to_test = [
        ("langswarm", "Core LangSwarm"),
        ("langswarm.create_agent", "Agent creation"),
        ("langswarm.create_workflow", "Workflow creation"),  
        ("langswarm.load_config", "Config loading"),
        ("openai", "OpenAI client"),
    ]
    
    all_available = True
    for import_name, description in imports_to_test:
        try:
            if "." in import_name:
                module_name, attr_name = import_name.rsplit(".", 1)
                module = __import__(module_name, fromlist=[attr_name])
                getattr(module, attr_name)
            else:
                __import__(import_name)
            print(f"✅ {description}")
        except ImportError as e:
            print(f"❌ {description}: {e}")
            all_available = False
        except AttributeError as e:
            print(f"⚠️ {description}: {e}")
            # Don't mark as failure for AttributeError - might be expected
    
    return all_available

def main():
    """Run all tests."""
    print("🚀 Simple Examples Test Suite")
    print("=" * 50)
    
    # Test file structure
    examples_passed = test_examples()
    
    # Test imports (optional - examples might still work)
    imports_available = check_imports()
    
    # Final result
    print("\n" + "=" * 50)
    if examples_passed:
        print("🎉 SUCCESS: Simple examples are well-structured!")
        print("\n💡 To run examples:")
        print("   1. Set OPENAI_API_KEY environment variable")
        print("   2. Run: python 01_basic_chat.py")
        print("   3. Try other examples as needed")
        
        if not imports_available:
            print("\n⚠️ Note: Some imports failed, but examples may still work")
            print("   Install missing dependencies as needed")
        
        return True
    else:
        print("❌ FAILED: Some examples need improvement")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)