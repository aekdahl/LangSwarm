
import os
import re
import sys
from pathlib import Path

def verify_links(docs_root):
    docs_path = Path(docs_root).resolve()
    print(f"Verifying links in: {docs_path}")
    
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    broken_links = []
    
    for root, _, files in os.walk(docs_path):
        if 'archive' in root:
            continue
            
        for file in files:
            if not file.endswith('.md') and not file.endswith('.mdx'):
                continue
                
            file_path = Path(root) / file
            
            try:
                content = file_path.read_text(encoding='utf-8')
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue
                
            matches = link_pattern.findall(content)
            
            for text, target in matches:
                # Skip anchors, external links, and mailto
                if target.startswith('#') or target.startswith('http') or target.startswith('mailto:'):
                    continue
                
                # Handling anchors in links (e.g. file.md#section)
                target_file = target.split('#')[0]
                if not target_file:
                    continue
                    
                # Resolve path
                if target_file.startswith('/'):
                    # Absolute path usually means from project root or docs root? 
                    # In Mintlify/Docusaurus, absolute usually means /docs/
                    # Let's assume relative for now or try to resolve from docs root
                    resolved_path = docs_path / target_file.lstrip('/')
                else:
                    resolved_path = (file_path.parent / target_file).resolve()
                
                # Check for existence (allow for .md -> .mdx reference mismatch if common)
                if not resolved_path.exists():
                    # Try appended extension if missing
                    if not resolved_path.suffix and (resolved_path.with_suffix('.md').exists() or resolved_path.with_suffix('.mdx').exists()):
                        continue
                        
                    # Try swapping md/mdx
                    if resolved_path.suffix == '.md' and resolved_path.with_suffix('.mdx').exists():
                        continue
                    if resolved_path.suffix == '.mdx' and resolved_path.with_suffix('.md').exists():
                        continue
                        
                    # Check if it's a directory with index.md/mdx
                    if resolved_path.is_dir():
                        if (resolved_path / 'index.md').exists() or (resolved_path / 'index.mdx').exists():
                            continue
                            
                    broken_links.append({
                        'source': str(file_path.relative_to(docs_path)),
                        'target': target,
                        'resolved': str(resolved_path)
                    })

    if broken_links:
        print("\n❌ Found Broken Links:")
        for link in broken_links:
            print(f"  File: {link['source']}")
            print(f"    Link: {link['target']}")
        sys.exit(1)
    else:
        print("\n✅ All links verified successfully!")
        sys.exit(0)

if __name__ == "__main__":
    verify_links("docs")
