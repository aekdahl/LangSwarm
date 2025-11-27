"""
LangSwarm V2 Agent Interfaces

Clean, type-safe interfaces for the V2 agent system that replace the complex
mixin-based architecture with simple, testable, composition-based design.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, AsyncIterator, Union, Callable, Tuple
import uuid

# Import multimodal types
try:
    from .multimodal import MultimodalContent, MultimodalRequest, MultimodalResponse, IMultimodalProcessor
except ImportError:
    MultimodalContent = None
    MultimodalRequest = None
    MultimodalResponse = None
    IMultimodalProcessor = None


class ProviderType(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    COHERE = "cohere"
    MISTRAL = "mistral"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"
    LITELLM = "litellm"


class AgentCapability(Enum):
    """Capabilities that agents can support"""
    TEXT_GENERATION = "text_generation"
    FUNCTION_CALLING = "function_calling"
    TOOL_USE = "tool_use"
    STREAMING = "streaming"
    VISION = "vision"
    IMAGE_GENERATION = "image_generation"
    MEMORY = "memory"
    SESSION_MANAGEMENT = "session_management"
    CONVERSATION_HISTORY = "conversation_history"
    # Enhanced memory capabilities
    PERSISTENT_MEMORY = "persistent_memory"
    CONTEXT_COMPRESSION = "context_compression"
    MEMORY_RETRIEVAL = "memory_retrieval"
    PERSONALIZATION = "personalization"
    MEMORY_ANALYTICS = "memory_analytics"
    SYSTEM_PROMPTS = "system_prompts"
    REALTIME_VOICE = "realtime_voice"
    MULTIMODAL = "multimodal"
    CODE_EXECUTION = "code_execution"
    FINE_TUNING = "fine_tuning"
    
    # Enhanced multimodal capabilities
    IMAGE_ANALYSIS = "image_analysis"
    VIDEO_UNDERSTANDING = "video_understanding"
    AUDIO_PROCESSING = "audio_processing"
    DOCUMENT_ANALYSIS = "document_analysis"
    OCR = "ocr"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    CROSS_MODAL_REASONING = "cross_modal_reasoning"
    CONTENT_GENERATION = "content_generation"
    CONTENT_TRANSFORMATION = "content_transformation"


class AgentStatus(Enum):
    """Agent operational status"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    MAINTENANCE = "maintenance"


@dataclass
class AgentMessage:
    """Represents a message in a conversation"""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Tool-related fields
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    
    # Enhanced multimodal support
    attachments: Optional[List[Dict[str, Any]]] = None  # Legacy format
    multimodal_content: Optional[List['MultimodalContent']] = None  # New format
    
    # Multimodal processing results
    multimodal_analysis: Optional[Dict[str, Any]] = None
    extracted_content: Optional[Dict[str, Any]] = None
    
    def add_attachment(self, content: 'MultimodalContent') -> None:
        """Add multimodal content to the message"""
        if self.multimodal_content is None:
            self.multimodal_content = []
        self.multimodal_content.append(content)
    
    def has_multimodal_content(self) -> bool:
        """Check if message has multimodal content"""
        return (self.multimodal_content and len(self.multimodal_content) > 0) or \
               (self.attachments and len(self.attachments) > 0)
    
    def get_text_content(self) -> str:
        """Get the text content including extracted text from multimodal content"""
        text_parts = [self.content] if self.content else []
        
        if self.multimodal_content:
            for content in self.multimodal_content:
                text = content.get_content_text()
                if text:
                    text_parts.append(f"[{content.modality.value.upper()}]: {text}")
        
        return "\n".join(text_parts)


@dataclass
class AgentUsage:
    """Token/resource usage information"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_estimate: Optional[float] = None
    model: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class IAgentResponse(ABC):
    """Interface for agent responses"""
    
    @property
    @abstractmethod
    def content(self) -> str:
        """The response content"""
        pass
    
    @property
    @abstractmethod
    def message(self) -> AgentMessage:
        """The response as an AgentMessage"""
        pass
    
    @property
    @abstractmethod
    def usage(self) -> Optional[AgentUsage]:
        """Usage information for the response"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Additional response metadata"""
        pass
    
    @property
    @abstractmethod
    def success(self) -> bool:
        """Whether the response was successful"""
        pass
    
    @property
    @abstractmethod
    def error(self) -> Optional[Exception]:
        """Error if the response failed"""
        pass


class IAgentSession(ABC):
    """Interface for agent conversation sessions"""
    
    @property
    @abstractmethod
    def session_id(self) -> str:
        """Unique session identifier"""
        pass
    
    @property
    @abstractmethod
    def messages(self) -> List[AgentMessage]:
        """All messages in the session"""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """When the session was created"""
        pass
    
    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """When the session was last updated"""
        pass
    
    @abstractmethod
    async def add_message(self, message: AgentMessage) -> None:
        """Add a message to the session"""
        pass
    
    @abstractmethod
    async def clear_messages(self) -> None:
        """Clear all messages from the session"""
        pass
    
    @abstractmethod
    async def get_context(self, max_tokens: Optional[int] = None) -> List[AgentMessage]:
        """Get conversation context within token limit"""
        pass


class IAgentConfiguration(ABC):
    """Interface for agent configuration"""
    
    @property
    @abstractmethod
    def provider(self) -> ProviderType:
        """The LLM provider"""
        pass
    
    @property
    @abstractmethod
    def model(self) -> str:
        """The model name/identifier"""
        pass
    
    @property
    @abstractmethod
    def api_key(self) -> Optional[str]:
        """API key for the provider"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> Optional[str]:
        """Base URL for API calls"""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> Optional[str]:
        """System prompt for the agent"""
        pass
    
    @property
    @abstractmethod
    def max_tokens(self) -> Optional[int]:
        """Maximum tokens for responses"""
        pass
    
    @property
    @abstractmethod
    def temperature(self) -> Optional[float]:
        """Temperature setting for randomness"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """Supported capabilities"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate the configuration"""
        pass


class IAgentProvider(ABC):
    """Interface for LLM provider implementations"""
    
    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """The provider type"""
        pass
    
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """List of supported models"""
        pass
    
    @property
    @abstractmethod
    def supported_capabilities(self) -> List[AgentCapability]:
        """List of supported capabilities"""
        pass
    
    @abstractmethod
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate provider-specific configuration"""
        pass
    
    @abstractmethod
    async def create_session(self, config: IAgentConfiguration) -> IAgentSession:
        """Create a new conversation session"""
        pass
    
    @abstractmethod
    async def send_message(
        self, 
        message: AgentMessage, 
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Send a message and get response"""
        pass
    
    @abstractmethod
    async def stream_message(
        self,
        message: AgentMessage,
        session: IAgentSession, 
        config: IAgentConfiguration
    ) -> AsyncIterator[IAgentResponse]:
        """Stream a response"""
        pass
    
    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        session: IAgentSession,
        config: IAgentConfiguration
    ) -> IAgentResponse:
        """Execute a tool call"""
        pass
    
    @abstractmethod
    async def get_health(self) -> Dict[str, Any]:
        """Get provider health status"""
        pass


class IAgent(ABC):
    """Main interface for V2 agents"""
    
    @property
    @abstractmethod
    def agent_id(self) -> str:
        """Unique agent identifier"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name"""
        pass
    
    @property
    @abstractmethod
    def configuration(self) -> IAgentConfiguration:
        """Agent configuration"""
        pass
    
    @property
    @abstractmethod
    def provider(self) -> IAgentProvider:
        """LLM provider implementation"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> AgentStatus:
        """Current agent status"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """Supported capabilities"""
        pass
    
    @property
    @abstractmethod
    def current_session(self) -> Optional[IAgentSession]:
        """Current active session"""
        pass
    
    # Core functionality
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the agent"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check agent health status"""
        pass
    
    # Session management
    @abstractmethod
    async def create_session(self, session_id: Optional[str] = None) -> IAgentSession:
        """Create a new conversation session"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[IAgentSession]:
        """Get an existing session"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        pass
    
    @abstractmethod
    async def list_sessions(self) -> List[str]:
        """List all session IDs"""
        pass
    
    # Conversation
    @abstractmethod
    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> IAgentResponse:
        """Send a chat message"""
        pass
    
    @abstractmethod
    async def stream_chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[IAgentResponse]:
        """Stream a chat response"""
        pass
    
    # Tool integration
    @abstractmethod
    async def register_tool(self, tool: Any) -> bool:
        """Register a tool with the agent"""
        pass
    
    @abstractmethod
    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool"""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[str]:
        """List registered tools"""
        pass
    
    # V2 System integration
    @abstractmethod
    async def process_through_middleware(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IAgentResponse:
        """Process message through V2 middleware pipeline"""
        pass
    
    # Multimodal capabilities
    @abstractmethod
    async def chat_multimodal(
        self,
        message: str,
        attachments: Optional[List['MultimodalContent']] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> IAgentResponse:
        """Send a multimodal chat message with attachments"""
        pass
    
    @abstractmethod
    async def process_multimodal(
        self,
        request: 'MultimodalRequest',
        session_id: Optional[str] = None
    ) -> 'MultimodalResponse':
        """Process multimodal content directly"""
        pass
    
    @abstractmethod
    async def describe_image(
        self,
        image: Any,  # ImageType from multimodal
        prompt: str = "Describe this image in detail",
        session_id: Optional[str] = None
    ) -> str:
        """Describe an image"""
        pass
    
    @abstractmethod
    async def analyze_document(
        self,
        document: Any,  # DocumentType from multimodal
        questions: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a document and answer questions"""
        pass
    
    @abstractmethod
    async def transcribe_audio(
        self,
        audio: Any,  # AudioType from multimodal
        language: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Transcribe audio to text"""
        pass
    
    @abstractmethod
    async def understand_video(
        self,
        video: Any,  # VideoType from multimodal
        questions: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze video content and answer questions"""
        pass
    
    @abstractmethod
    async def compare_content(
        self,
        content1: 'MultimodalContent',
        content2: 'MultimodalContent',
        comparison_aspects: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare two pieces of multimodal content"""
        pass
    
    @abstractmethod
    async def search_in_content(
        self,
        content: 'MultimodalContent',
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for specific information within content"""
        pass
    
    @abstractmethod
    async def cross_modal_reasoning(
        self,
        contents: List['MultimodalContent'],
        question: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform cross-modal reasoning across multiple content types"""
        pass
    
    # Enhanced Memory & Context Management
    @abstractmethod
    async def store_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        importance_score: float = 0.5,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store information in persistent memory"""
        pass
    
    @abstractmethod
    async def retrieve_memories(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on query"""
        pass
    
    @abstractmethod
    async def get_personalized_context(
        self,
        base_context: List[AgentMessage],
        user_id: str,
        session_id: Optional[str] = None
    ) -> List[AgentMessage]:
        """Get personalized conversation context for user"""
        pass
    
    @abstractmethod
    async def compress_context(
        self,
        session_id: str,
        target_token_count: int,
        strategy: str = "summarization"
    ) -> Dict[str, Any]:
        """Compress conversation context to fit token limits"""
        pass
    
    @abstractmethod
    async def get_memory_analytics(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get memory usage analytics and insights"""
        pass
    
    @abstractmethod
    async def update_personalization(
        self,
        user_id: str,
        interaction_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update user personalization based on interaction"""
        pass
    
    @abstractmethod
    async def predict_user_intent(
        self,
        user_message: str,
        context: List[AgentMessage],
        user_id: str
    ) -> Dict[str, float]:
        """Predict user intent from message and context"""
        pass


# Type aliases for convenience
AgentResponseCallback = Callable[[IAgentResponse], None]
AgentErrorCallback = Callable[[Exception], None]
AgentStreamCallback = Callable[[str], None]
