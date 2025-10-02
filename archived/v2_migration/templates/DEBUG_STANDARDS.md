# LangSwarm V2 Debug Standards

**Purpose**: Define comprehensive debug mode requirements for all V2 migration tasks to ensure excellent developer experience and troubleshooting capabilities.

---

## 🎯 **Debug Philosophy**

### **Core Principles**
1. **Developer-Friendly**: Debug mode should make developers' lives easier
2. **Production-Safe**: Debug features must be safely disabled in production
3. **Comprehensive Information**: Provide all information needed for troubleshooting
4. **Performance-Aware**: Debug mode overhead must be reasonable
5. **Actionable Output**: Debug information should lead to clear actions

### **Debug Goals**
- **Rapid Troubleshooting**: Quickly identify and resolve issues
- **System Understanding**: Help developers understand how the system works
- **Development Efficiency**: Reduce time spent debugging
- **Quality Assurance**: Catch issues before they reach production

---

## 📋 **Debug Mode Requirements**

### **1. Verbose Logging**
**Purpose**: Detailed logging for development and troubleshooting

**Requirements**:
- **Multiple Levels**: Support different verbosity levels
- **Structured Output**: JSON and human-readable formats
- **Context Preservation**: Maintain context across log entries
- **Performance Impact**: Minimal overhead when disabled

**Implementation Pattern**:
```python
# langswarm/v2/core/observability/debug_logging.py
import logging
import json
import sys
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

class DebugLevel(Enum):
    """Debug logging levels"""
    TRACE = 5      # Extremely detailed execution flow
    DEBUG = 10     # Detailed debugging information
    INFO = 20      # General information
    WARNING = 30   # Warning messages
    ERROR = 40     # Error messages
    CRITICAL = 50  # Critical system errors

class DebugLogger:
    """Enhanced logging system for debug mode"""
    
    def __init__(self, name: str, debug_enabled: bool = False):
        self.name = name
        self.debug_enabled = debug_enabled
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up logger with appropriate handlers and formatters"""
        if self.debug_enabled:
            # Console handler with colors
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(DebugLevel.TRACE.value)
            
            # Colored formatter for console
            console_formatter = ColoredFormatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            
            # File handler for persistent logs
            file_handler = logging.FileHandler('debug.log')
            file_handler.setLevel(DebugLevel.DEBUG.value)
            
            # JSON formatter for file (machine readable)
            json_formatter = JSONFormatter()
            file_handler.setFormatter(json_formatter)
            
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(DebugLevel.TRACE.value)
        else:
            # Minimal logging when debug disabled
            self.logger.setLevel(DebugLevel.WARNING.value)
    
    def trace(self, message: str, **kwargs):
        """Extremely detailed execution flow logging"""
        if self.debug_enabled:
            self._log(DebugLevel.TRACE, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Detailed debugging information"""
        if self.debug_enabled:
            self._log(DebugLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """General information logging"""
        self._log(DebugLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning message logging"""
        self._log(DebugLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Error message logging"""
        self._log(DebugLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Critical system error logging"""
        self._log(DebugLevel.CRITICAL, message, **kwargs)
    
    def _log(self, level: DebugLevel, message: str, **kwargs):
        """Internal logging method with context"""
        extra_data = {
            'component': self.name,
            'debug_context': kwargs,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add stack trace for errors if in debug mode
        if level.value >= DebugLevel.ERROR.value and self.debug_enabled:
            import traceback
            extra_data['stack_trace'] = traceback.format_stack()
        
        self.logger.log(level.value, message, extra=extra_data)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'TRACE': '\033[90m',     # Dark gray
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[91m',  # Bright red
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

class JSONFormatter(logging.Formatter):
    """JSON formatter for machine-readable logs"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra data if available
        if hasattr(record, 'debug_context'):
            log_data['context'] = record.debug_context
        
        if hasattr(record, 'stack_trace'):
            log_data['stack_trace'] = record.stack_trace
        
        return json.dumps(log_data)
```

**Required Logging Categories**:
- [ ] **Component Lifecycle**: Initialization, configuration, shutdown
- [ ] **Request Processing**: Request receipt, routing, processing, response
- [ ] **Error Handling**: Error occurrence, recovery attempts, resolution
- [ ] **Performance**: Timing information, resource usage
- [ ] **State Changes**: Component state transitions, configuration updates

### **2. Debug Utilities**
**Purpose**: Interactive tools for debugging and system inspection

**Requirements**:
- **System Inspection**: Ability to inspect component state
- **Interactive Debugging**: REPL or debug console
- **State Manipulation**: Ability to modify system state for testing
- **Documentation**: Self-documenting debug features

**Implementation Pattern**:
```python
# langswarm/v2/core/observability/debug_utils.py
from typing import Dict, Any, List, Optional
import pprint
import inspect
import sys

class DebugInspector:
    """Interactive debugging and inspection utilities"""
    
    def __init__(self, system_components: Dict[str, Any]):
        self.components = system_components
        self.history = []
    
    def inspect_component(self, component_name: str) -> Dict[str, Any]:
        """Inspect a component's current state"""
        if component_name not in self.components:
            return {"error": f"Component {component_name} not found"}
        
        component = self.components[component_name]
        inspection = {
            "name": component_name,
            "type": type(component).__name__,
            "module": component.__class__.__module__,
            "attributes": {},
            "methods": [],
            "state": {}
        }
        
        # Get component attributes
        for attr_name in dir(component):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(component, attr_name)
                    if callable(attr_value):
                        inspection["methods"].append({
                            "name": attr_name,
                            "signature": str(inspect.signature(attr_value)),
                            "doc": attr_value.__doc__
                        })
                    else:
                        inspection["attributes"][attr_name] = str(attr_value)
                except Exception as e:
                    inspection["attributes"][attr_name] = f"<Error: {e}>"
        
        # Get component state if available
        if hasattr(component, 'get_debug_state'):
            try:
                inspection["state"] = component.get_debug_state()
            except Exception as e:
                inspection["state"] = f"<Error getting state: {e}>"
        
        self.history.append(f"inspect_component({component_name})")
        return inspection
    
    def list_components(self) -> List[str]:
        """List all available components"""
        return list(self.components.keys())
    
    def call_method(self, component_name: str, method_name: str, *args, **kwargs) -> Any:
        """Call a method on a component (for testing)"""
        if component_name not in self.components:
            return {"error": f"Component {component_name} not found"}
        
        component = self.components[component_name]
        if not hasattr(component, method_name):
            return {"error": f"Method {method_name} not found on {component_name}"}
        
        method = getattr(component, method_name)
        if not callable(method):
            return {"error": f"{method_name} is not callable"}
        
        try:
            result = method(*args, **kwargs)
            self.history.append(f"call_method({component_name}, {method_name}, {args}, {kwargs})")
            return {"result": result, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get overall system state"""
        state = {
            "components": {},
            "memory_usage": self._get_memory_usage(),
            "thread_count": len(threading.enumerate()),
            "active_connections": self._get_active_connections()
        }
        
        for name, component in self.components.items():
            if hasattr(component, 'get_debug_state'):
                try:
                    state["components"][name] = component.get_debug_state()
                except Exception as e:
                    state["components"][name] = f"<Error: {e}>"
            else:
                state["components"][name] = f"<No debug state available>"
        
        return state
    
    def dump_state_to_file(self, filename: str = "debug_state.json"):
        """Dump current system state to file"""
        import json
        state = self.get_system_state()
        try:
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            return f"State dumped to {filename}"
        except Exception as e:
            return f"Error dumping state: {e}"
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            return {
                "rss": process.memory_info().rss,
                "vms": process.memory_info().vms,
                "percent": process.memory_percent()
            }
        except ImportError:
            return {"error": "psutil not available"}
    
    def _get_active_connections(self) -> int:
        """Get count of active network connections"""
        try:
            import psutil
            return len(psutil.net_connections())
        except ImportError:
            return -1

class DebugConsole:
    """Interactive debug console"""
    
    def __init__(self, inspector: DebugInspector):
        self.inspector = inspector
        self.commands = {
            'help': self.show_help,
            'list': self.inspector.list_components,
            'inspect': self.inspector.inspect_component,
            'state': self.inspector.get_system_state,
            'dump': self.inspector.dump_state_to_file,
            'call': self.inspector.call_method,
            'history': lambda: self.inspector.history,
            'exit': lambda: sys.exit(0)
        }
    
    def start(self):
        """Start interactive debug console"""
        print("🐛 LangSwarm Debug Console")
        print("Type 'help' for available commands, 'exit' to quit")
        
        while True:
            try:
                command = input("debug> ").strip().split()
                if not command:
                    continue
                
                cmd_name = command[0]
                cmd_args = command[1:]
                
                if cmd_name in self.commands:
                    result = self.commands[cmd_name](*cmd_args)
                    if result is not None:
                        pprint.pprint(result)
                else:
                    print(f"Unknown command: {cmd_name}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nExiting debug console...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def show_help(self):
        """Show available commands"""
        help_text = """
Available commands:
  help                          - Show this help
  list                          - List all components
  inspect <component>           - Inspect component state
  state                         - Show system state
  dump [filename]               - Dump state to file
  call <component> <method>     - Call component method
  history                       - Show command history
  exit                          - Exit debug console
        """
        print(help_text)
```

**Required Debug Utilities**:
- [ ] **Component Inspector**: Inspect any component's current state
- [ ] **Method Caller**: Call component methods for testing
- [ ] **State Dumper**: Export system state to files
- [ ] **Performance Monitor**: Real-time performance metrics
- [ ] **Interactive Console**: Command-line interface for debugging

### **3. Development Mode Features**
**Purpose**: Features specifically for development and testing

**Requirements**:
- **Hot Reloading**: Reload components without restart
- **Mock Integration**: Easy mocking of external dependencies
- **Test Data Generation**: Generate test data for development
- **Feature Flags**: Enable/disable features for testing

**Implementation Pattern**:
```python
# langswarm/v2/core/observability/development_mode.py
import importlib
import os
import threading
import time
from typing import Dict, Any, Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class DevelopmentMode:
    """Development mode features and utilities"""
    
    def __init__(self, debug_enabled: bool = False):
        self.debug_enabled = debug_enabled
        self.feature_flags = {}
        self.mock_registry = {}
        self.hot_reload_enabled = False
        self.file_watcher = None
    
    def enable_feature_flag(self, flag_name: str, value: Any = True):
        """Enable a feature flag for testing"""
        self.feature_flags[flag_name] = value
        if self.debug_enabled:
            print(f"🚩 Feature flag enabled: {flag_name} = {value}")
    
    def disable_feature_flag(self, flag_name: str):
        """Disable a feature flag"""
        if flag_name in self.feature_flags:
            del self.feature_flags[flag_name]
            if self.debug_enabled:
                print(f"🚩 Feature flag disabled: {flag_name}")
    
    def is_flag_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self.feature_flags.get(flag_name, False)
    
    def get_flag_value(self, flag_name: str, default: Any = None) -> Any:
        """Get feature flag value"""
        return self.feature_flags.get(flag_name, default)
    
    def register_mock(self, service_name: str, mock_implementation: Any):
        """Register a mock implementation for a service"""
        self.mock_registry[service_name] = mock_implementation
        if self.debug_enabled:
            print(f"🔧 Mock registered: {service_name}")
    
    def get_mock(self, service_name: str) -> Optional[Any]:
        """Get mock implementation for a service"""
        return self.mock_registry.get(service_name)
    
    def enable_hot_reload(self, watch_paths: List[str] = None):
        """Enable hot reloading of Python modules"""
        if not self.debug_enabled:
            return
        
        self.hot_reload_enabled = True
        watch_paths = watch_paths or ['langswarm/v2']
        
        event_handler = HotReloadHandler(self)
        self.file_watcher = Observer()
        
        for path in watch_paths:
            if os.path.exists(path):
                self.file_watcher.schedule(event_handler, path, recursive=True)
                print(f"🔄 Hot reload enabled for: {path}")
        
        self.file_watcher.start()
    
    def disable_hot_reload(self):
        """Disable hot reloading"""
        if self.file_watcher:
            self.file_watcher.stop()
            self.file_watcher.join()
            self.hot_reload_enabled = False
            print("🔄 Hot reload disabled")
    
    def generate_test_data(self, data_type: str, count: int = 1) -> List[Dict[str, Any]]:
        """Generate test data for development"""
        generators = {
            'user_request': self._generate_user_request,
            'agent_config': self._generate_agent_config,
            'tool_config': self._generate_tool_config,
            'error_scenario': self._generate_error_scenario
        }
        
        if data_type not in generators:
            raise ValueError(f"Unknown data type: {data_type}")
        
        return [generators[data_type]() for _ in range(count)]
    
    def _generate_user_request(self) -> Dict[str, Any]:
        """Generate sample user request"""
        import random
        requests = [
            "What is the weather like today?",
            "Can you help me write a Python function?",
            "Search for information about machine learning",
            "Create a file with the current timestamp"
        ]
        return {
            "text": random.choice(requests),
            "user_id": f"test_user_{random.randint(1000, 9999)}",
            "session_id": f"session_{random.randint(1000, 9999)}",
            "timestamp": time.time()
        }
    
    def _generate_agent_config(self) -> Dict[str, Any]:
        """Generate sample agent configuration"""
        import random
        return {
            "name": f"test_agent_{random.randint(100, 999)}",
            "model": random.choice(["gpt-4o", "gpt-4", "claude-3"]),
            "tools": random.sample(["filesystem", "web_search", "calculator"], 2),
            "memory": random.choice([True, False, "production"])
        }
    
    def _generate_tool_config(self) -> Dict[str, Any]:
        """Generate sample tool configuration"""
        import random
        return {
            "name": f"test_tool_{random.randint(100, 999)}",
            "type": random.choice(["mcp", "function", "workflow"]),
            "enabled": True,
            "config": {"timeout": random.randint(5, 30)}
        }
    
    def _generate_error_scenario(self) -> Dict[str, Any]:
        """Generate error scenario for testing"""
        import random
        scenarios = [
            {"type": "ConfigurationError", "message": "Invalid configuration format"},
            {"type": "ToolError", "message": "Tool execution failed"},
            {"type": "AgentError", "message": "Agent initialization failed"},
            {"type": "NetworkError", "message": "Connection timeout"}
        ]
        return random.choice(scenarios)

class HotReloadHandler(FileSystemEventHandler):
    """File system event handler for hot reloading"""
    
    def __init__(self, dev_mode: DevelopmentMode):
        self.dev_mode = dev_mode
        self.reload_delay = 1.0  # Delay to avoid multiple reloads
        self.last_reload = {}
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory or not event.src_path.endswith('.py'):
            return
        
        # Avoid rapid successive reloads
        now = time.time()
        if event.src_path in self.last_reload:
            if now - self.last_reload[event.src_path] < self.reload_delay:
                return
        
        self.last_reload[event.src_path] = now
        
        # Extract module name from file path
        module_name = self._path_to_module(event.src_path)
        if module_name:
            self._reload_module(module_name)
    
    def _path_to_module(self, file_path: str) -> Optional[str]:
        """Convert file path to module name"""
        try:
            # Convert path to module notation
            path = file_path.replace(os.sep, '.').replace('.py', '')
            if 'langswarm.v2' in path:
                module_start = path.find('langswarm.v2')
                return path[module_start:]
            return None
        except Exception:
            return None
    
    def _reload_module(self, module_name: str):
        """Reload a Python module"""
        try:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                print(f"🔄 Reloaded module: {module_name}")
            else:
                print(f"⚠️ Module not loaded: {module_name}")
        except Exception as e:
            print(f"❌ Failed to reload {module_name}: {e}")
```

**Required Development Features**:
- [ ] **Feature Flags**: Enable/disable features for testing
- [ ] **Mock Registry**: Easy mocking of external dependencies
- [ ] **Hot Reloading**: Reload code changes without restart
- [ ] **Test Data Generation**: Generate realistic test data
- [ ] **Environment Simulation**: Simulate different environments

---

## 🔧 **Debug Mode Integration**

### **Component Debug Interface**
```python
# Base interface that all V2 components should implement
class DebuggableComponent:
    """Base interface for debuggable components"""
    
    def get_debug_state(self) -> Dict[str, Any]:
        """Get current component state for debugging"""
        return {
            "component_type": self.__class__.__name__,
            "initialized": getattr(self, '_initialized', False),
            "configuration": getattr(self, '_config', {}),
            "runtime_state": self._get_runtime_state()
        }
    
    def _get_runtime_state(self) -> Dict[str, Any]:
        """Get component-specific runtime state"""
        # Override in subclasses
        return {}
    
    def enable_debug_mode(self, debug_config: Dict[str, Any] = None):
        """Enable debug mode for this component"""
        self._debug_enabled = True
        self._debug_config = debug_config or {}
        self._setup_debug_logging()
    
    def disable_debug_mode(self):
        """Disable debug mode for this component"""
        self._debug_enabled = False
    
    def _setup_debug_logging(self):
        """Set up debug logging for this component"""
        # Override in subclasses
        pass
```

### **Global Debug Configuration**
```python
# langswarm/v2/core/observability/debug_config.py
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class DebugConfig:
    """Global debug configuration"""
    
    # General debug settings
    enabled: bool = False
    level: str = "DEBUG"  # TRACE, DEBUG, INFO, WARNING, ERROR
    
    # Logging configuration
    console_output: bool = True
    file_output: bool = True
    json_format: bool = False
    log_file: str = "debug.log"
    
    # Component-specific settings
    component_configs: Dict[str, Dict[str, Any]] = None
    
    # Development mode settings
    hot_reload: bool = False
    feature_flags: Dict[str, Any] = None
    mock_services: List[str] = None
    
    # Performance settings
    max_log_size: int = 100 * 1024 * 1024  # 100MB
    max_memory_usage: int = 500 * 1024 * 1024  # 500MB
    
    def __post_init__(self):
        if self.component_configs is None:
            self.component_configs = {}
        if self.feature_flags is None:
            self.feature_flags = {}
        if self.mock_services is None:
            self.mock_services = []
```

---

## 📋 **Debug Mode Checklist for Each Task**

### **Before Implementation**
- [ ] Debug mode requirements defined for component
- [ ] Debug logging strategy planned
- [ ] Debug utilities identified and designed
- [ ] Performance impact assessed and acceptable

### **During Implementation**
- [ ] Verbose logging added to all major operations
- [ ] Debug utilities implemented for component inspection
- [ ] Development mode features added where appropriate
- [ ] Debug mode tested and validated

### **After Implementation**
- [ ] Debug output verified useful for troubleshooting
- [ ] Performance impact measured and within limits
- [ ] Debug documentation created for component
- [ ] Debug mode integration tested with observability system

### **Before Task Completion**
- [ ] Debug mode functionality complete and tested
- [ ] Debug documentation updated
- [ ] Debug utilities accessible to developers
- [ ] Debug lessons documented for future tasks

---

**Debug mode is essential for developer productivity and system maintainability!**
