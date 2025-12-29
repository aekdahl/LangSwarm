#!/usr/bin/env python3
"""
LangSwarm API Documentation Generator

Automatically generates comprehensive API documentation from type hints,
docstrings, and code analysis. Focuses on the orchestration APIs that
are the core value proposition of LangSwarm.
"""

import ast
import inspect
import importlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, get_type_hints
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class FunctionDoc:
    """Documentation for a single function."""
    name: str
    signature: str
    docstring: Optional[str]
    parameters: Dict[str, str]
    return_type: str
    module: str
    is_async: bool


@dataclass
class ClassDoc:
    """Documentation for a single class."""
    name: str
    docstring: Optional[str]
    methods: List[FunctionDoc]
    module: str
    inheritance: List[str]


@dataclass
class ModuleDoc:
    """Documentation for a complete module."""
    name: str
    docstring: Optional[str]
    functions: List[FunctionDoc]
    classes: List[ClassDoc]
    file_path: str


class APIDocumentationGenerator:
    """
    Generates comprehensive API documentation from Python code.
    
    Extracts type hints, docstrings, and signatures to create
    markdown documentation focused on LangSwarm's orchestration APIs.
    """
    
    def __init__(self, output_dir: str = "docs/api-reference"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Focus on these key orchestration modules
        self.key_modules = [
            "langswarm.core.agents",
            "langswarm.core.workflows", 
            "langswarm.core.session",
            "langswarm.simple_api",
            "langswarm.core.orchestration_errors",
            "langswarm_memory.interfaces",
            "langswarm_memory.backends",
            "langswarm_memory.errors"
        ]
    
    def generate_all_docs(self) -> None:
        """Generate documentation for all key modules."""
        print("🔧 Generating LangSwarm API Documentation")
        print("=" * 60)
        
        module_docs = []
        
        for module_name in self.key_modules:
            print(f"\n📋 Processing {module_name}...")
            try:
                doc = self.extract_module_documentation(module_name)
                if doc:
                    module_docs.append(doc)
                    self.write_module_documentation(doc)
                    print(f"✅ Generated docs for {module_name}")
                else:
                    print(f"⚠️  No documentation found for {module_name}")
            except Exception as e:
                print(f"❌ Error processing {module_name}: {e}")
        
        # Generate overview documentation
        self.generate_api_overview(module_docs)
        print(f"\n🎉 API documentation generated in {self.output_dir}")
    
    def extract_module_documentation(self, module_name: str) -> Optional[ModuleDoc]:
        """Extract documentation from a Python module."""
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            print(f"Cannot import {module_name}: {e}")
            return None
        
        # Get module file path
        file_path = getattr(module, '__file__', 'Unknown')
        
        # Extract module docstring
        module_docstring = inspect.getdoc(module)
        
        # Extract functions and classes
        functions = []
        classes = []
        
        for name, obj in inspect.getmembers(module):
            # Skip private members and imports
            if name.startswith('_') or getattr(obj, '__module__', None) != module_name:
                continue
            
            if inspect.isfunction(obj):
                func_doc = self.extract_function_documentation(obj, module_name)
                if func_doc:
                    functions.append(func_doc)
            
            elif inspect.isclass(obj):
                class_doc = self.extract_class_documentation(obj, module_name)
                if class_doc:
                    classes.append(class_doc)
        
        return ModuleDoc(
            name=module_name,
            docstring=module_docstring,
            functions=functions,
            classes=classes,
            file_path=file_path
        )
    
    def extract_function_documentation(self, func: Any, module_name: str) -> Optional[FunctionDoc]:
        """Extract documentation from a function."""
        try:
            # Get signature
            sig = inspect.signature(func)
            signature = f"{func.__name__}{sig}"
            
            # Get docstring
            docstring = inspect.getdoc(func)
            
            # Get type hints
            try:
                type_hints = get_type_hints(func)
            except (NameError, AttributeError):
                type_hints = {}
            
            # Extract parameter information
            parameters = {}
            for param_name, param in sig.parameters.items():
                param_type = type_hints.get(param_name, param.annotation)
                if param_type != inspect.Parameter.empty:
                    param_type_str = self.format_type(param_type)
                else:
                    param_type_str = "Any"
                
                # Add default value if present
                if param.default != inspect.Parameter.empty:
                    param_type_str += f" = {repr(param.default)}"
                
                parameters[param_name] = param_type_str
            
            # Get return type
            return_type = type_hints.get('return', sig.return_annotation)
            return_type_str = self.format_type(return_type) if return_type != inspect.Parameter.empty else "Any"
            
            # Check if async
            is_async = inspect.iscoroutinefunction(func)
            
            return FunctionDoc(
                name=func.__name__,
                signature=signature,
                docstring=docstring,
                parameters=parameters,
                return_type=return_type_str,
                module=module_name,
                is_async=is_async
            )
            
        except Exception as e:
            print(f"Error extracting function {func.__name__}: {e}")
            return None
    
    def extract_class_documentation(self, cls: Any, module_name: str) -> Optional[ClassDoc]:
        """Extract documentation from a class."""
        try:
            # Get class docstring
            docstring = inspect.getdoc(cls)
            
            # Get inheritance
            inheritance = [base.__name__ for base in cls.__bases__ if base != object]
            
            # Extract methods
            methods = []
            for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                if not method_name.startswith('_'):
                    method_doc = self.extract_function_documentation(method, module_name)
                    if method_doc:
                        methods.append(method_doc)
            
            return ClassDoc(
                name=cls.__name__,
                docstring=docstring,
                methods=methods,
                module=module_name,
                inheritance=inheritance
            )
            
        except Exception as e:
            print(f"Error extracting class {cls.__name__}: {e}")
            return None
    
    def format_type(self, type_annotation: Any) -> str:
        """Format a type annotation as a string."""
        if type_annotation is None or type_annotation == type(None):
            return "None"
        
        if hasattr(type_annotation, '__name__'):
            return type_annotation.__name__
        
        # Handle typing module types
        type_str = str(type_annotation)
        
        # Clean up common typing patterns
        type_str = type_str.replace('typing.', '')
        type_str = type_str.replace('<class \'', '').replace('\'>', '')
        
        return type_str
    
    def write_module_documentation(self, module_doc: ModuleDoc) -> None:
        """Write documentation for a module to a markdown file."""
        # Create filename from module name
        filename = module_doc.name.replace('.', '_') + '.md'
        file_path = self.output_dir / filename
        
        content = self.generate_module_markdown(module_doc)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def generate_module_markdown(self, module_doc: ModuleDoc) -> str:
        """Generate markdown content for a module."""
        lines = []
        
        # Header
        module_title = module_doc.name.replace('langswarm.', '').replace('.', ' ').title()
        lines.extend([
            f"# {module_title} API",
            "",
            f"**Module:** `{module_doc.name}`",
            ""
        ])
        
        # Module docstring
        if module_doc.docstring:
            lines.extend([
                "## Overview",
                "",
                module_doc.docstring,
                ""
            ])
        
        # Table of contents
        if module_doc.functions or module_doc.classes:
            lines.extend([
                "## Table of Contents",
                ""
            ])
            
            if module_doc.functions:
                lines.append("### Functions")
                for func in module_doc.functions:
                    lines.append(f"- [{func.name}](#{func.name.lower()})")
                lines.append("")
            
            if module_doc.classes:
                lines.append("### Classes")
                for cls in module_doc.classes:
                    lines.append(f"- [{cls.name}](#{cls.name.lower()})")
                lines.append("")
        
        # Functions
        if module_doc.functions:
            lines.extend([
                "## Functions",
                ""
            ])
            
            for func in module_doc.functions:
                lines.extend(self.generate_function_markdown(func))
                lines.append("")
        
        # Classes
        if module_doc.classes:
            lines.extend([
                "## Classes",
                ""
            ])
            
            for cls in module_doc.classes:
                lines.extend(self.generate_class_markdown(cls))
                lines.append("")
        
        return "\n".join(lines)
    
    def generate_function_markdown(self, func_doc: FunctionDoc) -> List[str]:
        """Generate markdown for a function."""
        lines = []
        
        # Function header
        async_prefix = "async " if func_doc.is_async else ""
        lines.extend([
            f"### {func_doc.name}",
            "",
            "```python",
            f"{async_prefix}def {func_doc.signature}",
            "```",
            ""
        ])
        
        # Docstring
        if func_doc.docstring:
            lines.extend([
                func_doc.docstring,
                ""
            ])
        
        # Parameters
        if func_doc.parameters:
            lines.extend([
                "**Parameters:**",
                ""
            ])
            
            for param_name, param_type in func_doc.parameters.items():
                lines.append(f"- `{param_name}`: `{param_type}`")
            
            lines.append("")
        
        # Return type
        if func_doc.return_type and func_doc.return_type != "Any":
            lines.extend([
                "**Returns:**",
                "",
                f"`{func_doc.return_type}`",
                ""
            ])
        
        return lines
    
    def generate_class_markdown(self, class_doc: ClassDoc) -> List[str]:
        """Generate markdown for a class."""
        lines = []
        
        # Class header
        inheritance_str = ""
        if class_doc.inheritance:
            inheritance_str = f"({', '.join(class_doc.inheritance)})"
        
        lines.extend([
            f"### {class_doc.name}",
            "",
            f"```python",
            f"class {class_doc.name}{inheritance_str}",
            "```",
            ""
        ])
        
        # Class docstring
        if class_doc.docstring:
            lines.extend([
                class_doc.docstring,
                ""
            ])
        
        # Methods
        if class_doc.methods:
            lines.extend([
                "**Methods:**",
                ""
            ])
            
            for method in class_doc.methods:
                async_prefix = "async " if method.is_async else ""
                lines.extend([
                    f"#### {method.name}",
                    "",
                    "```python",
                    f"{async_prefix}def {method.signature}",
                    "```",
                    ""
                ])
                
                if method.docstring:
                    lines.extend([
                        method.docstring,
                        ""
                    ])
                
                # Method parameters
                if method.parameters:
                    lines.extend([
                        "**Parameters:**",
                        ""
                    ])
                    
                    for param_name, param_type in method.parameters.items():
                        if param_name != 'self':  # Skip self parameter
                            lines.append(f"- `{param_name}`: `{param_type}`")
                    
                    lines.append("")
                
                # Method return type
                if method.return_type and method.return_type != "Any":
                    lines.extend([
                        "**Returns:**",
                        "",
                        f"`{method.return_type}`",
                        ""
                    ])
        
        return lines
    
    def generate_api_overview(self, module_docs: List[ModuleDoc]) -> None:
        """Generate an overview document for all API modules."""
        lines = [
            "# LangSwarm API Reference",
            "",
            "Complete API documentation for LangSwarm's multi-agent orchestration framework.",
            "",
            f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Quick Start",
            "",
            "LangSwarm's core value is **multi-agent orchestration**. Here's the essential workflow:",
            "",
            "```python",
            "from langswarm import create_openai_agent, register_agent, create_simple_workflow, get_workflow_engine",
            "",
            "# 1. Create specialized agents",
            "researcher = await create_openai_agent('researcher', system_prompt='Research specialist')",
            "summarizer = await create_openai_agent('summarizer', system_prompt='Summary specialist')",
            "",
            "# 2. Register for orchestration", 
            "register_agent(researcher)",
            "register_agent(summarizer)",
            "",
            "# 3. Create workflow",
            "workflow = create_simple_workflow('task', 'Research Task', ['researcher', 'summarizer'])",
            "",
            "# 4. Execute orchestration",
            "engine = get_workflow_engine()",
            "result = await engine.execute_workflow(workflow, {'input': 'AI safety research'})",
            "```",
            "",
            "## API Modules",
            ""
        ]
        
        # Add module summaries
        for module_doc in module_docs:
            module_name = module_doc.name.replace('langswarm.', '')
            filename = module_doc.name.replace('.', '_') + '.md'
            
            lines.extend([
                f"### [{module_name}]({filename})",
                ""
            ])
            
            if module_doc.docstring:
                # Get first line of docstring as summary
                summary = module_doc.docstring.split('\n')[0]
                lines.append(f"{summary}")
            
            lines.extend([
                "",
                f"- **Functions:** {len(module_doc.functions)}",
                f"- **Classes:** {len(module_doc.classes)}",
                ""
            ])
        
        # Key concepts section
        lines.extend([
            "## Key Concepts",
            "",
            "### 🤖 Agents",
            "Specialized AI entities with specific roles and capabilities. Each agent has a unique ID and system prompt.",
            "",
            "### 📋 Workflows",
            "Orchestration blueprints defining how agents collaborate. Specify sequence and data flow between agents.",
            "",
            "### 🔄 Data Flow", 
            "Automatic data passing between agents. Each agent receives output from the previous agent.",
            "",
            "### 🏭 Execution Engine",
            "Orchestration runtime that executes workflows, manages agent coordination and error handling.",
            "",
            "## Type System",
            "",
            "LangSwarm uses comprehensive type hints for better development experience:",
            "",
            "- `BaseAgent`: Core agent implementation",
            "- `IWorkflow`: Workflow interface",
            "- `WorkflowResult`: Execution result with status and data",
            "- `WorkflowStatus`: Enum for tracking execution state",
            "",
            "## Error Handling",
            "",
            "Comprehensive error system with actionable suggestions:",
            "",
            "- `AgentNotFoundError`: When workflow references unregistered agent",
            "- `WorkflowExecutionError`: When workflow execution fails", 
            "- `AgentExecutionError`: When individual agent fails",
            "- `DataPassingError`: When data cannot be passed between steps",
            "",
            "See the [orchestration_errors](langswarm_core_orchestration_errors.md) module for details.",
            ""
        ])
        
        # Write overview file
        overview_path = self.output_dir / "README.md"
        with open(overview_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))


def main():
    """Generate API documentation."""
    generator = APIDocumentationGenerator()
    generator.generate_all_docs()


if __name__ == "__main__":
    main()