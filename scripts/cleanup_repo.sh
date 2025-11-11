#!/bin/bash

echo "Cleaning up LangSwarm repository..."
echo "----------------------------------------"

# Create directories
mkdir -p scripts
mkdir -p test_artifacts
mkdir -p archived/demos

# Move utility scripts to scripts/
echo "📁 Moving utility scripts..."
mv fix_v1_imports.py scripts/ 2>/dev/null && echo "  ✅ fix_v1_imports.py → scripts/"
mv organize_docs.sh scripts/ 2>/dev/null && echo "  ✅ organize_docs.sh → scripts/"
mv llm_friendly_setup.py scripts/ 2>/dev/null && echo "  ✅ llm_friendly_setup.py → scripts/"

# Move demo files to archived/demos
echo "📁 Moving demo files to archived..."
mv demo_*.py archived/demos/ 2>/dev/null && echo "  ✅ demo_*.py → archived/demos/"
mv simple_e2e_demo.py archived/demos/ 2>/dev/null && echo "  ✅ simple_e2e_demo.py → archived/demos/"
mv example_working.py archived/demos/ 2>/dev/null && echo "  ✅ example_working.py → archived/demos/"
mv simple_working_example.py archived/demos/ 2>/dev/null && echo "  ✅ simple_working_example.py → archived/demos/"
mv minimal_example.py archived/demos/ 2>/dev/null && echo "  ✅ minimal_example.py → archived/demos/"
mv orchestration_mvp.py archived/demos/ 2>/dev/null && echo "  ✅ orchestration_mvp.py → archived/demos/"

# Move test files to tests/ (if not already there)
echo "📁 Moving test files..."
mv test_better_errors.py tests/ 2>/dev/null && echo "  ✅ test_better_errors.py → tests/"
mv test_clean_installation.py tests/ 2>/dev/null && echo "  ✅ test_clean_installation.py → tests/"
mv test_comprehensive_error_handling.py tests/ 2>/dev/null && echo "  ✅ test_comprehensive_error_handling.py → tests/"
mv test_mvp_*.py tests/ 2>/dev/null && echo "  ✅ test_mvp_*.py → tests/"
mv test_optional_dependencies.py tests/ 2>/dev/null && echo "  ✅ test_optional_dependencies.py → tests/"
mv test_orchestration_errors.py tests/ 2>/dev/null && echo "  ✅ test_orchestration_errors.py → tests/"
mv langswarm_structure_test.py tests/ 2>/dev/null && echo "  ✅ langswarm_structure_test.py → tests/"
mv simple_langswarm_test.py tests/ 2>/dev/null && echo "  ✅ simple_langswarm_test.py → tests/"

# Move databases and logs to test_artifacts
echo "📁 Moving test artifacts..."
mv *.db test_artifacts/ 2>/dev/null && echo "  ✅ *.db → test_artifacts/"
mv *.log test_artifacts/ 2>/dev/null && echo "  ✅ *.log → test_artifacts/"

# Remove temp config files
echo "🗑️  Removing temporary config files..."
rm -f demo_config_with_errors.yaml 2>/dev/null && echo "  ✅ Removed demo_config_with_errors.yaml"

echo "----------------------------------------"
echo "✅ Cleanup complete!"
