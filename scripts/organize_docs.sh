#!/bin/bash

# V1 Documentation
mv V1_*.md docs/v1/ 2>/dev/null
mv README_V1_USERS.md docs/v1/ 2>/dev/null
mv langswarm_v1_monkey_patch.py docs/v1/ 2>/dev/null

# Planning/V2 Documentation
mv HIERARCHICAL_PLANNING_COMPLETE.md docs/planning/ 2>/dev/null
mv RETROSPECTIVE_VALIDATION_COMPLETE.md docs/planning/ 2>/dev/null
mv PLANNING_SYSTEM_COMPLETE.md docs/planning/ 2>/dev/null
mv PHASE_1_2_DETAILED_PLAN.md docs/planning/ 2>/dev/null

# Release Notes
mv RELEASE_NOTES_*.md docs/releases/ 2>/dev/null
mv CHANGELOG.md docs/releases/ 2>/dev/null
mv PACKAGE_READY_SUMMARY.md docs/releases/ 2>/dev/null
mv PYPI_PACKAGE_COMPLETE.md docs/releases/ 2>/dev/null

# Installation & Setup Guides
mv QUICK_START*.md docs/guides/ 2>/dev/null
mv INSTALLATION_*.md docs/guides/ 2>/dev/null
mv SIMPLIFIED_INSTALLATION_STRATEGY.md docs/guides/ 2>/dev/null
mv CLEAN_INSTALLATION_STRATEGY.md docs/guides/ 2>/dev/null
mv SETUP_IMPROVEMENTS_SUMMARY.md docs/guides/ 2>/dev/null
mv UPDATED_INSTALLATION_SUMMARY.md docs/guides/ 2>/dev/null
mv SIMPLE_EXAMPLES_COMPLETE.md docs/guides/ 2>/dev/null

# Configuration & Features
mv CONFIGURATION_SIMPLIFICATION_SUMMARY.md docs/guides/ 2>/dev/null
mv IMPROVED_ERROR_MESSAGES_SUMMARY.md docs/guides/ 2>/dev/null
mv OPTIONAL_DEPENDENCIES_IMPLEMENTATION.md docs/guides/ 2>/dev/null
mv FINAL_CLEAN_DEPENDENCIES_SUMMARY.md docs/guides/ 2>/dev/null

# Archive old status/summary files
mkdir -p docs/archive
mv *_SUMMARY.md docs/archive/ 2>/dev/null
mv *_COMPLETE.md docs/archive/ 2>/dev/null
mv STATUS.md docs/archive/ 2>/dev/null
mv FINAL_STATUS.md docs/archive/ 2>/dev/null
mv IMPLEMENTATION_SUMMARY.md docs/archive/ 2>/dev/null
mv CLEANUP_COMPLETE.md docs/archive/ 2>/dev/null
mv STRUCTURE_MIGRATION_COMPLETE.md docs/archive/ 2>/dev/null
mv V2_REMOVAL_SUMMARY.md docs/archive/ 2>/dev/null
mv UPDATED_LANGSWARM_ANALYSIS_REPORT.md docs/archive/ 2>/dev/null
mv NEXT_PHASE_IMPROVEMENT_PLAN.md docs/archive/ 2>/dev/null
mv IMMEDIATE_ACTION_PLAN.md docs/archive/ 2>/dev/null
mv AGENTMEM_FINAL_SUMMARY.md docs/archive/ 2>/dev/null
mv PHASE_1B_COMPLETE*.md docs/archive/ 2>/dev/null

# Keep in root
# README.md - main readme
# MVP.md - current roadmap
# FIXME.md - current issues
# LICENSE - license file

echo "✅ Documentation organized!"
