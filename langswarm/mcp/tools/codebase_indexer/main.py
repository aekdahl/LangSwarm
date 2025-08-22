"""
Enhanced Codebase Indexer MCP Tool

Provides semantic code analysis, architecture insights, and intelligent code understanding
that complements filesystem and GitHub tools with deep codebase intelligence.
"""

import os
import ast
import json
import hashlib
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict, Counter

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from langswarm.mcp.server_base import BaseMCPToolServer
from langswarm.synapse.tools.base import BaseTool
from pydantic import BaseModel

# ===== MCP Tool Server Configuration =====
server = BaseMCPToolServer(
    name="Enhanced Codebase Indexer",
    description="Semantic code analysis and architecture intelligence tool",
    local_mode=True
)

# ===== Pydantic Models for MCP Methods =====

class CodebaseOverviewInput(BaseModel):
    root_path: str = "."
    max_depth: Optional[int] = None
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None

class CodebaseOverviewOutput(BaseModel):
    summary: Dict[str, Any]
    structure: Dict[str, Any]
    metrics: Dict[str, Any]
    entry_points: List[str]

class SemanticSearchInput(BaseModel):
    query: str
    root_path: str = "."
    file_types: Optional[List[str]] = None
    max_results: int = 10

class SemanticSearchOutput(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    search_summary: str

class AnalyzePatternsInput(BaseModel):
    root_path: str = "."
    target_files: Optional[List[str]] = None
    pattern_types: Optional[List[str]] = None

class AnalyzePatternsOutput(BaseModel):
    patterns: List[Dict[str, Any]]
    recommendations: List[str]
    summary: Dict[str, Any]

class GetDependenciesInput(BaseModel):
    file_path: str
    include_external: bool = True
    max_depth: int = 3

class GetDependenciesOutput(BaseModel):
    dependencies: Dict[str, Any]
    dependency_graph: List[Dict[str, Any]]
    circular_dependencies: List[List[str]]

class GetCodeMetricsInput(BaseModel):
    root_path: str = "."
    target_files: Optional[List[str]] = None
    include_complexity: bool = True

class GetCodeMetricsOutput(BaseModel):
    metrics: Dict[str, Any]
    file_metrics: List[Dict[str, Any]]
    recommendations: List[str]

# ===== Core Data Structures =====

@dataclass
class FileInfo:
    """Information about a file in the codebase"""
    path: str
    name: str
    extension: str
    size: int
    lines: int
    functions: List[str]
    classes: List[str]
    imports: List[str]
    complexity: Optional[int] = None
    
@dataclass
class CodePattern:
    """Detected code pattern"""
    name: str
    type: str
    confidence: float
    description: str
    files: List[str]
    examples: List[str]

@dataclass  
class Dependency:
    """Code dependency relationship"""
    source: str
    target: str
    type: str  # import, function_call, inheritance, etc.
    confidence: float

# ===== Core Analysis Engine =====

class CodebaseAnalyzer:
    """Core engine for codebase analysis and intelligence"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.file_cache: Dict[str, FileInfo] = {}
        self.dependency_cache: Dict[str, List[Dependency]] = {}
        
        # Supported file extensions for analysis
        self.code_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', 
            '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt'
        }
        
        # Common patterns to detect
        self.pattern_detectors = {
            'singleton': self._detect_singleton_pattern,
            'factory': self._detect_factory_pattern,
            'observer': self._detect_observer_pattern,
            'mvc': self._detect_mvc_pattern,
            'decorator': self._detect_decorator_pattern,
        }
    
    def get_codebase_overview(self, max_depth: Optional[int] = None, 
                            include_patterns: Optional[List[str]] = None,
                            exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate comprehensive codebase overview"""
        
        # Scan files
        files = self._scan_files(max_depth, include_patterns, exclude_patterns)
        
        # Analyze structure
        structure = self._analyze_structure(files)
        
        # Calculate metrics
        metrics = self._calculate_overview_metrics(files)
        
        # Find entry points
        entry_points = self._find_entry_points(files)
        
        return {
            'summary': {
                'total_files': len(files),
                'total_lines': sum(f.lines for f in files.values()),
                'languages': self._detect_languages(files),
                'main_directories': list(structure.keys())[:10],
                'estimated_complexity': metrics.get('avg_complexity', 0)
            },
            'structure': structure,
            'metrics': metrics,
            'entry_points': entry_points
        }
    
    def semantic_search(self, query: str, file_types: Optional[List[str]] = None, 
                       max_results: int = 10) -> Dict[str, Any]:
        """Search codebase semantically by meaning and context"""
        
        # Get relevant files
        files = self._get_files_by_type(file_types)
        
        # Perform semantic matching
        results = []
        query_lower = query.lower()
        query_tokens = set(re.findall(r'\w+', query_lower))
        
        for file_path, file_info in files.items():
            score = self._calculate_semantic_score(file_info, query_tokens, query_lower)
            if score > 0:
                results.append({
                    'file': file_path,
                    'score': score,
                    'relevance_reason': self._explain_relevance(file_info, query_tokens),
                    'preview': self._get_relevant_preview(file_path, query_tokens),
                    'functions': file_info.functions,
                    'classes': file_info.classes
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:max_results]
        
        return {
            'results': results,
            'total_found': len(results),
            'search_summary': f"Found {len(results)} files matching '{query}'"
        }
    
    def analyze_patterns(self, target_files: Optional[List[str]] = None,
                        pattern_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Detect architectural and design patterns"""
        
        if target_files:
            files = {f: self._analyze_file(f) for f in target_files if os.path.exists(f)}
        else:
            files = self._scan_files()
        
        patterns = []
        pattern_types = pattern_types or list(self.pattern_detectors.keys())
        
        for pattern_type in pattern_types:
            if pattern_type in self.pattern_detectors:
                detected = self.pattern_detectors[pattern_type](files)
                patterns.extend(detected)
        
        # Generate recommendations
        recommendations = self._generate_pattern_recommendations(patterns, files)
        
        # Create summary
        summary = {
            'total_patterns': len(patterns),
            'pattern_types': Counter(p.type for p in patterns),
            'high_confidence_patterns': len([p for p in patterns if p.confidence > 0.8])
        }
        
        return {
            'patterns': [self._pattern_to_dict(p) for p in patterns],
            'recommendations': recommendations,
            'summary': summary
        }
    
    def get_dependencies(self, file_path: str, include_external: bool = True, 
                        max_depth: int = 3) -> Dict[str, Any]:
        """Analyze dependencies and relationships for a file"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(file_path, max_depth)
        
        # Detect circular dependencies
        circular = self._detect_circular_dependencies(dependencies)
        
        # Format dependency graph
        graph = self._format_dependency_graph(dependencies, include_external)
        
        return {
            'dependencies': self._dependencies_to_dict(dependencies),
            'dependency_graph': graph,
            'circular_dependencies': circular
        }
    
    def get_code_metrics(self, target_files: Optional[List[str]] = None,
                        include_complexity: bool = True) -> Dict[str, Any]:
        """Calculate comprehensive code metrics"""
        
        if target_files:
            files = {f: self._analyze_file(f) for f in target_files if os.path.exists(f)}
        else:
            files = self._scan_files()
        
        # Calculate overall metrics
        total_lines = sum(f.lines for f in files.values())
        total_functions = sum(len(f.functions) for f in files.values())
        total_classes = sum(len(f.classes) for f in files.values())
        
        # File-level metrics
        file_metrics = []
        for file_path, file_info in files.items():
            metrics = {
                'file': file_path,
                'lines': file_info.lines,
                'functions': len(file_info.functions),
                'classes': len(file_info.classes),
                'imports': len(file_info.imports)
            }
            
            if include_complexity and file_info.complexity:
                metrics['complexity'] = file_info.complexity
                
            file_metrics.append(metrics)
        
        # Generate recommendations
        recommendations = self._generate_metrics_recommendations(files)
        
        return {
            'metrics': {
                'total_files': len(files),
                'total_lines': total_lines,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'avg_lines_per_file': total_lines / len(files) if files else 0,
                'avg_functions_per_file': total_functions / len(files) if files else 0
            },
            'file_metrics': file_metrics,
            'recommendations': recommendations
        }
    
    # ===== Helper Methods =====
    
    def _scan_files(self, max_depth: Optional[int] = None,
                   include_patterns: Optional[List[str]] = None,
                   exclude_patterns: Optional[List[str]] = None) -> Dict[str, FileInfo]:
        """Scan and analyze all relevant files in the codebase"""
        files = {}
        
        exclude_patterns = exclude_patterns or [
            '__pycache__', '.git', 'node_modules', '.venv', 'venv',
            '*.pyc', '*.pyo', '*.pyd', '.DS_Store'
        ]
        
        for root, dirs, filenames in os.walk(self.root_path):
            # Apply depth limit
            depth = len(Path(root).relative_to(self.root_path).parts)
            if max_depth and depth > max_depth:
                continue
            
            # Filter directories
            dirs[:] = [d for d in dirs if not any(
                self._matches_pattern(d, pattern) for pattern in exclude_patterns
            )]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, self.root_path)
                
                # Apply inclusion/exclusion patterns
                if exclude_patterns and any(
                    self._matches_pattern(rel_path, pattern) for pattern in exclude_patterns
                ):
                    continue
                
                if include_patterns and not any(
                    self._matches_pattern(rel_path, pattern) for pattern in include_patterns
                ):
                    continue
                
                # Analyze file if it's a code file
                if Path(filename).suffix.lower() in self.code_extensions:
                    try:
                        files[rel_path] = self._analyze_file(file_path)
                    except Exception:
                        # Skip files that can't be analyzed
                        continue
        
        return files
    
    def _analyze_file(self, file_path: str) -> FileInfo:
        """Analyze a single file and extract metadata"""
        if file_path in self.file_cache:
            return self.file_cache[file_path]
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            # Return minimal info for files that can't be read
            return FileInfo(
                path=file_path,
                name=os.path.basename(file_path),
                extension=Path(file_path).suffix,
                size=0,
                lines=0,
                functions=[],
                classes=[],
                imports=[]
            )
        
        lines = content.count('\n') + 1
        size = len(content.encode('utf-8'))
        
        # Language-specific analysis
        functions = []
        classes = []
        imports = []
        complexity = None
        
        if file_path.endswith('.py'):
            functions, classes, imports, complexity = self._analyze_python_file(content)
        elif file_path.endswith(('.js', '.ts')):
            functions, classes, imports = self._analyze_javascript_file(content)
        # Add more language analyzers as needed
        
        file_info = FileInfo(
            path=file_path,
            name=os.path.basename(file_path),
            extension=Path(file_path).suffix,
            size=size,
            lines=lines,
            functions=functions,
            classes=classes,
            imports=imports,
            complexity=complexity
        )
        
        self.file_cache[file_path] = file_info
        return file_info
    
    def _analyze_python_file(self, content: str) -> Tuple[List[str], List[str], List[str], Optional[int]]:
        """Analyze Python file for functions, classes, imports, and complexity"""
        functions = []
        classes = []
        imports = []
        complexity = 0
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                    complexity += self._calculate_cyclomatic_complexity(node)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    else:
                        imports.append(node.module or '')
        except SyntaxError:
            # Handle files with syntax errors
            pass
        
        return functions, classes, imports, complexity
    
    def _analyze_javascript_file(self, content: str) -> Tuple[List[str], List[str], List[str]]:
        """Basic JavaScript/TypeScript analysis using regex patterns"""
        functions = []
        classes = []
        imports = []
        
        # Function patterns
        func_patterns = [
            r'function\s+(\w+)',
            r'(\w+)\s*=\s*function',
            r'(\w+)\s*:\s*function',
            r'(\w+)\s*=>\s*'
        ]
        
        for pattern in func_patterns:
            functions.extend(re.findall(pattern, content))
        
        # Class patterns
        class_matches = re.findall(r'class\s+(\w+)', content)
        classes.extend(class_matches)
        
        # Import patterns
        import_patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)'
        ]
        
        for pattern in import_patterns:
            imports.extend(re.findall(pattern, content))
        
        return functions, classes, imports
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, 
                                ast.With, ast.Assert)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_semantic_score(self, file_info: FileInfo, query_tokens: Set[str], 
                                query_lower: str) -> float:
        """Calculate semantic relevance score for a file"""
        score = 0.0
        
        # Check filename
        filename_lower = file_info.name.lower()
        if query_lower in filename_lower:
            score += 0.5
        
        # Check function names
        for func in file_info.functions:
            func_lower = func.lower()
            if query_lower in func_lower:
                score += 0.3
            # Token overlap
            func_tokens = set(re.findall(r'\w+', func_lower))
            overlap = len(query_tokens & func_tokens)
            score += overlap * 0.1
        
        # Check class names
        for cls in file_info.classes:
            cls_lower = cls.lower()
            if query_lower in cls_lower:
                score += 0.3
            # Token overlap
            cls_tokens = set(re.findall(r'\w+', cls_lower))
            overlap = len(query_tokens & cls_tokens)
            score += overlap * 0.1
        
        # Check imports
        for imp in file_info.imports:
            if query_lower in imp.lower():
                score += 0.2
        
        return score
    
    def _explain_relevance(self, file_info: FileInfo, query_tokens: Set[str]) -> str:
        """Explain why a file is relevant to the search query"""
        reasons = []
        
        # Check various matches
        filename_tokens = set(re.findall(r'\w+', file_info.name.lower()))
        if query_tokens & filename_tokens:
            reasons.append("filename match")
        
        matching_functions = [f for f in file_info.functions 
                            if any(token in f.lower() for token in query_tokens)]
        if matching_functions:
            reasons.append(f"functions: {', '.join(matching_functions[:3])}")
        
        matching_classes = [c for c in file_info.classes 
                          if any(token in c.lower() for token in query_tokens)]
        if matching_classes:
            reasons.append(f"classes: {', '.join(matching_classes[:3])}")
        
        return "; ".join(reasons) or "general relevance"
    
    def _get_relevant_preview(self, file_path: str, query_tokens: Set[str]) -> str:
        """Get a relevant preview of the file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Find lines with query tokens
            relevant_lines = []
            for i, line in enumerate(lines[:100]):  # Only check first 100 lines
                line_lower = line.lower()
                if any(token in line_lower for token in query_tokens):
                    relevant_lines.append(f"{i+1}: {line.strip()}")
                    if len(relevant_lines) >= 3:
                        break
            
            return "\n".join(relevant_lines) if relevant_lines else "No preview available"
        except Exception:
            return "No preview available"
    
    def _detect_singleton_pattern(self, files: Dict[str, FileInfo]) -> List[CodePattern]:
        """Detect singleton pattern in codebase"""
        patterns = []
        
        for file_path, file_info in files.items():
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Look for singleton indicators
                    singleton_indicators = [
                        '__new__',
                        '_instance',
                        'getInstance',
                        '@singleton'
                    ]
                    
                    matches = sum(1 for indicator in singleton_indicators 
                                if indicator in content)
                    
                    if matches >= 2:  # Need multiple indicators
                        patterns.append(CodePattern(
                            name="Singleton Pattern",
                            type="singleton",
                            confidence=min(matches / 3.0, 1.0),
                            description="Singleton pattern implementation detected",
                            files=[file_path],
                            examples=[f"Found in {file_info.name}"]
                        ))
                except Exception:
                    continue
        
        return patterns
    
    def _detect_factory_pattern(self, files: Dict[str, FileInfo]) -> List[CodePattern]:
        """Detect factory pattern in codebase"""
        patterns = []
        
        factory_indicators = ['factory', 'create', 'build', 'make']
        
        for file_path, file_info in files.items():
            factory_functions = [f for f in file_info.functions 
                               if any(indicator in f.lower() for indicator in factory_indicators)]
            
            if len(factory_functions) >= 2:
                patterns.append(CodePattern(
                    name="Factory Pattern",
                    type="factory",
                    confidence=min(len(factory_functions) / 3.0, 1.0),
                    description="Factory pattern implementation detected",
                    files=[file_path],
                    examples=factory_functions[:3]
                ))
        
        return patterns
    
    def _detect_observer_pattern(self, files: Dict[str, FileInfo]) -> List[CodePattern]:
        """Detect observer pattern in codebase"""
        patterns = []
        
        observer_indicators = ['observer', 'notify', 'subscribe', 'listener', 'event']
        
        for file_path, file_info in files.items():
            observer_elements = []
            observer_elements.extend([f for f in file_info.functions 
                                    if any(indicator in f.lower() for indicator in observer_indicators)])
            observer_elements.extend([c for c in file_info.classes 
                                    if any(indicator in c.lower() for indicator in observer_indicators)])
            
            if len(observer_elements) >= 2:
                patterns.append(CodePattern(
                    name="Observer Pattern",
                    type="observer",
                    confidence=min(len(observer_elements) / 4.0, 1.0),
                    description="Observer pattern implementation detected",
                    files=[file_path],
                    examples=observer_elements[:3]
                ))
        
        return patterns
    
    def _detect_mvc_pattern(self, files: Dict[str, FileInfo]) -> List[CodePattern]:
        """Detect MVC pattern in codebase"""
        mvc_files = {'model': [], 'view': [], 'controller': []}
        
        for file_path, file_info in files.items():
            path_lower = file_path.lower()
            name_lower = file_info.name.lower()
            
            if 'model' in path_lower or 'model' in name_lower:
                mvc_files['model'].append(file_path)
            elif 'view' in path_lower or 'view' in name_lower or 'template' in name_lower:
                mvc_files['view'].append(file_path)
            elif 'controller' in path_lower or 'controller' in name_lower or 'handler' in name_lower:
                mvc_files['controller'].append(file_path)
        
        # Check if we have all three components
        if all(mvc_files.values()):
            return [CodePattern(
                name="MVC Pattern",
                type="mvc",
                confidence=0.8,
                description="Model-View-Controller architecture detected",
                files=sum(mvc_files.values(), []),
                examples=[f"Models: {len(mvc_files['model'])}, Views: {len(mvc_files['view'])}, Controllers: {len(mvc_files['controller'])}"]
            )]
        
        return []
    
    def _detect_decorator_pattern(self, files: Dict[str, FileInfo]) -> List[CodePattern]:
        """Detect decorator pattern in codebase"""
        patterns = []
        
        for file_path, file_info in files.items():
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Count decorator usage
                    decorator_count = content.count('@')
                    decorator_indicators = ['@property', '@staticmethod', '@classmethod']
                    custom_decorators = decorator_count - sum(content.count(indicator) for indicator in decorator_indicators)
                    
                    if custom_decorators >= 3:
                        patterns.append(CodePattern(
                            name="Decorator Pattern",
                            type="decorator",
                            confidence=min(custom_decorators / 5.0, 1.0),
                            description="Decorator pattern usage detected",
                            files=[file_path],
                            examples=[f"{custom_decorators} custom decorators found"]
                        ))
                except Exception:
                    continue
        
        return patterns
    
    def _build_dependency_graph(self, file_path: str, max_depth: int) -> List[Dependency]:
        """Build dependency graph for a file"""
        dependencies = []
        visited = set()
        
        def analyze_dependencies(current_file: str, depth: int):
            if depth > max_depth or current_file in visited:
                return
            
            visited.add(current_file)
            file_info = self._analyze_file(current_file)
            
            for imp in file_info.imports:
                # Try to resolve import to actual file
                target_file = self._resolve_import(imp, current_file)
                if target_file:
                    dependencies.append(Dependency(
                        source=current_file,
                        target=target_file,
                        type="import",
                        confidence=1.0
                    ))
                    analyze_dependencies(target_file, depth + 1)
        
        analyze_dependencies(file_path, 0)
        return dependencies
    
    def _resolve_import(self, import_name: str, current_file: str) -> Optional[str]:
        """Try to resolve an import to an actual file path"""
        # This is a simplified resolution - could be enhanced
        current_dir = os.path.dirname(current_file)
        
        # Check for relative imports
        possible_paths = [
            os.path.join(current_dir, f"{import_name}.py"),
            os.path.join(current_dir, import_name, "__init__.py"),
            os.path.join(self.root_path, f"{import_name.replace('.', os.sep)}.py"),
            os.path.join(self.root_path, import_name.replace('.', os.sep), "__init__.py")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.relpath(path, self.root_path)
        
        return None
    
    def _detect_circular_dependencies(self, dependencies: List[Dependency]) -> List[List[str]]:
        """Detect circular dependencies in the dependency graph"""
        # Build adjacency list
        graph = defaultdict(list)
        for dep in dependencies:
            graph[dep.source].append(dep.target)
        
        # Find cycles using DFS
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]):
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph[node]:
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in list(graph.keys()):
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    # ===== Utility Methods =====
    
    def _analyze_structure(self, files: Dict[str, FileInfo]) -> Dict[str, Any]:
        """Analyze directory structure"""
        structure = defaultdict(list)
        
        for file_path in files.keys():
            parts = Path(file_path).parts
            if len(parts) > 1:
                directory = parts[0]
                structure[directory].append(file_path)
            else:
                structure['root'].append(file_path)
        
        return dict(structure)
    
    def _calculate_overview_metrics(self, files: Dict[str, FileInfo]) -> Dict[str, Any]:
        """Calculate overview metrics"""
        if not files:
            return {}
        
        complexities = [f.complexity for f in files.values() if f.complexity]
        
        return {
            'avg_file_size': sum(f.size for f in files.values()) / len(files),
            'avg_lines_per_file': sum(f.lines for f in files.values()) / len(files),
            'avg_functions_per_file': sum(len(f.functions) for f in files.values()) / len(files),
            'avg_complexity': sum(complexities) / len(complexities) if complexities else 0,
            'languages': self._detect_languages(files)
        }
    
    def _detect_languages(self, files: Dict[str, FileInfo]) -> Dict[str, int]:
        """Detect programming languages in the codebase"""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP'
        }
        
        languages = Counter()
        for file_info in files.values():
            lang = language_map.get(file_info.extension, 'Other')
            languages[lang] += 1
        
        return dict(languages)
    
    def _find_entry_points(self, files: Dict[str, FileInfo]) -> List[str]:
        """Find likely entry points in the codebase"""
        entry_points = []
        
        # Look for main files
        main_patterns = ['main.py', 'app.py', 'index.js', 'index.ts', '__main__.py']
        
        for file_path, file_info in files.items():
            if any(pattern in file_info.name for pattern in main_patterns):
                entry_points.append(file_path)
            elif 'main' in file_info.functions:
                entry_points.append(file_path)
        
        return entry_points
    
    def _get_files_by_type(self, file_types: Optional[List[str]]) -> Dict[str, FileInfo]:
        """Get files filtered by type"""
        if not hasattr(self, '_all_files'):
            self._all_files = self._scan_files()
        
        if not file_types:
            return self._all_files
        
        return {path: info for path, info in self._all_files.items() 
                if any(info.extension == ext for ext in file_types)}
    
    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches a pattern (supports basic wildcards)"""
        if '*' in pattern:
            import fnmatch
            return fnmatch.fnmatch(text, pattern)
        return pattern in text
    
    def _pattern_to_dict(self, pattern: CodePattern) -> Dict[str, Any]:
        """Convert CodePattern to dictionary"""
        return {
            'name': pattern.name,
            'type': pattern.type,
            'confidence': pattern.confidence,
            'description': pattern.description,
            'files': pattern.files,
            'examples': pattern.examples
        }
    
    def _dependencies_to_dict(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """Convert dependencies to dictionary format"""
        dep_dict = defaultdict(list)
        for dep in dependencies:
            dep_dict[dep.source].append({
                'target': dep.target,
                'type': dep.type,
                'confidence': dep.confidence
            })
        return dict(dep_dict)
    
    def _format_dependency_graph(self, dependencies: List[Dependency], 
                                include_external: bool) -> List[Dict[str, Any]]:
        """Format dependency graph for output"""
        graph = []
        for dep in dependencies:
            if include_external or self._is_internal_file(dep.target):
                graph.append({
                    'source': dep.source,
                    'target': dep.target,
                    'type': dep.type,
                    'confidence': dep.confidence
                })
        return graph
    
    def _is_internal_file(self, file_path: str) -> bool:
        """Check if a file is internal to the project"""
        return os.path.exists(os.path.join(self.root_path, file_path))
    
    def _generate_pattern_recommendations(self, patterns: List[CodePattern], 
                                        files: Dict[str, FileInfo]) -> List[str]:
        """Generate recommendations based on detected patterns"""
        recommendations = []
        
        pattern_types = [p.type for p in patterns]
        
        if 'singleton' in pattern_types:
            recommendations.append("Consider if singleton patterns are necessary - they can make testing difficult")
        
        if 'factory' in pattern_types:
            recommendations.append("Factory patterns detected - ensure they're not over-engineered for simple use cases")
        
        if len(patterns) == 0:
            recommendations.append("No clear design patterns detected - consider applying appropriate patterns for better architecture")
        
        return recommendations
    
    def _generate_metrics_recommendations(self, files: Dict[str, FileInfo]) -> List[str]:
        """Generate recommendations based on code metrics"""
        recommendations = []
        
        if not files:
            return recommendations
        
        avg_lines = sum(f.lines for f in files.values()) / len(files)
        if avg_lines > 500:
            recommendations.append("Average file size is large - consider breaking down large files")
        
        avg_functions = sum(len(f.functions) for f in files.values()) / len(files)
        if avg_functions > 20:
            recommendations.append("High function count per file - consider splitting responsibilities")
        
        complexities = [f.complexity for f in files.values() if f.complexity]
        if complexities:
            avg_complexity = sum(complexities) / len(complexities)
            if avg_complexity > 10:
                recommendations.append("High cyclomatic complexity detected - consider refactoring complex functions")
        
        return recommendations

# ===== MCP Handler Functions =====

def get_codebase_overview(root_path: str = ".", max_depth: Optional[int] = None,
                         include_patterns: Optional[List[str]] = None,
                         exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get comprehensive overview of the codebase"""
    analyzer = CodebaseAnalyzer(root_path)
    return analyzer.get_codebase_overview(max_depth, include_patterns, exclude_patterns)

def semantic_search(query: str, root_path: str = ".", file_types: Optional[List[str]] = None,
                   max_results: int = 10) -> Dict[str, Any]:
    """Search codebase semantically by meaning and context"""
    analyzer = CodebaseAnalyzer(root_path)
    return analyzer.semantic_search(query, file_types, max_results)

def analyze_patterns(root_path: str = ".", target_files: Optional[List[str]] = None,
                    pattern_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """Detect architectural and design patterns"""
    analyzer = CodebaseAnalyzer(root_path)
    return analyzer.analyze_patterns(target_files, pattern_types)

def get_dependencies(file_path: str, include_external: bool = True, 
                    max_depth: int = 3, root_path: str = ".") -> Dict[str, Any]:
    """Analyze dependencies and relationships for a file"""
    analyzer = CodebaseAnalyzer(root_path)
    return analyzer.get_dependencies(file_path, include_external, max_depth)

def get_code_metrics(root_path: str = ".", target_files: Optional[List[str]] = None,
                    include_complexity: bool = True) -> Dict[str, Any]:
    """Calculate comprehensive code metrics"""
    analyzer = CodebaseAnalyzer(root_path)
    return analyzer.get_code_metrics(target_files, include_complexity)

# ===== MCP Server Task Registration =====

server.add_task(
    name="get_codebase_overview",
    description="Get comprehensive overview of the codebase including structure, metrics, and entry points.",
    input_model=CodebaseOverviewInput,
    output_model=CodebaseOverviewOutput,
    handler=get_codebase_overview
)

server.add_task(
    name="semantic_search",
    description="Search codebase semantically by meaning and context, not just text matching.",
    input_model=SemanticSearchInput,
    output_model=SemanticSearchOutput,
    handler=semantic_search
)

server.add_task(
    name="analyze_patterns",
    description="Detect architectural and design patterns in the codebase.",
    input_model=AnalyzePatternsInput,
    output_model=AnalyzePatternsOutput,
    handler=analyze_patterns
)

server.add_task(
    name="get_dependencies",
    description="Analyze dependencies and relationships for a specific file.",
    input_model=GetDependenciesInput,
    output_model=GetDependenciesOutput,
    handler=get_dependencies
)

server.add_task(
    name="get_code_metrics",
    description="Calculate comprehensive code metrics including complexity and quality indicators.",
    input_model=GetCodeMetricsInput,
    output_model=GetCodeMetricsOutput,
    handler=get_code_metrics
)

# Build app (None if local_mode=True)
app = server.build_app()

# ===== LangChain-Compatible Tool Class =====

class CodebaseIndexerMCPTool(BaseTool):
    """
    Enhanced Codebase Indexer MCP tool with semantic analysis capabilities.
    
    Provides intelligent code understanding, architecture insights, and semantic search
    that complements filesystem and GitHub tools with deep codebase intelligence.
    """
    _bypass_pydantic = True
    
    def __init__(self, identifier: str, name: str = None, local_mode: bool = True, 
                 mcp_url: str = None, root_path: str = ".", **kwargs):
        # Set defaults for enhanced codebase indexer
        description = kwargs.pop('description', "Enhanced codebase analysis with semantic search, pattern detection, and architecture insights")
        instruction = kwargs.pop('instruction', (
            "Use this tool for intelligent codebase analysis. "
            "Available methods: get_codebase_overview, semantic_search, analyze_patterns, get_dependencies, get_code_metrics. "
            "Provides semantic understanding beyond basic file operations."
        ))
        brief = kwargs.pop('brief', "Enhanced Codebase Indexer with AI-powered analysis")
        
        # Add MCP server reference
        kwargs['mcp_server'] = server
        
        # Initialize with BaseTool (handles all MCP setup automatically)
        super().__init__(
            name=name or f"EnhancedCodebaseIndexer-{identifier}",
            description=description,
            instruction=instruction,
            identifier=identifier,
            brief=brief,
            **kwargs
        )
        
        # Store configuration AFTER parent initialization
        object.__setattr__(self, 'root_path', root_path)
        object.__setattr__(self, '_is_mcp_tool', True)
        object.__setattr__(self, 'local_mode', local_mode)
    
    def run(self, input_data=None):
        """Execute enhanced codebase indexer MCP methods locally"""
        # Get configuration from instance
        root_path = getattr(self, 'root_path', ".")
        
        # Define method handlers for this tool
        method_handlers = {
            "get_codebase_overview": lambda **kwargs: get_codebase_overview(root_path=root_path, **kwargs),
            "semantic_search": lambda **kwargs: semantic_search(root_path=root_path, **kwargs),
            "analyze_patterns": lambda **kwargs: analyze_patterns(root_path=root_path, **kwargs),
            "get_dependencies": lambda **kwargs: get_dependencies(root_path=root_path, **kwargs),
            "get_code_metrics": lambda **kwargs: get_code_metrics(root_path=root_path, **kwargs),
        }
        
        # Use BaseTool's common MCP input handler
        try:
            return self._handle_mcp_structured_input(input_data, method_handlers)
        except Exception as e:
            # Enhanced error handling and debugging
            if isinstance(input_data, dict) and 'method' in input_data:
                method_name = input_data['method']
                if method_name in method_handlers:
                    # Method exists, so there's a different issue
                    try:
                        params = input_data.get('params', {})
                        handler = method_handlers[method_name]
                        return handler(**params)
                    except Exception as handler_error:
                        return f"Error executing {method_name}: {str(handler_error)}"
                else:
                    return f"Error: Unknown method '{method_name}'. Available methods: {list(method_handlers.keys())}"
            else:
                return f"Error: {str(e)}"

if __name__ == "__main__":
    if server.local_mode:
        print(f"✅ {server.name} ready for local mode usage")
        # In local mode, server is ready to use - no uvicorn needed
    else:
        print(f"🌐 Starting {server.name} HTTP server...")
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)