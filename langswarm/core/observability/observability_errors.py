"""
Observability System Error Handling for LangSwarm

Provides clear, actionable error messages for monitoring, tracing,
and logging issues in the observability system.
"""

from typing import List, Optional, Dict, Any
from langswarm.core.errors import LangSwarmError, ErrorContext


class ObservabilityError(LangSwarmError):
    """Base class for all observability-related errors."""
    pass


class TracingError(ObservabilityError):
    """Raised when tracing operations fail."""
    
    def __init__(
        self,
        operation: str,
        tracer_type: str,
        error: Optional[Exception] = None,
        span_name: Optional[str] = None
    ):
        self.operation = operation
        self.tracer_type = tracer_type
        self.original_error = error
        self.span_name = span_name
        
        message = f"Tracing {operation} failed with {tracer_type}"
        if span_name:
            message += f" (span: {span_name})"
        
        context = ErrorContext(
            component="TracingSystem",
            operation=operation,
            metadata={
                "tracer_type": tracer_type,
                "span_name": span_name,
                "error_type": type(error).__name__ if error else None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for tracing errors."""
        suggestions = [f"Fix {self.tracer_type} tracing issue:"]
        
        tracer_suggestions = {
            "opentelemetry": [
                "• Install OpenTelemetry: pip install opentelemetry-api opentelemetry-sdk",
                "• Check exporter configuration",
                "• Verify trace endpoint connectivity",
                "• Ensure proper SDK initialization"
            ],
            "jaeger": [
                "• Verify Jaeger agent/collector is running",
                "• Check Jaeger endpoint configuration",
                "• Ensure network connectivity to Jaeger",
                "• Monitor Jaeger server logs"
            ],
            "zipkin": [
                "• Verify Zipkin server is accessible",
                "• Check Zipkin endpoint URL",
                "• Ensure proper trace format",
                "• Monitor Zipkin server status"
            ],
            "console": [
                "• Check console output permissions",
                "• Verify logging configuration",
                "• Ensure stdout/stderr are accessible",
                "• Check for output redirection issues"
            ]
        }
        
        if self.tracer_type in tracer_suggestions:
            suggestions.extend([""])
            suggestions.extend(tracer_suggestions[self.tracer_type])
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "network" in error_str or "connection" in error_str:
                suggestions.extend([
                    "",
                    "Network/connection issue detected:",
                    "• Check if tracing endpoint is reachable",
                    "• Verify firewall and proxy settings",
                    "• Test connectivity with curl or telnet",
                    "• Consider using local tracing for development"
                ])
            elif "auth" in error_str or "permission" in error_str:
                suggestions.extend([
                    "",
                    "Authentication/permission issue detected:",
                    "• Check tracing service credentials",
                    "• Verify API keys or tokens",
                    "• Ensure proper RBAC permissions",
                    "• Check service account configuration"
                ])
            elif "format" in error_str or "serialization" in error_str:
                suggestions.extend([
                    "",
                    "Data format issue detected:",
                    "• Check span data format compatibility",
                    "• Verify attribute value types",
                    "• Ensure trace context is valid",
                    "• Remove problematic span attributes"
                ])
        
        suggestions.extend([
            "",
            "For development, use simple console tracing:",
            "```yaml",
            "observability:",
            "  tracing:",
            "    enabled: true",
            "    exporter: console  # No external dependencies",
            "```"
        ])
        
        return "\n".join(suggestions)


class MetricsError(ObservabilityError):
    """Raised when metrics collection fails."""
    
    def __init__(
        self,
        operation: str,
        metrics_backend: str,
        metric_name: Optional[str] = None,
        error: Optional[Exception] = None
    ):
        self.operation = operation
        self.metrics_backend = metrics_backend
        self.metric_name = metric_name
        self.original_error = error
        
        message = f"Metrics {operation} failed with {metrics_backend}"
        if metric_name:
            message += f" (metric: {metric_name})"
        
        context = ErrorContext(
            component="MetricsSystem",
            operation=operation,
            metadata={
                "backend": metrics_backend,
                "metric_name": metric_name,
                "error_type": type(error).__name__ if error else None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for metrics errors."""
        suggestions = [f"Fix {self.metrics_backend} metrics issue:"]
        
        backend_suggestions = {
            "prometheus": [
                "• Verify Prometheus server is running",
                "• Check metrics endpoint configuration",
                "• Ensure proper metric name format",
                "• Monitor Prometheus scrape targets"
            ],
            "datadog": [
                "• Check DataDog API key configuration",
                "• Verify DataDog agent is running",
                "• Ensure proper metric tags format",
                "• Monitor DataDog agent logs"
            ],
            "cloudwatch": [
                "• Verify AWS credentials and permissions",
                "• Check CloudWatch service availability",
                "• Ensure proper namespace configuration",
                "• Monitor AWS API quotas"
            ],
            "statsd": [
                "• Verify StatsD server is accessible",
                "• Check UDP/TCP connectivity",
                "• Ensure proper metric format",
                "• Monitor StatsD server logs"
            ]
        }
        
        if self.metrics_backend in backend_suggestions:
            suggestions.extend([""])
            suggestions.extend(backend_suggestions[self.metrics_backend])
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "rate" in error_str or "quota" in error_str or "limit" in error_str:
                suggestions.extend([
                    "",
                    "Rate limit/quota issue detected:",
                    "• Reduce metrics collection frequency",
                    "• Batch metrics to reduce API calls",
                    "• Check service quotas and limits",
                    "• Consider metrics sampling"
                ])
            elif "format" in error_str or "name" in error_str:
                suggestions.extend([
                    "",
                    "Metric format issue detected:",
                    "• Check metric name format (alphanumeric + underscores)",
                    "• Verify metric value is numeric",
                    "• Ensure tags/labels follow backend format",
                    "• Remove special characters from names"
                ])
        
        if self.metric_name:
            suggestions.extend([
                "",
                f"Problematic metric: {self.metric_name}",
                "• Check metric name follows naming conventions",
                "• Verify metric value type and range",
                "• Ensure metric is properly defined"
            ])
        
        suggestions.extend([
            "",
            "For development, use simple logging metrics:",
            "```yaml",
            "observability:",
            "  metrics:",
            "    enabled: true",
            "    exporter: console  # Log metrics to console",
            "```"
        ])
        
        return "\n".join(suggestions)


class LoggingError(ObservabilityError):
    """Raised when logging operations fail."""
    
    def __init__(
        self,
        operation: str,
        logger_config: str,
        error: Optional[Exception] = None,
        log_level: Optional[str] = None
    ):
        self.operation = operation
        self.logger_config = logger_config
        self.original_error = error
        self.log_level = log_level
        
        message = f"Logging {operation} failed with {logger_config}"
        if log_level:
            message += f" (level: {log_level})"
        
        context = ErrorContext(
            component="LoggingSystem",
            operation=operation,
            metadata={
                "logger_config": logger_config,
                "log_level": log_level,
                "error_type": type(error).__name__ if error else None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for logging errors."""
        suggestions = [f"Fix {self.logger_config} logging issue:"]
        
        config_suggestions = {
            "file": [
                "• Check file path permissions",
                "• Verify directory exists",
                "• Ensure sufficient disk space",
                "• Check file rotation settings"
            ],
            "syslog": [
                "• Verify syslog daemon is running",
                "• Check syslog facility configuration",
                "• Ensure proper log format",
                "• Monitor syslog server connectivity"
            ],
            "remote": [
                "• Check remote logging endpoint",
                "• Verify network connectivity",
                "• Ensure proper authentication",
                "• Monitor remote server status"
            ],
            "structured": [
                "• Verify JSON format compliance",
                "• Check field name conventions",
                "• Ensure proper data types",
                "• Remove circular references"
            ]
        }
        
        if self.logger_config in config_suggestions:
            suggestions.extend([""])
            suggestions.extend(config_suggestions[self.logger_config])
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "permission" in error_str or "access" in error_str:
                suggestions.extend([
                    "",
                    "Permission issue detected:",
                    "• Check file/directory write permissions",
                    "• Verify user has required access",
                    "• Consider running with appropriate privileges",
                    "• Check SELinux/AppArmor policies"
                ])
            elif "disk" in error_str or "space" in error_str:
                suggestions.extend([
                    "",
                    "Disk space issue detected:",
                    "• Free up disk space",
                    "• Implement log rotation",
                    "• Consider log compression",
                    "• Move logs to larger volume"
                ])
            elif "format" in error_str:
                suggestions.extend([
                    "",
                    "Log format issue detected:",
                    "• Check log format configuration",
                    "• Verify timestamp format",
                    "• Ensure proper field escaping",
                    "• Test with simpler format first"
                ])
        
        suggestions.extend([
            "",
            "For development, use simple console logging:",
            "```python",
            "import logging",
            "logging.basicConfig(",
            "    level=logging.INFO,",
            "    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'",
            ")",
            "```"
        ])
        
        return "\n".join(suggestions)


class MonitoringError(ObservabilityError):
    """Raised when monitoring operations fail."""
    
    def __init__(
        self,
        operation: str,
        monitor_type: str,
        component: Optional[str] = None,
        error: Optional[Exception] = None
    ):
        self.operation = operation
        self.monitor_type = monitor_type
        self.component = component
        self.original_error = error
        
        message = f"Monitoring {operation} failed for {monitor_type}"
        if component:
            message += f" (component: {component})"
        
        context = ErrorContext(
            component="MonitoringSystem",
            operation=operation,
            metadata={
                "monitor_type": monitor_type,
                "component": component,
                "error_type": type(error).__name__ if error else None
            }
        )
        
        suggestion = self._build_suggestion()
        
        super().__init__(message, context=context, suggestion=suggestion)
    
    def _build_suggestion(self) -> str:
        """Build helpful suggestion for monitoring errors."""
        suggestions = [f"Fix {self.monitor_type} monitoring issue:"]
        
        monitor_suggestions = {
            "health_check": [
                "• Verify health check endpoint accessibility",
                "• Check component dependencies",
                "• Ensure proper timeout settings",
                "• Monitor underlying service status"
            ],
            "performance": [
                "• Check performance metric collection",
                "• Verify sufficient monitoring resources",
                "• Ensure proper sampling rates",
                "• Monitor system resource usage"
            ],
            "error_tracking": [
                "• Verify error capture configuration",
                "• Check error aggregation settings",
                "• Ensure proper error classification",
                "• Monitor error service connectivity"
            ],
            "alerting": [
                "• Check alert rule configuration",
                "• Verify notification channels",
                "• Ensure proper threshold settings",
                "• Test alert delivery mechanisms"
            ]
        }
        
        if self.monitor_type in monitor_suggestions:
            suggestions.extend([""])
            suggestions.extend(monitor_suggestions[self.monitor_type])
        
        if self.component:
            suggestions.extend([
                "",
                f"Component-specific troubleshooting for {self.component}:",
                "• Check component health and status",
                "• Verify component configuration",
                "• Monitor component dependencies",
                "• Review component-specific logs"
            ])
        
        if self.original_error:
            error_str = str(self.original_error).lower()
            
            if "timeout" in error_str:
                suggestions.extend([
                    "",
                    "Timeout issue detected:",
                    "• Increase monitoring timeout values",
                    "• Check component response times",
                    "• Optimize monitoring queries",
                    "• Consider async monitoring"
                ])
            elif "threshold" in error_str:
                suggestions.extend([
                    "",
                    "Threshold issue detected:",
                    "• Review alert threshold settings",
                    "• Check metric baseline values",
                    "• Adjust sensitivity parameters",
                    "• Consider dynamic thresholds"
                ])
        
        suggestions.extend([
            "",
            "For development, use basic monitoring:",
            "```yaml",
            "observability:",
            "  monitoring:",
            "    enabled: true",
            "    health_check:",
            "      interval: 30s",
            "      timeout: 5s",
            "```"
        ])
        
        return "\n".join(suggestions)


# Convenience functions for creating common observability errors
def tracing_failed(
    operation: str, 
    tracer_type: str, 
    error: Optional[Exception] = None
) -> TracingError:
    """Create a TracingError with context."""
    return TracingError(operation, tracer_type, error)


def metrics_failed(
    operation: str, 
    backend: str, 
    error: Optional[Exception] = None
) -> MetricsError:
    """Create a MetricsError with context."""
    return MetricsError(operation, backend, error=error)


def logging_failed(
    operation: str, 
    config: str, 
    error: Optional[Exception] = None
) -> LoggingError:
    """Create a LoggingError with context."""
    return LoggingError(operation, config, error)


def monitoring_failed(
    operation: str, 
    monitor_type: str, 
    error: Optional[Exception] = None
) -> MonitoringError:
    """Create a MonitoringError with context."""
    return MonitoringError(operation, monitor_type, error=error)