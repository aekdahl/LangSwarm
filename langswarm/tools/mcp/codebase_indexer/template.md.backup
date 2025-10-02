# Enhanced Codebase Indexer MCP Tool

## Tool Description
Enhanced codebase analysis with semantic search, pattern detection, architecture insights, and intelligent code understanding. Provides deep code intelligence that complements filesystem and GitHub tools.

## Available Methods

### get_codebase_overview
Get comprehensive overview of the codebase including structure, metrics, and entry points.

**Parameters:**
- `root_path` (string, optional): Root directory to analyze (default: ".")
- `max_depth` (integer, optional): Maximum directory depth to scan
- `include_patterns` (array, optional): File patterns to include
- `exclude_patterns` (array, optional): File patterns to exclude

**Returns:**
- `summary`: High-level codebase statistics and overview
- `structure`: Directory structure analysis
- `metrics`: Code quality and complexity metrics
- `entry_points`: Identified main files and entry points

### semantic_search
Search codebase semantically by meaning and context, not just text matching.

**Parameters:**
- `query` (string, required): Search query describing what you're looking for
- `root_path` (string, optional): Root directory to search (default: ".")
- `file_types` (array, optional): File extensions to include (e.g., [".py", ".js"])
- `max_results` (integer, optional): Maximum number of results (default: 10)

**Returns:**
- `results`: Array of relevant files with scores and explanations
- `total_found`: Total number of matching files
- `search_summary`: Description of search results

### analyze_patterns
Detect architectural and design patterns in the codebase.

**Parameters:**
- `root_path` (string, optional): Root directory to analyze (default: ".")
- `target_files` (array, optional): Specific files to analyze
- `pattern_types` (array, optional): Pattern types to detect (singleton, factory, observer, mvc, decorator)

**Returns:**
- `patterns`: Detected patterns with confidence scores
- `recommendations`: Architecture improvement suggestions
- `summary`: Pattern detection summary statistics

### get_dependencies
Analyze dependencies and relationships for a specific file.

**Parameters:**
- `file_path` (string, required): Path to the file to analyze
- `include_external` (boolean, optional): Include external dependencies (default: true)
- `max_depth` (integer, optional): Maximum dependency depth to traverse (default: 3)

**Returns:**
- `dependencies`: Structured dependency information
- `dependency_graph`: Graph representation of dependencies
- `circular_dependencies`: Detected circular dependency cycles

### get_code_metrics
Calculate comprehensive code metrics including complexity and quality indicators.

**Parameters:**
- `root_path` (string, optional): Root directory to analyze (default: ".")
- `target_files` (array, optional): Specific files to analyze
- `include_complexity` (boolean, optional): Include complexity calculations (default: true)

**Returns:**
- `metrics`: Overall codebase metrics
- `file_metrics`: Per-file metrics and statistics
- `recommendations`: Code quality improvement suggestions

## Intent-Based Usage Examples

### Architecture Analysis
```json
{
  "mcp": {
    "tool": "codebase_indexer",
    "intent": "analyze_architecture",
    "context": "I want to understand the overall architecture and design patterns in this codebase"
  }
}
```

### Find Authentication Code
```json
{
  "mcp": {
    "tool": "codebase_indexer",
    "method": "semantic_search",
    "params": {
      "query": "authentication login user validation",
      "max_results": 5
    }
  }
}
```

### Code Quality Assessment
```json
{
  "mcp": {
    "tool": "codebase_indexer",
    "intent": "assess_quality",
    "context": "Evaluate code quality and identify areas that need improvement"
  }
}
```

### Dependency Analysis
```json
{
  "mcp": {
    "tool": "codebase_indexer",
    "method": "get_dependencies",
    "params": {
      "file_path": "src/main.py",
      "max_depth": 2
    }
  }
}
```

## Direct Method Usage Examples

### Codebase Overview
```json
{
  "mcp": {
    "tool": "codebase_indexer",
    "method": "get_codebase_overview",
    "params": {
      "max_depth": 3,
      "exclude_patterns": ["*.test.js", "__pycache__"]
    }
  }
}
```

### Pattern Detection
```json
{
  "mcp": {
    "tool": "codebase_indexer",
    "method": "analyze_patterns",
    "params": {
      "pattern_types": ["singleton", "factory", "observer"]
    }
  }
}
```

### Semantic Code Search
```json
{
  "mcp": {
    "tool": "codebase_indexer",
    "method": "semantic_search",
    "params": {
      "query": "database connection pooling",
      "file_types": [".py", ".js"],
      "max_results": 8
    }
  }
}
```

### Code Metrics Analysis
```json
{
  "mcp": {
    "tool": "codebase_indexer",
    "method": "get_code_metrics",
    "params": {
      "include_complexity": true
    }
  }
}
```

## Tool Integration Patterns

### With Filesystem Tool
1. Use `semantic_search` to find relevant files
2. Use `filesystem.read_file` to get implementation details
3. Use `get_dependencies` to understand relationships

### With GitHub Tool
1. Use `get_codebase_overview` for current state
2. Use `github.get_file_history` for evolution context
3. Use `analyze_patterns` to understand design decisions

### Comprehensive Analysis Chain
1. `get_codebase_overview` → Understand structure
2. `semantic_search` → Find specific functionality
3. `get_dependencies` → Map relationships
4. `analyze_patterns` → Identify design patterns
5. `get_code_metrics` → Assess quality

## Capabilities and Limitations

### Strengths
- Semantic understanding beyond text matching
- Architecture pattern detection
- Dependency relationship mapping
- Code quality and complexity analysis
- Multi-language support (Python, JavaScript, TypeScript, Java, C++, etc.)
- Integration with other LangSwarm tools

### Limitations
- Analysis quality depends on code structure and documentation
- Complex patterns may require manual verification
- Large codebases may take time to analyze
- Language-specific features vary by implementation
- Semantic search uses heuristics, not deep learning embeddings

### Best Practices
- Start with `get_codebase_overview` for context
- Use specific queries for `semantic_search`
- Combine multiple methods for comprehensive analysis
- Verify pattern detection results manually
- Use with filesystem and GitHub tools for complete understanding

### Performance Notes
- Results are cached for better performance
- Large codebases benefit from targeted analysis
- Use `max_depth` and patterns to limit scope
- Consider analyzing specific directories for focused results

### Error Handling
- Gracefully handles unreadable files
- Skips binary and non-text files
- Provides meaningful error messages
- Continues analysis even if some files fail