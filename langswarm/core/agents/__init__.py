"""
LangSwarm V2 Agent System

Modern, simplified agent architecture that replaces the complex mixin-based AgentWrapper
with clean, provider-specific implementations and composition-based design.

Key Features:
- Provider-specific agents (OpenAI, Anthropic, Gemini, etc.)
- Composition over inheritance
- Native implementations (no LangChain/LlamaIndex dependencies)
- V2 error system, middleware, and tool integration
- Smart defaults with builder pattern for advanced configurations
- Full backward compatibility with V1 agent system

Usage:
    from langswarm.core.agents import AgentBuilder, OpenAIAgent, AnthropicAgent
    
    # Simple agent creation
    agent = AgentBuilder().openai().model("gpt-4o").build()
    
    # Advanced configuration
    agent = (AgentBuilder()
             .openai()
             .model("gpt-4o")
             .system_prompt("You are a helpful assistant")
             .tools(["calculator", "web_search"])
             .memory_enabled(True)
             .build())
    
    # Direct provider instantiation
    agent = OpenAIAgent(
        model="gpt-4o",
        api_key="your-key-here"
    )
"""

from .interfaces import (
    IAgent,
    IAgentProvider,
    IAgentConfiguration,
    IAgentSession,
    IAgentResponse,
    AgentCapability,
    AgentStatus,
    ProviderType
)

from .base import (
    BaseAgent,
    AgentConfiguration,
    AgentSession,
    AgentResponse,
    AgentMetadata
)

from .builder import (
    AgentBuilder,
    create_agent,
    create_openai_agent,
    create_anthropic_agent,
    create_gemini_agent,
    create_cohere_agent,
    create_mistral_agent,
    create_huggingface_agent,
    create_local_agent
)

# Provider implementations
try:
    from .providers import *
except ImportError:
    pass

from .registry import (
    AgentRegistry,
    register_agent,
    get_agent,
    list_agents,
    list_agent_info,
    agent_health_check,
    get_agent_statistics,
    save_registry,
    load_registry,
    export_registry,
    import_registry,
    get_agent_children,
    get_agent_parent,
    get_agent_hierarchy,
    get_root_agents
)

# Multimodal capabilities (Task C1)
try:
    from .multimodal import (
        # Core multimodal interfaces
        IMultimodalProcessor,
        IMultimodalAgent,
        
        # Data structures
        MultimodalContent,
        MultimodalRequest,
        MultimodalResponse,
        MediaMetadata,
        
        # Enums
        MediaType,
        ModalityType,
        ProcessingMode,
        
        # Helper functions
        create_image_content,
        create_video_content,
        create_audio_content,
        create_document_content,
        validate_media_type,
        get_content_info
    )
    
    from .multimodal_processor import (
        BaseMultimodalProcessor
    )
    
    from .multimodal_agent import (
        MultimodalAgent,
        MultimodalAgentFactory
    )
    
    # Provider-specific multimodal processors
    from .providers.openai_multimodal import (
        OpenAIMultimodalProcessor,
        OpenAIMultimodalProvider
    )
    
    from .providers.anthropic_multimodal import (
        AnthropicMultimodalProcessor,
        AnthropicMultimodalProvider
    )
    
    from .providers.gemini_multimodal import (
        GeminiMultimodalProcessor,
        GeminiMultimodalProvider
    )
    
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False

# Real-time capabilities (Task C2)
try:
    from .realtime import (
        # Core real-time interfaces
        IRealtimeAgent,
        IRealtimeSession,
        IWebSocketHandler,
        ISSEHandler,
        IVoiceConversation,
        ILiveCollaboration,
        
        # Real-time manager
        RealtimeAgentManager,
        create_realtime_manager,
        
        # WebSocket support
        WebSocketHandler,
        create_websocket_handler,
        
        # Server-sent events
        SSEHandler,
        create_sse_handler,
        
        # Voice conversation
        VoiceConversationManager,
        create_voice_conversation,
        
        # Live collaboration
        LiveCollaborationSession,
        create_collaboration_session,
        
        # Streaming response
        StreamingResponseManager,
        create_streaming_manager,
        
        # Data structures
        RealtimeMessage,
        RealtimeEvent,
        StreamingChunk,
        VoiceSegment,
        CollaborationState,
        RealtimeConfiguration,
        
        # Enums
        RealtimeMessageType,
        EventType,
        StreamingType,
        VoiceState,
        CollaborationRole,
        ConnectionStatus
    )
    REALTIME_AVAILABLE = True
except ImportError:
    REALTIME_AVAILABLE = False

__all__ = [
    # Interfaces
    'IAgent',
    'IAgentProvider', 
    'IAgentConfiguration',
    'IAgentSession',
    'IAgentResponse',
    'AgentCapability',
    'AgentStatus',
    'ProviderType',
    
    # Base Classes
    'BaseAgent',
    'AgentConfiguration',
    'AgentSession', 
    'AgentResponse',
    'AgentMetadata',
    
    # Builder Pattern
    'AgentBuilder',
    'create_agent',
    'create_openai_agent',
    'create_anthropic_agent',
    'create_gemini_agent',
    'create_cohere_agent',
    'create_mistral_agent',
    'create_huggingface_agent',
    'create_local_agent',
    
    # Registry
    'AgentRegistry',
    'register_agent',
    'get_agent',
    'list_agents',
    'list_agent_info',
    'agent_health_check',
    'get_agent_statistics',
    'save_registry',
    'load_registry',
    'export_registry',
    'import_registry',
    
    # Hierarchy
    'get_agent_children',
    'get_agent_parent',
    'get_agent_hierarchy',
    'get_root_agents'
]

# Add multimodal capabilities to __all__ if available
if MULTIMODAL_AVAILABLE:
    __all__.extend([
        # Multimodal interfaces
        'IMultimodalProcessor',
        'IMultimodalAgent',
        
        # Data structures
        'MultimodalContent',
        'MultimodalRequest',
        'MultimodalResponse',
        'MediaMetadata',
        
        # Enums
        'MediaType',
        'ModalityType',
        'ProcessingMode',
        
        # Helper functions
        'create_image_content',
        'create_video_content',
        'create_audio_content',
        'create_document_content',
        'validate_media_type',
        'get_content_info',
        
        # Processors and agents
        'BaseMultimodalProcessor',
        'MultimodalAgent',
        'MultimodalAgentFactory',
        
        # Provider-specific
        'OpenAIMultimodalProcessor',
        'OpenAIMultimodalProvider',
        'AnthropicMultimodalProcessor',
        'AnthropicMultimodalProvider',
        'GeminiMultimodalProcessor',
        'GeminiMultimodalProvider'
    ])

# Add real-time capabilities to __all__ if available
if REALTIME_AVAILABLE:
    __all__.extend([
        # Real-time interfaces
        'IRealtimeAgent',
        'IRealtimeSession',
        'IWebSocketHandler',
        'ISSEHandler',
        'IVoiceConversation',
        'ILiveCollaboration',
        
        # Real-time manager
        'RealtimeAgentManager',
        'create_realtime_manager',
        
        # WebSocket support
        'WebSocketHandler',
        'create_websocket_handler',
        
        # Server-sent events
        'SSEHandler',
        'create_sse_handler',
        
        # Voice conversation
        'VoiceConversationManager',
        'create_voice_conversation',
        
        # Live collaboration
        'LiveCollaborationSession',
        'create_collaboration_session',
        
        # Streaming response
        'StreamingResponseManager',
        'create_streaming_manager',
        
        # Data structures
        'RealtimeMessage',
        'RealtimeEvent',
        'StreamingChunk',
        'VoiceSegment',
        'CollaborationState',
        'RealtimeConfiguration',
        
        # Enums
        'RealtimeMessageType',
        'EventType',
        'StreamingType',
        'VoiceState',
        'CollaborationRole',
        'ConnectionStatus'
    ])
