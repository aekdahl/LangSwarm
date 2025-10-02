"""
Text Processor Tool - V2 Built-in Tool

Provides basic text processing capabilities for common string operations.
Useful for data cleaning, formatting, and basic text analysis.
"""

import json
import re
import hashlib
import base64
from typing import Dict, Any, Optional, List, Union

from langswarm.tools.base import BaseTool, ToolResult, create_tool_metadata, create_method_schema
from langswarm.tools.interfaces import ToolType, ToolCapability


class TextProcessorTool(BaseTool):
    """
    Built-in tool for text processing operations.
    
    Provides common text operations:
    - String manipulation (upper, lower, strip, etc.)
    - Text analysis (length, word count, etc.)
    - Encoding/decoding (base64, url, etc.)
    - Regular expressions
    - Hash generation
    - JSON formatting
    """
    
    def __init__(self):
        metadata = create_tool_metadata(
            tool_id="builtin_text_processor",
            name="text_processor",
            description="Text processing and string manipulation tool",
            version="2.0.0",
            tool_type=ToolType.BUILTIN,
            capabilities=[ToolCapability.TEXT_PROCESSING, ToolCapability.FORMATTING, ToolCapability.ENCODING]
        )
        
        # Add methods for text manipulation
        metadata.add_method(create_method_schema(
            name="transform",
            description="Transform text with various operations",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to transform"},
                "operations": {"type": "array", "items": {"type": "string"}, "required": True,
                              "description": "List of operations: upper, lower, strip, title, reverse"}
            },
            returns="Transformed text"
        ))
        
        metadata.add_method(create_method_schema(
            name="analyze",
            description="Analyze text and return statistics",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to analyze"}
            },
            returns="Text analysis with length, word count, line count, etc."
        ))
        
        metadata.add_method(create_method_schema(
            name="encode",
            description="Encode text using various encoding schemes",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to encode"},
                "encoding": {"type": "string", "required": True, 
                           "description": "Encoding type: base64, url, html, json"}
            },
            returns="Encoded text"
        ))
        
        metadata.add_method(create_method_schema(
            name="decode",
            description="Decode text using various encoding schemes",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to decode"},
                "encoding": {"type": "string", "required": True,
                           "description": "Encoding type: base64, url, html, json"}
            },
            returns="Decoded text"
        ))
        
        metadata.add_method(create_method_schema(
            name="regex_find",
            description="Find matches using regular expressions",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to search"},
                "pattern": {"type": "string", "required": True, "description": "Regular expression pattern"},
                "flags": {"type": "string", "required": False, "description": "Regex flags (i, m, s, x)"}
            },
            returns="List of matches"
        ))
        
        metadata.add_method(create_method_schema(
            name="regex_replace",
            description="Replace text using regular expressions",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to process"},
                "pattern": {"type": "string", "required": True, "description": "Regular expression pattern"},
                "replacement": {"type": "string", "required": True, "description": "Replacement text"},
                "flags": {"type": "string", "required": False, "description": "Regex flags (i, m, s, x)"}
            },
            returns="Text with replacements"
        ))
        
        metadata.add_method(create_method_schema(
            name="hash_text",
            description="Generate hash of text",
            parameters={
                "text": {"type": "string", "required": True, "description": "Text to hash"},
                "algorithm": {"type": "string", "required": False, "default": "sha256",
                            "description": "Hash algorithm: md5, sha1, sha256, sha512"}
            },
            returns="Hash of the text"
        ))
        
        metadata.add_method(create_method_schema(
            name="format_json",
            description="Format JSON text with proper indentation",
            parameters={
                "json_text": {"type": "string", "required": True, "description": "JSON text to format"},
                "indent": {"type": "integer", "required": False, "default": 2, "description": "Indentation spaces"}
            },
            returns="Formatted JSON text"
        ))
        
        super().__init__(metadata)
    
    async def transform(self, text: str, operations: List[str]) -> str:
        """Transform text with various operations"""
        result = text
        
        for operation in operations:
            if operation == "upper":
                result = result.upper()
            elif operation == "lower":
                result = result.lower()
            elif operation == "strip":
                result = result.strip()
            elif operation == "title":
                result = result.title()
            elif operation == "reverse":
                result = result[::-1]
            elif operation == "capitalize":
                result = result.capitalize()
            elif operation == "swapcase":
                result = result.swapcase()
            else:
                raise ValueError(f"Unknown operation: {operation}")
        
        return result
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text and return statistics"""
        lines = text.split('\n')
        words = text.split()
        
        return {
            "length": len(text),
            "characters": len(text),
            "characters_no_spaces": len(text.replace(' ', '')),
            "words": len(words),
            "lines": len(lines),
            "paragraphs": len([line for line in lines if line.strip()]),
            "sentences": len(re.findall(r'[.!?]+', text)),
            "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "unique_words": len(set(word.lower() for word in words)),
            "starts_with": text[:10] + "..." if len(text) > 10 else text,
            "ends_with": "..." + text[-10:] if len(text) > 10 else text
        }
    
    async def encode(self, text: str, encoding: str) -> str:
        """Encode text using various encoding schemes"""
        if encoding == "base64":
            return base64.b64encode(text.encode('utf-8')).decode('ascii')
        elif encoding == "url":
            import urllib.parse
            return urllib.parse.quote(text)
        elif encoding == "html":
            import html
            return html.escape(text)
        elif encoding == "json":
            return json.dumps(text)
        else:
            raise ValueError(f"Unknown encoding: {encoding}")
    
    async def decode(self, text: str, encoding: str) -> str:
        """Decode text using various encoding schemes"""
        if encoding == "base64":
            return base64.b64decode(text.encode('ascii')).decode('utf-8')
        elif encoding == "url":
            import urllib.parse
            return urllib.parse.unquote(text)
        elif encoding == "html":
            import html
            return html.unescape(text)
        elif encoding == "json":
            return json.loads(text)
        else:
            raise ValueError(f"Unknown encoding: {encoding}")
    
    async def regex_find(self, text: str, pattern: str, flags: Optional[str] = None) -> List[str]:
        """Find matches using regular expressions"""
        regex_flags = 0
        if flags:
            if 'i' in flags:
                regex_flags |= re.IGNORECASE
            if 'm' in flags:
                regex_flags |= re.MULTILINE
            if 's' in flags:
                regex_flags |= re.DOTALL
            if 'x' in flags:
                regex_flags |= re.VERBOSE
        
        matches = re.findall(pattern, text, regex_flags)
        return matches
    
    async def regex_replace(self, text: str, pattern: str, replacement: str, flags: Optional[str] = None) -> str:
        """Replace text using regular expressions"""
        regex_flags = 0
        if flags:
            if 'i' in flags:
                regex_flags |= re.IGNORECASE
            if 'm' in flags:
                regex_flags |= re.MULTILINE
            if 's' in flags:
                regex_flags |= re.DOTALL
            if 'x' in flags:
                regex_flags |= re.VERBOSE
        
        return re.sub(pattern, replacement, text, flags=regex_flags)
    
    async def hash_text(self, text: str, algorithm: str = "sha256") -> str:
        """Generate hash of text"""
        text_bytes = text.encode('utf-8')
        
        if algorithm == "md5":
            return hashlib.md5(text_bytes).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(text_bytes).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(text_bytes).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(text_bytes).hexdigest()
        else:
            raise ValueError(f"Unknown hash algorithm: {algorithm}")
    
    async def format_json(self, json_text: str, indent: int = 2) -> str:
        """Format JSON text with proper indentation"""
        try:
            data = json.loads(json_text)
            return json.dumps(data, indent=indent, ensure_ascii=False)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def run(self, input_data: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        MCP-compatible run method - returns coroutines that can be awaited
        """
        if input_data is None:
            input_data = kwargs
        
        method = input_data.get('method', 'transform')
        method_args = {k: v for k, v in input_data.items() if k != 'method'}
        
        if method == 'transform':
            return self.transform(**method_args)
        elif method == 'analyze':
            return self.analyze(**method_args)
        elif method == 'encode':
            return self.encode(**method_args)
        elif method == 'decode':
            return self.decode(**method_args)
        elif method == 'regex_find':
            return self.regex_find(**method_args)
        elif method == 'regex_replace':
            return self.regex_replace(**method_args)
        elif method == 'hash_text':
            return self.hash_text(**method_args)
        elif method == 'format_json':
            return self.format_json(**method_args)
        else:
            raise ValueError(f"Unknown method: {method}")


# Import asyncio for the run method
import asyncio
