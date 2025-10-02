#!/usr/bin/env python3
"""
LangSwarm V2 Error System Demonstration

This script demonstrates the new V2 error system with:
- Structured error hierarchy
- Rich error context
- Severity-based routing
- Recovery mechanisms
- Backward compatibility
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langswarm.v2.core.errors import (
    LangSwarmError,
    ConfigurationError,
    AgentError,
    ToolError,
    CriticalError,
    ErrorContext,
    ErrorSeverity,
    ErrorCategory,
    handle_error,
    get_error_handler,
    register_recovery_strategy
)

def demo_basic_errors():
    """Demonstrate basic error creation and handling"""
    print("\n🔧 === BASIC ERROR DEMONSTRATION ===")
    
    # Create a configuration error with context
    context = ErrorContext(
        component="config_loader",
        operation="load_yaml",
        user_id="demo_user",
        session_id="demo_session_123"
    )
    
    config_error = ConfigurationError(
        "Configuration file not found: config.yaml",
        context=context,
        suggestion="Check if the file exists and has correct permissions"
    )
    
    print(f"Configuration Error:\n{config_error}")
    print(f"\nError Dictionary: {config_error.to_dict()}")
    
    # Handle the error
    result = handle_error(config_error, "demo_component")
    print(f"Handler result (should continue): {result}")

def demo_error_conversion():
    """Demonstrate automatic error conversion"""
    print("\n🔄 === ERROR CONVERSION DEMONSTRATION ===")
    
    # Standard Python exceptions get converted to LangSwarm errors
    try:
        raise ValueError("Invalid API key format")
    except Exception as e:
        result = handle_error(e, "auth_component")
        print(f"Converted error handled, should continue: {result}")
    
    try:
        raise ConnectionError("Network timeout after 30 seconds")
    except Exception as e:
        result = handle_error(e, "network_component")
        print(f"Network error handled, should continue: {result}")

def demo_critical_errors():
    """Demonstrate critical error handling"""
    print("\n🚨 === CRITICAL ERROR DEMONSTRATION ===")
    
    # Critical errors halt the system
    critical_error = CriticalError(
        "Database connection completely failed",
        context=ErrorContext("database", "connect"),
        suggestion="Check database server status and connection credentials"
    )
    
    print(f"Critical Error:\n{critical_error}")
    result = handle_error(critical_error, "database_component")
    print(f"Handler result (should halt): {result}")

def demo_recovery_strategies():
    """Demonstrate recovery strategies"""
    print("\n🔄 === RECOVERY STRATEGY DEMONSTRATION ===")
    
    # Register a recovery strategy for tool errors
    def tool_recovery(error):
        print(f"🛠️ Attempting recovery for: {error.message}")
        print("🔧 Recovery: Restarting tool service...")
        return True  # Recovery successful
    
    register_recovery_strategy("tool:CriticalError", tool_recovery)
    
    # Create a critical tool error
    tool_error = CriticalError(
        "Tool execution engine crashed",
        category=ErrorCategory.TOOL,
        context=ErrorContext("tool_engine", "execute"),
        suggestion="Try restarting the tool service"
    )
    
    # This should attempt recovery
    result = handle_error(tool_error, "tool_component")
    print(f"Handler result after recovery (should continue): {result}")

def demo_error_statistics():
    """Demonstrate error statistics and monitoring"""
    print("\n📊 === ERROR STATISTICS DEMONSTRATION ===")
    
    # Generate some errors
    errors = [
        ConfigurationError("Config error 1"),
        ConfigurationError("Config error 2"),
        AgentError("Agent error 1"),
        ToolError("Tool error 1"),
    ]
    
    for error in errors:
        handle_error(error, f"component_{errors.index(error)}")
    
    # Get statistics
    stats = get_error_handler().get_error_statistics()
    
    print("Error Statistics:")
    print(f"  Total errors: {stats['total_errors']}")
    print(f"  Error counts by type: {stats['error_counts']}")
    print(f"  Critical error count: {stats['critical_error_count']}")
    print(f"  Circuit breaker active: {stats['circuit_breaker_active']}")
    print(f"  Recent errors: {len(stats['recent_errors'])}")

def demo_legacy_compatibility():
    """Demonstrate backward compatibility with V1 errors"""
    print("\n🔄 === LEGACY COMPATIBILITY DEMONSTRATION ===")
    
    # Import legacy error aliases
    from langswarm.v2.core.errors.types import (
        ConfigurationNotFoundError,
        InvalidAgentBehaviorError,
        UnknownToolError,
        AgentToolError
    )
    
    # These are aliases that work exactly like the new errors
    legacy_errors = [
        ConfigurationNotFoundError("Old-style config error"),
        InvalidAgentBehaviorError("Old-style agent error"),
        UnknownToolError("Old-style tool error"),
        AgentToolError("Old-style agent tool error")
    ]
    
    print("Legacy error compatibility:")
    for error in legacy_errors:
        print(f"  {error.__class__.__name__}: {error.message} -> {error.category.value}")
        handle_error(error, "legacy_component")

def main():
    """Main demonstration function"""
    print("🚀 LangSwarm V2 Error System Demonstration")
    print("=" * 50)
    
    try:
        demo_basic_errors()
        demo_error_conversion()
        demo_critical_errors()
        demo_recovery_strategies()
        demo_error_statistics()
        demo_legacy_compatibility()
        
        print("\n✅ === DEMONSTRATION COMPLETE ===")
        print("V2 Error System Features Demonstrated:")
        print("  ✅ Structured error hierarchy")
        print("  ✅ Rich error context")
        print("  ✅ Automatic error conversion")
        print("  ✅ Severity-based routing")
        print("  ✅ Recovery strategies")
        print("  ✅ Error statistics and monitoring")
        print("  ✅ Backward compatibility")
        print("\n🎯 Error System Phase 1 Implementation: COMPLETE!")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
