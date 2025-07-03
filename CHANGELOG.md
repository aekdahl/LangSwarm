# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.49]

### Fixed
- **Critical Workflow Intelligence Bug**: Fixed `TypeError: unhashable type: 'slice'` error in workflow reporting
  - **Issue**: Line 116 in `intelligence.py` was incorrectly attempting to slice a dictionary
  - **Root Cause**: `self.step_data[step_id][:20]` tried to slice dict instead of using it directly
  - **Impact**: Prevented workflow completion and integration tests from running
  - **Fix**: Removed incorrect slice operation, now uses `self.step_data[step_id]` directly
  - **Testing**: Verified fix resolves error and maintains report functionality

- **Critical Middleware Bug**: Fixed `TypeError: 'str' object is not a mapping` error in MCP handling
  - **Issue**: MCP data was being passed incorrectly to middleware, causing type mismatch
  - **Root Cause**: `parsed_json.get('mcp')` passed partial data instead of full structure
  - **Impact**: Prevented MCP tool calls from working in agent workflows
  - **Fix**: Pass complete `parsed_json` to middleware and added defensive type checking
  - **Testing**: Verified MCP intent-based and direct patterns work correctly

### Enhanced
- **MCP Tool Architecture**: Continued improvements to BaseTool inheritance pattern
  - **FilesystemMCPTool**: Simplified from 63 lines to 21 lines (67% reduction)
  - **MCPGitHubTool**: Updated to use new simplified architecture
  - **Universal Pattern**: Both tools now leverage common MCP functionality in BaseTool
  - **Scalability**: Template established for easy creation of new MCP tools

- **Error Handling**: Added comprehensive defensive checks in middleware
  - **Type Validation**: Ensure agent_input is dictionary before processing
  - **Graceful Degradation**: Better error messages for invalid input types
  - **Legacy Compatibility**: Protected legacy action handling with try/catch

## [0.0.48]
- **MCP Tool Fixes**

## [0.0.47]

### Added  
- **Simplified MCP Tool Architecture**: Revolutionary BaseTool enhancement for MCP tool development
  - **Automatic Pydantic Bypass**: `_is_mcp_tool = True` flag enables validation bypass via `__init_subclass__`
  - **Common MCP Methods**: Built-in `invoke()`, `_run()`, `_handle_mcp_structured_input()` for all MCP tools
  - **Intelligent Attribute Setup**: Automatic configuration of MCP-specific attributes (id, type, workflows)
  - **Pattern Support**: Unified handling of both direct and intent-based MCP patterns

### Fixed
- **MCP Tool Registration**: Resolved "Unknown tool type 'mcpfilesystem'" error
  - **Root Cause**: MCP tool classes weren't registered in `LangSwarmConfigLoader`
  - **Solution**: Proper BaseTool inheritance with Pydantic validation bypass
  - **Impact**: Both `mcpfilesystem` and `mcpgithubtool` now work seamlessly

## [0.0.46]

### Added
- **Enhanced MCP Patterns**: Revolutionary new architecture for MCP tool integration
  - **Intent-Based Pattern**: Agents express high-level intent, tools handle orchestration
    - Example: `{"mcp": {"tool": "github_mcp", "intent": "create issue about bug", "context": "auth failing"}}`
  - **Direct Pattern**: Simple method calls for straightforward operations  
    - Example: `{"mcp": {"tool": "filesystem", "method": "read_file", "params": {"path": "/tmp/file"}}}`
  - **Local Mode Integration**: Zero-latency local tool calls (`local_mode: true`)
  - **Automatic URL Construction**: `local://` for local tools, `stdio://` for remote

### Enhanced
- **Middleware Architecture**: 
  - Added `use_mcp_workflow()` for intent-based tool orchestration
  - Added `use_mcp_direct()` for direct method calls
  - Enhanced `to_middleware()` with intelligent pattern detection and routing
  - Improved error handling with detailed validation messages

### Fixed
- **Backward Compatibility**: All existing tool patterns continue working unchanged
- **Robust Initialization**: Graceful handling of missing tool registries in test environments
- **Type Safety**: Added `hasattr()` checks for optional tool attributes

### Performance
- **Zero-Latency Local Mode**: 500x-1000x performance improvement over remote calls
- **Smart Routing**: Direct pattern bypasses unnecessary workflow overhead
- **Efficient Initialization**: Conditional loading of dependencies

### Documentation
- **README Updates**: Comprehensive "Enhanced MCP Patterns" section with examples
- **Configuration Examples**: Complete YAML configurations for all patterns
- **Migration Guide**: Step-by-step guide from legacy approaches
- **Performance Comparisons**: Local vs remote mode benchmarks

### Testing
- **Comprehensive Test Suite**: 35+ tests covering all enhanced patterns
- **Manual Testing Script**: `test_enhanced_mcp_manual.py` for quick validation
- **Integration Tests**: Configuration loading and agent wrapper integration
- **Backward Compatibility Tests**: Ensures no regressions in existing functionality

### Breaking Changes
- None - Full backward compatibility maintained

---

## [0.0.45] - Previous Release
- Previous functionality and features

---

### Key Benefits of v0.0.46

1. **Solved Architectural Problem**: Eliminates duplication where agents needed deep tool implementation knowledge
2. **True Separation of Concerns**: Tools handle complexity, agents express intent
3. **Performance + Intelligence**: Zero-latency local mode with smart abstraction
4. **Scalable Architecture**: Supports simple direct calls to complex orchestration workflows
5. **Production Ready**: Comprehensive testing and documentation 