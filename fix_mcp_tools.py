#!/usr/bin/env python3
"""
Batch fix script for MCP tools - fixes BaseTool compatibility issues
"""

import re
from pathlib import Path

# Tools that need fixing (based on verification output)
TOOLS_TO_FIX = [
    "gcp_environment",
    "tasklist",
    "workflow_executor",
    "daytona_environment",
    "message_queue_consumer",
    "message_queue_publisher",
    "mcpgithubtool",
    "remote",
    "sql_database",
    "bigquery_vector_search",
]

MCP_TOOLS_DIR = Path("/Users/alexanderekdahl/Docker/LangSwarm/langswarm/tools/mcp")

def fix_import(tool_path):
    """Fix the BaseTool import from synapse to tools"""
    main_py = tool_path / "main.py"
    if not main_py.exists():
        print(f"⚠️  {tool_path.name}: main.py not found")
        return False
    
    content = main_py.read_text()
    original = content
    
    # Fix import
    content = content.replace(
        "from langswarm.synapse.tools.base import BaseTool",
        "from langswarm.tools.base import BaseTool"
    )
    
    if content != original:
        main_py.write_text(content)
        print(f"✅ {tool_path.name}: Fixed import")
        return True
    else:
        print(f"⏭️  {tool_path.name}: Import already correct or no Tool class")
        return False

def fix_init_method(tool_path):
    """Fix the __init__ method to use correct BaseTool parameters"""
    main_py = tool_path / "main.py"
    if not main_py.exists():
        return False
    
    content = main_py.read_text()
    original = content
    
    # Pattern to match super().__init__( calls with the old parameters
    # This is complex, so we'll do specific replacements
    
    # Remove instruction= from super().__init__
    content = re.sub(
        r'(\s+super\(\).__init__\([^)]*)\n\s*instruction=instruction,',
        r'\1',
        content
    )
    
    # Change identifier= to tool_id=
    content = re.sub(
        r'identifier=identifier,',
        r'tool_id=identifier,',
        content
    )
    
    # Remove brief= from super().__init__
    content = re.sub(
        r'(\s+super\(\).__init__\([^)]*)\n\s*brief=brief,',
        r'\1',
        content
    )
    
    # Remove kwargs['mcp_server'] = server before super().__init__
    content = re.sub(
        r"\s+# Add MCP server reference\s+kwargs\['mcp_server'\] = server\s+",
        "\n        ",
        content
    )
    
    # Add object.__setattr__(self, 'mcp_server', server) after super().__init__ if not present
    if "'mcp_server'" not in content or "object.__setattr__(self, 'mcp_server'" not in content:
        # Find where to add it - after super().__init__ and before other setattr
        pattern = r"(super\(\).__init__\([^)]+\))\s+(# Store|object.__setattr__)"
        if re.search(pattern, content):
            content = re.sub(
                pattern,
                r"\1\n        \n        # Store configuration AFTER parent initialization\n        object.__setattr__(self, 'mcp_server', server)\n        \2",
                content,
                count=1
            )
    
    if content != original:
        main_py.write_text(content)
        print(f"✅ {tool_path.name}: Fixed __init__ method")
        return True
    else:
        print(f"⏭️  {tool_path.name}: __init__ already correct or no changes needed")
        return False

def main():
    print("🔧 Batch fixing MCP tools...")
    print(f"Tools to fix: {len(TOOLS_TO_FIX)}\n")
    
    fixed_imports = 0
    fixed_inits = 0
    
    for tool_name in TOOLS_TO_FIX:
        tool_path = MCP_TOOLS_DIR / tool_name
        if not tool_path.exists():
            print(f"❌ {tool_name}: Directory not found")
            continue
        
        print(f"\n📝 Processing {tool_name}...")
        if fix_import(tool_path):
            fixed_imports += 1
        if fix_init_method(tool_path):
            fixed_inits += 1
    
    print(f"\n\n✨ Summary:")
    print(f"   Fixed imports: {fixed_imports}")
    print(f"   Fixed __init__ methods: {fixed_inits}")
    print(f"\n🎉 Done!")

if __name__ == "__main__":
    main()
