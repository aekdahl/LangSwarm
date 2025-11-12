"""
V1 MCP Tools Compatibility Layer

This module provides backward compatibility for V1 imports by re-exporting
tools from their actual location at langswarm.tools.mcp

All MCP tools have been moved to langswarm.tools.mcp in the unified V2 structure.
This compatibility layer ensures V1 code continues to work without modifications.
"""

# Re-export all MCP tools from their actual location
try:
    from langswarm.tools.mcp.filesystem.main import FilesystemMCPTool
except ImportError:
    FilesystemMCPTool = None

try:
    from langswarm.tools.mcp.mcpgithubtool.main import MCPGitHubTool
except ImportError:
    MCPGitHubTool = None

try:
    from langswarm.tools.mcp.dynamic_forms.main import DynamicFormsMCPTool
except ImportError:
    DynamicFormsMCPTool = None

try:
    from langswarm.tools.mcp.remote.main import RemoteMCPTool
except ImportError:
    RemoteMCPTool = None

try:
    from langswarm.tools.mcp.tasklist.main import TasklistMCPTool
except ImportError:
    TasklistMCPTool = None

try:
    from langswarm.tools.mcp.message_queue_publisher.main import MessageQueuePublisherMCPTool
except ImportError:
    MessageQueuePublisherMCPTool = None

try:
    from langswarm.tools.mcp.message_queue_consumer.main import MessageQueueConsumerMCPTool
except ImportError:
    MessageQueueConsumerMCPTool = None

try:
    from langswarm.tools.mcp.gcp_environment.main import GCPEnvironmentMCPTool
except ImportError:
    GCPEnvironmentMCPTool = None

try:
    from langswarm.tools.mcp.codebase_indexer.main import CodebaseIndexerMCPTool
except ImportError:
    CodebaseIndexerMCPTool = None

try:
    from langswarm.tools.mcp.workflow_executor.main import WorkflowExecutorMCPTool
except ImportError:
    WorkflowExecutorMCPTool = None

try:
    from langswarm.tools.mcp.sql_database.main import SQLDatabaseMCPTool
except ImportError:
    SQLDatabaseMCPTool = None

try:
    from langswarm.tools.mcp.bigquery_vector_search.main import BigQueryVectorSearchMCPTool
except ImportError:
    BigQueryVectorSearchMCPTool = None

try:
    from langswarm.tools.mcp.daytona_environment.main import DaytonaEnvironmentMCPTool
except ImportError:
    DaytonaEnvironmentMCPTool = None

try:
    from langswarm.tools.mcp.daytona_self_hosted.main import SelfHostedDaytonaManager
except ImportError:
    SelfHostedDaytonaManager = None

try:
    from langswarm.tools.mcp.realtime_voice.main import RealtimeVoiceMCPTool
except ImportError:
    RealtimeVoiceMCPTool = None

# Also import brokers for message queue tools
try:
    from langswarm.tools.mcp.message_queue_publisher.main import InMemoryBroker, RedisBroker, GCPPubSubBroker
except ImportError:
    InMemoryBroker = None
    RedisBroker = None
    GCPPubSubBroker = None

# Template loader compatibility
try:
    from langswarm.tools.mcp.template_loader import load_tool_template, get_cached_tool_template_safe
except ImportError:
    load_tool_template = None
    get_cached_tool_template_safe = None

__all__ = [
    'FilesystemMCPTool',
    'MCPGitHubTool',
    'DynamicFormsMCPTool',
    'RemoteMCPTool',
    'TasklistMCPTool',
    'MessageQueuePublisherMCPTool',
    'MessageQueueConsumerMCPTool',
    'GCPEnvironmentMCPTool',
    'CodebaseIndexerMCPTool',
    'WorkflowExecutorMCPTool',
    'SQLDatabaseMCPTool',
    'BigQueryVectorSearchMCPTool',
    'DaytonaEnvironmentMCPTool',
    'SelfHostedDaytonaManager',
    'RealtimeVoiceMCPTool',
    'InMemoryBroker',
    'RedisBroker',
    'GCPPubSubBroker',
    'load_tool_template',
    'get_cached_tool_template_safe',
]

