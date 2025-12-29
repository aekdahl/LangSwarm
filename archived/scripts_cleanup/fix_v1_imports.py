#!/usr/bin/env python3
"""
Automated script to fix V1 imports after moving archived/v1 to langswarm/v1

Changes:
  from langswarm.core.X → from langswarm.v1.core.X
  from langswarm.memory.X → from langswarm.v1.memory.X
  from langswarm.synapse.X → from langswarm.v1.synapse.X
  from langswarm.mcp.X → from langswarm.v1.mcp.X
  from langswarm.tools.X → from langswarm.v1.tools.X
  from langswarm.ui.X → from langswarm.v1.ui.X
"""

import os
import re
from pathlib import Path

# Directories to process
V1_DIR = Path("langswarm/v1")

# Import patterns to fix
PATTERNS = [
    # from langswarm.core.X → from langswarm.v1.core.X
    (r'from langswarm\.core\.', 'from langswarm.v1.core.'),
    # from langswarm.memory.X → from langswarm.v1.memory.X
    (r'from langswarm\.memory\.', 'from langswarm.v1.memory.'),
    # from langswarm.synapse.X → from langswarm.v1.synapse.X
    (r'from langswarm\.synapse\.', 'from langswarm.v1.synapse.'),
    # from langswarm.mcp.X → from langswarm.v1.mcp.X
    (r'from langswarm\.mcp\.', 'from langswarm.v1.mcp.'),
    # from langswarm.tools.X → from langswarm.v1.tools.X
    (r'from langswarm\.tools\.', 'from langswarm.v1.tools.'),
    # from langswarm.ui.X → from langswarm.v1.ui.X
    (r'from langswarm\.ui\.', 'from langswarm.v1.ui.'),
    # from langswarm.api.X → from langswarm.v1.api.X
    (r'from langswarm\.api\.', 'from langswarm.v1.api.'),
    # from langswarm.cli.X → from langswarm.v1.cli.X
    (r'from langswarm\.cli\.', 'from langswarm.v1.cli.'),
    # from langswarm.features.X → from langswarm.v1.features.X
    (r'from langswarm\.features\.', 'from langswarm.v1.features.'),
    # from langswarm.intelligent_navigation.X → from langswarm.v1.intelligent_navigation.X
    (r'from langswarm\.intelligent_navigation\.', 'from langswarm.v1.intelligent_navigation.'),
    
    # import langswarm.core.X → import langswarm.v1.core.X (less common but handle it)
    (r'import langswarm\.core\.', 'import langswarm.v1.core.'),
    (r'import langswarm\.memory\.', 'import langswarm.v1.memory.'),
    (r'import langswarm\.synapse\.', 'import langswarm.v1.synapse.'),
    (r'import langswarm\.mcp\.', 'import langswarm.v1.mcp.'),
]

def fix_file(filepath):
    """Fix imports in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Apply each pattern
        for pattern, replacement in PATTERNS:
            if re.search(pattern, content):
                matches = re.findall(pattern + r'[\w.]+', content)
                content = re.sub(pattern, replacement, content)
                if matches:
                    changes_made.extend(matches[:3])  # Show first 3 matches
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        
        return False, []
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False, []

def main():
    """Process all Python files in V1 directory"""
    print(f"Fixing imports in {V1_DIR}...")
    print("-" * 60)
    
    total_files = 0
    modified_files = 0
    
    # Walk through all Python files
    for filepath in V1_DIR.rglob("*.py"):
        total_files += 1
        modified, changes = fix_file(filepath)
        
        if modified:
            modified_files += 1
            rel_path = filepath.relative_to(V1_DIR)
            print(f"✅ {rel_path}")
            if changes:
                for change in changes[:2]:  # Show first 2 changes
                    print(f"   - {change}")
    
    print("-" * 60)
    print(f"✅ Done! Modified {modified_files} of {total_files} files")

if __name__ == "__main__":
    main()

