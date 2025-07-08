# langswarm/mcp/tools/template_loader.py

import os
import re
from typing import Dict, Optional

def load_tool_template(tool_directory: str) -> Dict[str, str]:
    """
    Load template values from a tool's template.md file.
    
    Args:
        tool_directory: Directory containing the tool (should have template.md)
        
    Returns:
        Dictionary containing template values for description, instruction, brief, etc.
    """
    template_path = os.path.join(tool_directory, "template.md")
    
    if not os.path.exists(template_path):
        return get_generic_fallback_values()
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return parse_template_content(content)
    except Exception as e:
        print(f"Warning: Could not load template from {template_path}: {e}")
        return get_generic_fallback_values()

def parse_template_content(content: str) -> Dict[str, str]:
    """
    Parse template.md content and extract key values.
    Expects simplified structure with 3 level 2 headers: Description, Instructions, Brief
    
    Args:
        content: Raw content from template.md file
        
    Returns:
        Dictionary with parsed template values
    """
    values = {}
    
    # Extract description section (## Description)
    desc_match = re.search(r'## Description\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if desc_match:
        values['description'] = desc_match.group(1).strip()
    
    # Extract instructions section (## Instructions)
    inst_match = re.search(r'## Instructions\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if inst_match:
        values['instruction'] = inst_match.group(1).strip()
    
    # Extract brief section (## Brief)
    brief_match = re.search(r'## Brief\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if brief_match:
        values['brief'] = brief_match.group(1).strip()
    
    # For backward compatibility, also try to extract old format sections if new format not found
    if not values.get('description'):
        # Try old Primary Description format
        primary_desc_match = re.search(r'### Primary Description\n(.*?)(?=\n###|\n##|\Z)', content, re.DOTALL)
        if primary_desc_match:
            values['description'] = primary_desc_match.group(1).strip()
    
    if not values.get('instruction'):
        # Try old Primary Instruction format
        primary_inst_match = re.search(r'### Primary Instruction\n(.*?)(?=\n###|\n##|\Z)', content, re.DOTALL)
        if primary_inst_match:
            values['instruction'] = primary_inst_match.group(1).strip()
    
    if not values.get('brief'):
        # Try old Brief Description format
        brief_desc_match = re.search(r'### Brief Description\n(.*?)(?=\n###|\n##|\Z)', content, re.DOTALL)
        if brief_desc_match:
            values['brief'] = brief_desc_match.group(1).strip()
    
    # Extract tool ID from instructions if present
    tool_id_match = re.search(r'\*\*Tool ID\*\*: ([^\n]+)', content)
    if tool_id_match:
        values['tool_id'] = tool_id_match.group(1).strip()
    
    # Extract tool type from instructions if present
    tool_type_match = re.search(r'\*\*Tool Type\*\*: ([^\n]+)', content)
    if tool_type_match:
        values['tool_type'] = tool_type_match.group(1).strip()
    
    return values

def get_generic_fallback_values() -> Dict[str, str]:
    """
    Provide generic fallback template values if template.md cannot be loaded.
    
    Returns:
        Dictionary with basic fallback values
    """
    return {
        'description': 'MCP tool for LangSwarm framework',
        'brief': 'MCP tool',
        'instruction': 'Use this tool to perform operations via MCP protocol',
        'tool_id': 'unknown',
        'tool_type': 'Direct method calls'
    }

def get_tool_template_value(tool_directory: str, key: str, default: str = "") -> str:
    """
    Get a specific template value by key for a given tool.
    
    Args:
        tool_directory: Directory containing the tool's template.md
        key: The template key to retrieve
        default: Default value if key not found
        
    Returns:
        Template value or default
    """
    template_values = load_tool_template(tool_directory)
    return template_values.get(key, default)

# Cache for template values to avoid repeated file reads
_template_cache = {}

def get_cached_tool_template(tool_directory: str) -> Dict[str, str]:
    """
    Get template values with caching for performance.
    
    Args:
        tool_directory: Directory containing the tool's template.md
        
    Returns:
        Dictionary with cached template values
    """
    if tool_directory not in _template_cache:
        _template_cache[tool_directory] = load_tool_template(tool_directory)
    
    return _template_cache[tool_directory]

def create_tool_with_template(tool_class, tool_directory: str, identifier: str, name: str, 
                            description: str = "", instruction: str = "", brief: str = "", **kwargs):
    """
    Create a tool instance using template values as defaults.
    
    Args:
        tool_class: The tool class to instantiate
        tool_directory: Directory containing the tool's template.md
        identifier: Tool identifier
        name: Tool name
        description: Tool description (uses template if empty)
        instruction: Tool instruction (uses template if empty)
        brief: Tool brief (uses template if empty)
        **kwargs: Additional arguments for tool initialization
        
    Returns:
        Instantiated tool with template values applied
    """
    template_values = get_cached_tool_template(tool_directory)
    
    # Use template values as defaults if not provided
    description = description or template_values.get('description', 'MCP tool for LangSwarm framework')
    instruction = instruction or template_values.get('instruction', 'Use this tool to perform operations via MCP protocol')
    brief = brief or template_values.get('brief', 'MCP tool')
    
    return tool_class(
        identifier=identifier,
        name=name,
        description=description,
        instruction=instruction,
        brief=brief,
        **kwargs
    ) 