- [x] **Fixed**: 2025-07-03 17:30:18,242 - chat_response_agent - ERROR - Agent chat_response_agent: MCP tool filesystem error: local variable 'pkg_dir' referenced before assignment
ERROR:chat_response_agent:Agent chat_response_agent: MCP tool filesystem error: local variable 'pkg_dir' referenced before assignment

**Resolution**: Fixed `pkg_dir` variable reference bug in `langswarm/core/wrappers/middleware.py:_find_workflow_path()` method. The variable is now properly defined in both the importlib.resources code path and the fallback inspection path.

