"""
Session Management Error Handling for LangSwarm

Provides clear, actionable error messages for session-related issues
including storage failures, memory problems, and session lifecycle errors.
"""

from typing import List, Optional, Dict, Any
from langswarm.core.errors import LangSwarmError, ErrorContext


class SessionError(LangSwarmError):
    """Base class for all session-related errors."""
    pass


class SessionNotFoundError(SessionError):
    """Raised when a session cannot be found."""
    
    def __init__(
        self,
        session_id: str,
        available_sessions: Optional[List[str]] = None
    ):
        self.session_id = session_id
        self.available_sessions = available_sessions or []
        
        message = f"Session '{session_id}' not found"
        
        context = ErrorContext(
            component="SessionManager",
            operation="get_session",
            metadata={
                "session_id": session_id,
                "available_count": len(self.available_sessions)
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for session not found."""
        suggestions = [
            f"Session '{self.session_id}' does not exist.",
            "",
            "Create a new session:"
        ]
        
        # Different session creation examples
        suggestions.extend([
            "  # Simple session",
            "  session = create_session()",
            "",
            "  # Session with memory",
            "  session = create_session(memory_enabled=True)",
            "",
            "  # Session with custom storage",
            "  session = create_session(storage_backend='redis')"
        ])
        
        if self.available_sessions:
            suggestions.extend([
                "",
                f"Available sessions ({len(self.available_sessions)}):",
                *[f"  • {session}" for session in self.available_sessions[:5]]
            ])
            
            if len(self.available_sessions) > 5:
                suggestions.append(f"  ... and {len(self.available_sessions) - 5} more")
        
        return "\n".join(suggestions)


class SessionStorageError(SessionError):
    """Raised when session storage operations fail."""
    
    def __init__(
        self,
        operation: str,
        backend: str,
        error: Optional[Exception] = None,
        session_id: Optional[str] = None
    ):
        self.operation = operation
        self.backend = backend
        self.original_error = error
        self.session_id = session_id
        
        message = f"Session storage {operation} failed"
        if session_id:
            message += f" for session '{session_id}'"
        message += f" (backend: {backend})"
        
        context = ErrorContext(
            component="SessionStorage",
            operation=operation,
            metadata={
                "backend": backend,
                "session_id": session_id,
                "error_type": type(error).__name__ if error else None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for storage errors."""
        suggestions = [f"Fix {self.backend} storage issue:"]
        
        if self.backend == "sqlite":
            suggestions.extend([
                "",
                "SQLite storage troubleshooting:",
                "• Check file permissions",
                "• Ensure directory exists",
                "• Verify disk space available",
                "• Check for database corruption"
            ])
        elif self.backend == "redis":
            suggestions.extend([
                "",
                "Redis storage troubleshooting:",
                "• Verify Redis server is running",
                "• Check connection settings (host, port, password)",
                "• Test connection: redis-cli ping",
                "• Check Redis memory limits"
            ])
        elif self.backend == "bigquery":
            suggestions.extend([
                "",
                "BigQuery storage troubleshooting:",
                "• Verify Google Cloud credentials",
                "• Check dataset permissions",
                "• Ensure project quota is available",
                "• Verify table schema compatibility"
            ])
        elif self.backend == "memory":
            suggestions.extend([
                "",
                "Memory storage troubleshooting:",
                "• Check available system memory",
                "• Consider using persistent storage instead",
                "• Monitor memory usage patterns"
            ])
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "permission" in error_str or "access" in error_str:
                suggestions.extend([
                    "",
                    "Permission issue detected:",
                    "• Check file/directory permissions",
                    "• Verify user has required access",
                    "• Run with appropriate privileges if needed"
                ])
            elif "network" in error_str or "connection" in error_str:
                suggestions.extend([
                    "",
                    "Network/connection issue detected:",
                    "• Check network connectivity",
                    "• Verify service endpoints",
                    "• Check firewall settings"
                ])
            elif "timeout" in error_str:
                suggestions.extend([
                    "",
                    "Timeout issue detected:",
                    "• Increase timeout settings",
                    "• Check service performance",
                    "• Consider retry mechanisms"
                ])
        
        suggestions.extend([
            "",
            "Fallback option:",
            "  # Use in-memory storage for development",
            "  session = create_session(storage_backend='memory')"
        ])
        
        return "\n".join(suggestions)


class SessionMemoryError(SessionError):
    """Raised when session memory operations fail."""
    
    def __init__(
        self,
        operation: str,
        memory_backend: str,
        error: Optional[Exception] = None,
        session_id: Optional[str] = None
    ):
        self.operation = operation
        self.memory_backend = memory_backend
        self.original_error = error
        self.session_id = session_id
        
        message = f"Session memory {operation} failed (backend: {memory_backend})"
        if session_id:
            message += f" for session '{session_id}'"
        
        context = ErrorContext(
            component="SessionMemory",
            operation=operation,
            metadata={
                "memory_backend": memory_backend,
                "session_id": session_id,
                "error_type": type(error).__name__ if error else None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for memory errors."""
        suggestions = [f"Fix {self.memory_backend} memory issue:"]
        
        memory_troubleshooting = {
            "chromadb": [
                "• Verify ChromaDB installation: pip install chromadb",
                "• Check if collection exists",
                "• Verify embedding model compatibility",
                "• Monitor ChromaDB logs for errors"
            ],
            "redis": [
                "• Verify Redis server is running",
                "• Check Redis memory configuration",
                "• Test basic Redis operations",
                "• Verify Redis persistence settings"
            ],
            "bigquery": [
                "• Check Google Cloud authentication",
                "• Verify BigQuery dataset permissions",
                "• Ensure vector search is enabled",
                "• Check query quotas and limits"
            ],
            "qdrant": [
                "• Verify Qdrant server connection",
                "• Check collection configuration",
                "• Verify vector dimensions match",
                "• Monitor Qdrant server logs"
            ],
            "sqlite": [
                "• Check SQLite file permissions",
                "• Verify FTS extension is available",
                "• Check database file integrity",
                "• Ensure sufficient disk space"
            ]
        }
        
        if self.memory_backend in memory_troubleshooting:
            suggestions.extend(["", f"{self.memory_backend.title()} troubleshooting:"])
            suggestions.extend(memory_troubleshooting[self.memory_backend])
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "embedding" in error_str:
                suggestions.extend([
                    "",
                    "Embedding issue detected:",
                    "• Check embedding model configuration",
                    "• Verify text preprocessing",
                    "• Check vector dimensions",
                    "• Validate input text format"
                ])
            elif "index" in error_str or "search" in error_str:
                suggestions.extend([
                    "",
                    "Search/index issue detected:",
                    "• Rebuild the search index",
                    "• Check query format",
                    "• Verify collection schema",
                    "• Monitor index size and performance"
                ])
        
        suggestions.extend([
            "",
            "For development, use simple memory:",
            "  # In-memory storage (no persistence)",
            "  session = create_session(memory_backend='memory')",
            "",
            "  # SQLite for local persistence",
            "  session = create_session(memory_backend='sqlite')"
        ])
        
        return "\n".join(suggestions)


class SessionLifecycleError(SessionError):
    """Raised when session lifecycle operations fail."""
    
    def __init__(
        self,
        operation: str,
        session_id: str,
        current_state: str,
        expected_state: Optional[str] = None,
        reason: Optional[str] = None
    ):
        self.operation = operation
        self.session_id = session_id
        self.current_state = current_state
        self.expected_state = expected_state
        self.reason = reason
        
        message = f"Cannot {operation} session '{session_id}' in state '{current_state}'"
        if expected_state:
            message += f" (expected: {expected_state})"
        if reason:
            message += f": {reason}"
        
        context = ErrorContext(
            component="SessionLifecycle",
            operation=operation,
            metadata={
                "session_id": session_id,
                "current_state": current_state,
                "expected_state": expected_state,
                "reason": reason
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for lifecycle errors."""
        suggestions = [f"Fix session lifecycle issue:"]
        
        state_transitions = {
            "created": ["active", "closed"],
            "active": ["paused", "closed"],
            "paused": ["active", "closed"],
            "closed": ["create new session"]
        }
        
        if self.current_state in state_transitions:
            valid_transitions = state_transitions[self.current_state]
            suggestions.extend([
                "",
                f"From '{self.current_state}' state, you can:",
                *[f"  • {transition}" for transition in valid_transitions]
            ])
        
        operation_fixes = {
            "activate": [
                "Ensure session is not already active",
                "Check if session was properly created",
                "Verify session storage is accessible"
            ],
            "pause": [
                "Session must be active to pause",
                "Save any pending operations first",
                "Ensure graceful pause is possible"
            ],
            "close": [
                "Finish any pending operations",
                "Save session state if needed",
                "Release resources properly"
            ],
            "save": [
                "Ensure session is in a saveable state",
                "Check storage backend availability",
                "Verify permissions for write operations"
            ]
        }
        
        if self.operation in operation_fixes:
            suggestions.extend([
                "",
                f"To {self.operation} a session:",
                *[f"  • {fix}" for fix in operation_fixes[self.operation]]
            ])
        
        suggestions.extend([
            "",
            "Session lifecycle example:",
            "  session = create_session()      # State: created",
            "  session.activate()              # State: active",
            "  # ... use session ...",
            "  session.pause()                 # State: paused",
            "  session.activate()              # State: active",
            "  session.close()                 # State: closed"
        ])
        
        return "\n".join(suggestions)


class SessionConfigurationError(SessionError):
    """Raised when session configuration is invalid."""
    
    def __init__(
        self,
        config_issue: str,
        session_config: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ):
        self.config_issue = config_issue
        self.session_config = session_config
        self.field = field
        
        message = f"Invalid session configuration: {config_issue}"
        if field:
            message += f" (field: {field})"
        
        context = ErrorContext(
            component="SessionConfiguration",
            operation="validate_config",
            metadata={
                "issue": config_issue,
                "field": field,
                "has_config": session_config is not None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for configuration errors."""
        suggestions = ["Fix session configuration:"]
        
        if "storage" in self.config_issue.lower():
            suggestions.extend([
                "",
                "Valid storage backends:",
                "  • memory - In-memory only (fast, no persistence)",
                "  • sqlite - Local file storage (good for development)",
                "  • redis - Redis backend (good for production)",
                "  • bigquery - Google BigQuery (enterprise scale)"
            ])
        
        if "memory" in self.config_issue.lower():
            suggestions.extend([
                "",
                "Valid memory backends:",
                "  • memory - Simple in-memory storage",
                "  • sqlite - SQLite with FTS",
                "  • chromadb - Vector database",
                "  • redis - Redis with search",
                "  • qdrant - Qdrant vector database",
                "  • bigquery - BigQuery vector search"
            ])
        
        if "timeout" in self.config_issue.lower():
            suggestions.extend([
                "",
                "Timeout configuration:",
                "  • session_timeout: 3600  # seconds",
                "  • operation_timeout: 30  # seconds",
                "  • storage_timeout: 10    # seconds"
            ])
        
        suggestions.extend([
            "",
            "Example valid session configuration:",
            "```yaml",
            "session:",
            "  storage_backend: sqlite",
            "  memory_backend: sqlite",
            "  auto_save: true",
            "  session_timeout: 3600",
            "  max_memory_size: 100MB",
            "```"
        ])
        
        return "\n".join(suggestions)


# Convenience functions for creating common session errors
def session_not_found(session_id: str, available: Optional[List[str]] = None) -> SessionNotFoundError:
    """Create a SessionNotFoundError with context."""
    return SessionNotFoundError(session_id, available)


def storage_failed(operation: str, backend: str, error: Optional[Exception] = None) -> SessionStorageError:
    """Create a SessionStorageError with context."""
    return SessionStorageError(operation, backend, error)


def memory_failed(operation: str, backend: str, error: Optional[Exception] = None) -> SessionMemoryError:
    """Create a SessionMemoryError with context."""
    return SessionMemoryError(operation, backend, error)


def lifecycle_failed(
    operation: str, 
    session_id: str, 
    current_state: str,
    expected_state: Optional[str] = None
) -> SessionLifecycleError:
    """Create a SessionLifecycleError with context."""
    return SessionLifecycleError(operation, session_id, current_state, expected_state)


def config_invalid(issue: str, field: Optional[str] = None) -> SessionConfigurationError:
    """Create a SessionConfigurationError with context."""
    return SessionConfigurationError(issue, field=field)