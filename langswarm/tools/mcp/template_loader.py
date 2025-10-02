# langswarm/mcp/tools/template_loader.py

import os
import re
from typing import Dict, Optional


# Custom exception classes for template system errors
class TemplateNotFoundError(Exception):
    """Raised when template.md file is not found"""
    def __init__(self, template_path: str, tool_directory: str):
        super().__init__(f"Template file not found: {template_path}")
        self.template_path = template_path
        self.tool_directory = tool_directory


class TemplateParsingError(Exception):
    """Raised when template.md parsing fails"""
    def __init__(self, template_path: str, details: str):
        super().__init__(f"Failed to parse template {template_path}: {details}")
        self.template_path = template_path
        self.details = details


class TemplateValidationError(Exception):
    """Raised when template.md is missing required sections"""
    def __init__(self, template_path: str, missing_sections: list):
        super().__init__(f"Template {template_path} missing required sections: {', '.join(missing_sections)}")
        self.template_path = template_path
        self.missing_sections = missing_sections

def load_tool_template(tool_directory: str, strict_mode: bool = True) -> Dict[str, str]:
    """
    Load template values from a tool's template.md file.
    
    Args:
        tool_directory: Directory containing the tool (should have template.md)
        strict_mode: If True, raise exceptions for missing or invalid templates.
                    If False, return fallback values (for backward compatibility)
        
    Returns:
        Dictionary containing template values for description, instruction, brief, etc.
        
    Raises:
        TemplateNotFoundError: If template.md is missing and strict_mode=True
        TemplateParsingError: If template.md cannot be parsed and strict_mode=True
    """
    template_path = os.path.join(tool_directory, "template.md")
    
    if not os.path.exists(template_path):
        if strict_mode:
            raise TemplateNotFoundError(template_path, tool_directory)
        else:
            return get_generic_fallback_values()
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return parse_template_content(content, template_path, strict_mode)
    except TemplateParsingError:
        # Re-raise template parsing errors
        raise
    except Exception as e:
        if strict_mode:
            raise TemplateParsingError(template_path, f"File read error: {e}") from e
        else:
            print(f"Warning: Could not load template from {template_path}: {e}")
            return get_generic_fallback_values()

def parse_template_content(content: str, template_path: str = None, strict_mode: bool = True) -> Dict[str, str]:
    """
    Parse template.md content and extract key values.
    Expects simplified structure with 3 level 2 headers: Description, Instructions, Brief
    
    Args:
        content: Raw content from template.md file
        template_path: Path to template file (for error reporting)
        strict_mode: If True, validate that required sections are present
        
    Returns:
        Dictionary with parsed template values
        
    Raises:
        TemplateValidationError: If required sections are missing and strict_mode=True
    """
    # Note: Template content is static, but tools apply user config to actual operations
    
    values = {}
    found_sections = []
    
    # Extract description section (## Description)
    desc_match = re.search(r'## Description\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if desc_match:
        values['description'] = desc_match.group(1).strip()
        found_sections.append('Description')
    
    # Extract instructions section (## Instructions)
    inst_match = re.search(r'## Instructions\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if inst_match:
        values['instruction'] = inst_match.group(1).strip()
        found_sections.append('Instructions')
    
    # Extract brief section (## Brief)
    brief_match = re.search(r'## Brief\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if brief_match:
        values['brief'] = brief_match.group(1).strip()
        found_sections.append('Brief')
    
    # Try backward compatibility formats with explicit logging
    backward_compat_found = []
    
    if not values.get('description'):
        # Try old Primary Description format
        primary_desc_match = re.search(r'### Primary Description\n(.*?)(?=\n###|\n##|\Z)', content, re.DOTALL)
        if primary_desc_match:
            values['description'] = primary_desc_match.group(1).strip()
            backward_compat_found.append('Primary Description (deprecated)')
    
    if not values.get('instruction'):
        # Try old Primary Instruction format
        primary_inst_match = re.search(r'### Primary Instruction\n(.*?)(?=\n###|\n##|\Z)', content, re.DOTALL)
        if primary_inst_match:
            values['instruction'] = primary_inst_match.group(1).strip()
            backward_compat_found.append('Primary Instruction (deprecated)')
    
    if not values.get('brief'):
        # Try old Brief Description format
        brief_desc_match = re.search(r'### Brief Description\n(.*?)(?=\n###|\n##|\Z)', content, re.DOTALL)
        if brief_desc_match:
            values['brief'] = brief_desc_match.group(1).strip()
            backward_compat_found.append('Brief Description (deprecated)')
    
    # Warn about deprecated formats
    if backward_compat_found and template_path:
        print(f"Warning: {template_path} uses deprecated format sections: {', '.join(backward_compat_found)}")
        print(f"Please update to use: ## Description, ## Instructions, ## Brief")
    
    # Extract tool ID from instructions if present
    tool_id_match = re.search(r'\*\*Tool ID\*\*: ([^\n]+)', content)
    if tool_id_match:
        values['tool_id'] = tool_id_match.group(1).strip()
    
    # Extract tool type from instructions if present
    tool_type_match = re.search(r'\*\*Tool Type\*\*: ([^\n]+)', content)
    if tool_type_match:
        values['tool_type'] = tool_type_match.group(1).strip()
    
    # Validate required sections in strict mode
    if strict_mode:
        required_sections = ['description', 'instruction', 'brief']
        missing_sections = [section for section in required_sections if not values.get(section)]
        
        if missing_sections:
            template_path = template_path or "template.md"
            available_sections = found_sections + backward_compat_found
            error_details = (
                f"Missing sections: {missing_sections}. "
                f"Found sections: {available_sections if available_sections else 'none'}. "
                f"Required format: ## Description, ## Instructions, ## Brief"
            )
            raise TemplateValidationError(template_path, missing_sections)
    
    return values


def get_generic_fallback_values() -> Dict[str, str]:
    """
    Provide generic fallback template values if template.md cannot be loaded.
    
    This should only be used in non-strict mode for backward compatibility.
    
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

def get_tool_template_value(tool_directory: str, key: str, default: str = "", strict_mode: bool = True) -> str:
    """
    Get a specific template value by key for a given tool.
    
    Args:
        tool_directory: Directory containing the tool's template.md
        key: The template key to retrieve
        default: Default value if key not found
        strict_mode: If True, fail fast on template errors. If False, use default
        
    Returns:
        Template value or default
        
    Raises:
        TemplateNotFoundError: If template.md is missing and strict_mode=True
        TemplateParsingError: If template.md cannot be parsed and strict_mode=True
    """
    try:
        template_values = load_tool_template(tool_directory, strict_mode)
        return template_values.get(key, default)
    except (TemplateNotFoundError, TemplateParsingError, TemplateValidationError):
        if strict_mode:
            raise
        else:
            return default

# Cache for template values to avoid repeated file reads
_template_cache = {}


def validate_template_requirements(tool_directory: str) -> None:
    """
    Validate that a tool directory has a proper template.md file.
    
    Args:
        tool_directory: Directory containing the tool
        
    Raises:
        TemplateNotFoundError: If template.md is missing
        TemplateParsingError: If template.md cannot be parsed
        TemplateValidationError: If required sections are missing
    """
    load_tool_template(tool_directory, strict_mode=True)


# Backward compatibility functions (deprecated)
def load_tool_template_safe(tool_directory: str) -> Dict[str, str]:
    """
    DEPRECATED: Load template with fallbacks (backward compatibility).
    Use load_tool_template(tool_directory, strict_mode=False) instead.
    """
    return load_tool_template(tool_directory, strict_mode=False)


def get_cached_tool_template_safe(tool_directory: str) -> Dict[str, str]:
    """
    DEPRECATED: Get cached template with fallbacks (backward compatibility).
    Use get_cached_tool_template(tool_directory, strict_mode=False) instead.
    """
    return get_cached_tool_template(tool_directory, strict_mode=False)

def get_cached_tool_template(tool_directory: str, strict_mode: bool = True) -> Dict[str, str]:
    """
    Get template values with caching for performance.
    
    Args:
        tool_directory: Directory containing the tool's template.md
        strict_mode: If True, raise exceptions for missing or invalid templates
        
    Returns:
        Dictionary with cached template values
        
    Raises:
        TemplateNotFoundError: If template.md is missing and strict_mode=True
        TemplateParsingError: If template.md cannot be parsed and strict_mode=True
        TemplateValidationError: If required sections are missing and strict_mode=True
    """
    cache_key = f"{tool_directory}:{strict_mode}"
    
    if cache_key not in _template_cache:
        _template_cache[cache_key] = load_tool_template(tool_directory, strict_mode)
    
    return _template_cache[cache_key]

def create_tool_with_template(tool_class, tool_directory: str, identifier: str, name: str, 
                            description: str = "", instruction: str = "", brief: str = "", 
                            strict_mode: bool = True, **kwargs):
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
        strict_mode: If True, fail fast on template errors. If False, use fallbacks
        **kwargs: Additional arguments for tool initialization
        
    Returns:
        Instantiated tool with template values applied
        
    Raises:
        TemplateNotFoundError: If template.md is missing and strict_mode=True
        TemplateParsingError: If template.md cannot be parsed and strict_mode=True
        TemplateValidationError: If required sections are missing and strict_mode=True
    """
    try:
        template_values = get_cached_tool_template(tool_directory, strict_mode)
    except (TemplateNotFoundError, TemplateParsingError, TemplateValidationError) as e:
        if strict_mode:
            # Re-raise with additional context
            raise type(e)(f"Failed to create tool '{identifier}' from directory '{tool_directory}': {e}") from e
        else:
            # Use fallback values if not in strict mode
            template_values = get_generic_fallback_values()
    
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