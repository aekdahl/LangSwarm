"""
LangSwarm V2 Structured Logger

Production-ready structured logging implementation with support for
multiple output formats and integration with tracing system.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Optional, Any, TextIO
from pathlib import Path

from .interfaces import ILogger, LogLevel, LogEvent, ObservabilityConfig


class V2Logger(ILogger):
    """
    Structured logger implementation for V2 observability system.
    
    Provides structured logging with JSON output, component tracking,
    and integration with tracing for comprehensive observability.
    """
    
    def __init__(self, config: ObservabilityConfig):
        """
        Initialize V2 logger.
        
        Args:
            config: Observability configuration
        """
        self.config = config
        self._current_trace_id: Optional[str] = None
        self._current_span_id: Optional[str] = None
        
        # Set up Python logging
        self._setup_python_logging()
        
        # Output streams
        self._console_stream = sys.stdout
        self._file_stream: Optional[TextIO] = None
        
        if config.log_output in ["file", "both"] and config.log_file_path:
            self._setup_file_logging()
    
    def _setup_python_logging(self):
        """Configure Python logging integration"""
        # Map our log levels to Python logging levels
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        
        # Configure root logger
        logging.basicConfig(
            level=level_map.get(self.config.log_level, logging.INFO),
            format='%(message)s',  # We'll handle formatting ourselves
            handlers=[]  # We'll handle output ourselves
        )
    
    def _setup_file_logging(self):
        """Set up file logging output"""
        try:
            log_path = Path(self.config.log_file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_stream = open(log_path, 'a', encoding='utf-8')
        except Exception as e:
            # Fall back to console only
            print(f"Failed to setup file logging: {e}", file=sys.stderr)
            self.config.log_output = "console"
    
    def set_trace_context(self, trace_id: Optional[str], span_id: Optional[str]):
        """Set current trace context for log correlation"""
        self._current_trace_id = trace_id
        self._current_span_id = span_id
    
    def debug(self, message: str, component: str = None, **kwargs):
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, component, **kwargs)
    
    def info(self, message: str, component: str = None, **kwargs):
        """Log info message"""
        self.log(LogLevel.INFO, message, component, **kwargs)
    
    def warning(self, message: str, component: str = None, **kwargs):
        """Log warning message"""
        self.log(LogLevel.WARNING, message, component, **kwargs)
    
    def error(self, message: str, component: str = None, **kwargs):
        """Log error message"""
        self.log(LogLevel.ERROR, message, component, **kwargs)
    
    def critical(self, message: str, component: str = None, **kwargs):
        """Log critical message"""
        self.log(LogLevel.CRITICAL, message, component, **kwargs)
    
    def log(self, level: LogLevel, message: str, component: str = None, **kwargs):
        """Log message at specified level"""
        if not self.config.enabled:
            return
        
        # Check if level is enabled
        if not self._is_level_enabled(level):
            return
        
        # Check component filtering
        if not self._is_component_enabled(component):
            return
        
        # Create log event
        log_event = LogEvent(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            component=component or "unknown",
            trace_id=self._current_trace_id,
            span_id=self._current_span_id,
            operation=kwargs.pop('operation', None),
            user_id=kwargs.pop('user_id', None),
            session_id=kwargs.pop('session_id', None),
            metadata=kwargs
        )
        
        # Format and output log
        self._output_log(log_event)
    
    def _is_level_enabled(self, level: LogLevel) -> bool:
        """Check if log level is enabled"""
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        
        return level_order.get(level, 1) >= level_order.get(self.config.log_level, 1)
    
    def _is_component_enabled(self, component: Optional[str]) -> bool:
        """Check if component logging is enabled"""
        if not component:
            return True
        
        # Check disabled components
        if self.config.disabled_components and component in self.config.disabled_components:
            return False
        
        # Check enabled components (if specified, only these are enabled)
        if self.config.enabled_components:
            return component in self.config.enabled_components
        
        return True
    
    def _output_log(self, log_event: LogEvent):
        """Output log event to configured destinations"""
        if self.config.log_format == "structured":
            formatted_log = self._format_structured(log_event)
        else:
            formatted_log = self._format_text(log_event)
        
        # Output to console
        if self.config.log_output in ["console", "both"]:
            print(formatted_log, file=self._console_stream)
            self._console_stream.flush()
        
        # Output to file
        if self.config.log_output in ["file", "both"] and self._file_stream:
            print(formatted_log, file=self._file_stream)
            self._file_stream.flush()
    
    def _format_structured(self, log_event: LogEvent) -> str:
        """Format log event as structured JSON"""
        data = {
            "timestamp": log_event.timestamp.isoformat(),
            "level": log_event.level.value,
            "message": log_event.message,
            "component": log_event.component
        }
        
        # Add optional fields
        if log_event.operation:
            data["operation"] = log_event.operation
        if log_event.trace_id:
            data["trace_id"] = log_event.trace_id
        if log_event.span_id:
            data["span_id"] = log_event.span_id
        if log_event.user_id:
            data["user_id"] = log_event.user_id
        if log_event.session_id:
            data["session_id"] = log_event.session_id
        if log_event.metadata:
            data["metadata"] = log_event.metadata
        
        return json.dumps(data, separators=(',', ':'))
    
    def _format_text(self, log_event: LogEvent) -> str:
        """Format log event as human-readable text"""
        timestamp = log_event.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = log_event.level.value.upper()
        component = log_event.component
        message = log_event.message
        
        # Build base log line
        log_line = f"{timestamp} [{level}] {component}: {message}"
        
        # Add trace context if available
        if log_event.trace_id or log_event.span_id:
            trace_info = []
            if log_event.trace_id:
                trace_info.append(f"trace={log_event.trace_id[:8]}")
            if log_event.span_id:
                trace_info.append(f"span={log_event.span_id[:8]}")
            log_line += f" [{', '.join(trace_info)}]"
        
        # Add user/session context if available
        context_info = []
        if log_event.user_id:
            context_info.append(f"user={log_event.user_id}")
        if log_event.session_id:
            context_info.append(f"session={log_event.session_id[:8]}")
        if context_info:
            log_line += f" ({', '.join(context_info)})"
        
        # Add metadata if available
        if log_event.metadata:
            metadata_str = json.dumps(log_event.metadata, separators=(',', ':'))
            log_line += f" {metadata_str}"
        
        return log_line
    
    def close(self):
        """Close logger and cleanup resources"""
        if self._file_stream:
            self._file_stream.close()
            self._file_stream = None


# Global logger registry
_loggers: Dict[str, V2Logger] = {}
_default_config: Optional[ObservabilityConfig] = None


def configure_logging(config: ObservabilityConfig):
    """Configure global logging settings"""
    global _default_config
    _default_config = config


def create_logger(name: str = "default", config: Optional[ObservabilityConfig] = None) -> V2Logger:
    """Create a named logger instance"""
    if config is None:
        config = _default_config or ObservabilityConfig()
    
    logger = V2Logger(config)
    _loggers[name] = logger
    return logger


def get_logger(name: str = "default") -> Optional[V2Logger]:
    """Get existing logger by name"""
    return _loggers.get(name)


def get_or_create_logger(name: str = "default", 
                        config: Optional[ObservabilityConfig] = None) -> V2Logger:
    """Get existing logger or create new one"""
    logger = get_logger(name)
    if logger is None:
        logger = create_logger(name, config)
    return logger


# Convenience functions for default logger
def debug(message: str, component: str = None, **kwargs):
    """Log debug message to default logger"""
    logger = get_or_create_logger()
    logger.debug(message, component, **kwargs)


def info(message: str, component: str = None, **kwargs):
    """Log info message to default logger"""
    logger = get_or_create_logger()
    logger.info(message, component, **kwargs)


def warning(message: str, component: str = None, **kwargs):
    """Log warning message to default logger"""
    logger = get_or_create_logger()
    logger.warning(message, component, **kwargs)


def error(message: str, component: str = None, **kwargs):
    """Log error message to default logger"""
    logger = get_or_create_logger()
    logger.error(message, component, **kwargs)


def critical(message: str, component: str = None, **kwargs):
    """Log critical message to default logger"""
    logger = get_or_create_logger()
    logger.critical(message, component, **kwargs)
