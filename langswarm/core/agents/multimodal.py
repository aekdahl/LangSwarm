"""
LangSwarm V2 Multimodal Agent System

Complete multimodal capabilities for the V2 agent system including:
- Image processing and analysis
- Video understanding and transcription  
- Audio processing and voice interaction
- Document analysis and OCR integration
- Cross-modal reasoning and understanding
"""

import base64
import io
import mimetypes
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO
import uuid

# Type hints for multimodal content
ImageType = Union[str, bytes, BinaryIO, Path]
VideoType = Union[str, bytes, BinaryIO, Path]
AudioType = Union[str, bytes, BinaryIO, Path]
DocumentType = Union[str, bytes, BinaryIO, Path]


class MediaType(Enum):
    """Supported media types for multimodal processing"""
    # Image types
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png" 
    IMAGE_GIF = "image/gif"
    IMAGE_WEBP = "image/webp"
    IMAGE_BMP = "image/bmp"
    IMAGE_TIFF = "image/tiff"
    IMAGE_SVG = "image/svg+xml"
    
    # Video types
    VIDEO_MP4 = "video/mp4"
    VIDEO_AVI = "video/avi"
    VIDEO_MOV = "video/mov"
    VIDEO_WMV = "video/wmv"
    VIDEO_FLV = "video/flv"
    VIDEO_WEBM = "video/webm"
    VIDEO_MKV = "video/mkv"
    
    # Audio types
    AUDIO_MP3 = "audio/mp3"
    AUDIO_WAV = "audio/wav"
    AUDIO_AAC = "audio/aac"
    AUDIO_OGG = "audio/ogg"
    AUDIO_FLAC = "audio/flac"
    AUDIO_M4A = "audio/m4a"
    AUDIO_WMA = "audio/wma"
    
    # Document types
    DOCUMENT_PDF = "application/pdf"
    DOCUMENT_DOC = "application/msword"
    DOCUMENT_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    DOCUMENT_XLS = "application/vnd.ms-excel"
    DOCUMENT_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    DOCUMENT_PPT = "application/vnd.ms-powerpoint"
    DOCUMENT_PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    DOCUMENT_TXT = "text/plain"
    DOCUMENT_RTF = "application/rtf"
    DOCUMENT_ODT = "application/vnd.oasis.opendocument.text"
    
    # Web content
    TEXT_HTML = "text/html"
    TEXT_MARKDOWN = "text/markdown"
    TEXT_CSV = "text/csv"
    TEXT_PLAIN = "text/plain"  # Add missing TEXT_PLAIN
    APPLICATION_JSON = "application/json"
    APPLICATION_XML = "application/xml"


class ProcessingMode(Enum):
    """Processing modes for multimodal content"""
    ANALYZE = "analyze"  # Analyze and describe content
    EXTRACT = "extract"  # Extract text, objects, or data
    TRANSFORM = "transform"  # Transform or modify content
    GENERATE = "generate"  # Generate new content based on input
    COMPARE = "compare"  # Compare multiple pieces of content
    SEARCH = "search"  # Search within content
    TRANSLATE = "translate"  # Translate content between formats/languages


class ModalityType(Enum):
    """Types of modalities for cross-modal reasoning"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    CODE = "code"
    DATA = "data"


@dataclass
class MediaMetadata:
    """Metadata for media content"""
    filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    duration: Optional[float] = None  # For video/audio in seconds
    dimensions: Optional[tuple] = None  # For images/video (width, height)
    format: Optional[str] = None
    creation_date: Optional[datetime] = None
    resolution: Optional[str] = None
    bit_rate: Optional[int] = None  # For audio/video
    sample_rate: Optional[int] = None  # For audio
    channels: Optional[int] = None  # For audio
    codec: Optional[str] = None
    language: Optional[str] = None
    encoding: Optional[str] = None
    page_count: Optional[int] = None  # For documents
    word_count: Optional[int] = None  # For text documents
    author: Optional[str] = None  # For documents
    title: Optional[str] = None  # For documents


@dataclass
class MultimodalContent:
    """Represents multimodal content with unified interface"""
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    modality: ModalityType = ModalityType.TEXT
    media_type: MediaType = MediaType.TEXT_PLAIN
    
    # Content data (one of these will be populated)
    text_content: Optional[str] = None
    binary_content: Optional[bytes] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    base64_content: Optional[str] = None
    
    # Content metadata
    metadata: MediaMetadata = field(default_factory=MediaMetadata)
    processing_hints: Dict[str, Any] = field(default_factory=dict)
    
    # Extracted features and analysis results
    extracted_text: Optional[str] = None
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate and normalize content after initialization"""
        if self.file_path and Path(self.file_path).exists():
            # Infer media type from file extension
            mime_type, _ = mimetypes.guess_type(self.file_path)
            if mime_type:
                try:
                    self.media_type = MediaType(mime_type)
                except ValueError:
                    # Unknown mime type, keep as is
                    pass
            
            # Set basic metadata
            path = Path(self.file_path)
            self.metadata.filename = path.name
            self.metadata.file_size = path.stat().st_size
            self.metadata.creation_date = datetime.fromtimestamp(path.stat().st_ctime)
    
    def get_content_bytes(self) -> Optional[bytes]:
        """Get content as bytes regardless of storage method"""
        if self.binary_content:
            return self.binary_content
        elif self.base64_content:
            return base64.b64decode(self.base64_content)
        elif self.file_path and Path(self.file_path).exists():
            with open(self.file_path, 'rb') as f:
                return f.read()
        elif self.text_content:
            return self.text_content.encode('utf-8')
        return None
    
    def get_content_text(self) -> Optional[str]:
        """Get content as text (if applicable)"""
        if self.text_content:
            return self.text_content
        elif self.extracted_text:
            return self.extracted_text
        elif self.modality == ModalityType.TEXT:
            content_bytes = self.get_content_bytes()
            if content_bytes:
                try:
                    return content_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    return None
        return None
    
    def set_content_from_file(self, file_path: str) -> None:
        """Load content from file"""
        self.file_path = file_path
        self.__post_init__()  # Update metadata
    
    def set_content_from_bytes(self, content: bytes, mime_type: str = None) -> None:
        """Set content from bytes"""
        self.binary_content = content
        if mime_type:
            try:
                self.media_type = MediaType(mime_type)
            except ValueError:
                pass
    
    def set_content_from_base64(self, base64_str: str, mime_type: str = None) -> None:
        """Set content from base64 string"""
        self.base64_content = base64_str
        if mime_type:
            try:
                self.media_type = MediaType(mime_type)
            except ValueError:
                pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "content_id": self.content_id,
            "modality": self.modality.value,
            "media_type": self.media_type.value,
            "text_content": self.text_content,
            "file_path": self.file_path,
            "url": self.url,
            "base64_content": self.base64_content,
            "metadata": {
                "filename": self.metadata.filename,
                "file_size": self.metadata.file_size,
                "mime_type": self.metadata.mime_type,
                "duration": self.metadata.duration,
                "dimensions": self.metadata.dimensions,
                "format": self.metadata.format,
                "creation_date": self.metadata.creation_date.isoformat() if self.metadata.creation_date else None,
                "resolution": self.metadata.resolution,
                "bit_rate": self.metadata.bit_rate,
                "sample_rate": self.metadata.sample_rate,
                "channels": self.metadata.channels,
                "codec": self.metadata.codec,
                "language": self.metadata.language,
                "encoding": self.metadata.encoding,
                "page_count": self.metadata.page_count,
                "word_count": self.metadata.word_count,
                "author": self.metadata.author,
                "title": self.metadata.title
            },
            "processing_hints": self.processing_hints,
            "extracted_text": self.extracted_text,
            "analysis_results": self.analysis_results,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }


@dataclass
class MultimodalRequest:
    """Request for multimodal processing"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: List[MultimodalContent] = field(default_factory=list)
    processing_mode: ProcessingMode = ProcessingMode.ANALYZE
    instructions: Optional[str] = None
    output_format: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    cross_modal_context: bool = True  # Whether to consider relationships between modalities
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_content(self, content: MultimodalContent) -> None:
        """Add content to the request"""
        self.content.append(content)
    
    def add_image(self, image: ImageType, **kwargs) -> MultimodalContent:
        """Add image content"""
        content = MultimodalContent(
            modality=ModalityType.IMAGE,
            **kwargs
        )
        
        if isinstance(image, str):
            if image.startswith('http'):
                content.url = image
            elif image.startswith('data:'):
                # Data URL
                header, data = image.split(',', 1)
                content.base64_content = data
                mime_type = header.split(';')[0].split(':')[1]
                content.media_type = MediaType(mime_type)
            else:
                content.file_path = image
        elif isinstance(image, bytes):
            content.binary_content = image
        elif isinstance(image, Path):
            content.file_path = str(image)
        elif hasattr(image, 'read'):
            content.binary_content = image.read()
        
        self.add_content(content)
        return content
    
    def add_video(self, video: VideoType, **kwargs) -> MultimodalContent:
        """Add video content"""
        content = MultimodalContent(
            modality=ModalityType.VIDEO,
            **kwargs
        )
        
        if isinstance(video, str):
            if video.startswith('http'):
                content.url = video
            else:
                content.file_path = video
        elif isinstance(video, bytes):
            content.binary_content = video
        elif isinstance(video, Path):
            content.file_path = str(video)
        elif hasattr(video, 'read'):
            content.binary_content = video.read()
        
        self.add_content(content)
        return content
    
    def add_audio(self, audio: AudioType, **kwargs) -> MultimodalContent:
        """Add audio content"""
        content = MultimodalContent(
            modality=ModalityType.AUDIO,
            **kwargs
        )
        
        if isinstance(audio, str):
            if audio.startswith('http'):
                content.url = audio
            else:
                content.file_path = audio
        elif isinstance(audio, bytes):
            content.binary_content = audio
        elif isinstance(audio, Path):
            content.file_path = str(audio)
        elif hasattr(audio, 'read'):
            content.binary_content = audio.read()
        
        self.add_content(content)
        return content
    
    def add_document(self, document: DocumentType, **kwargs) -> MultimodalContent:
        """Add document content"""
        content = MultimodalContent(
            modality=ModalityType.DOCUMENT,
            **kwargs
        )
        
        if isinstance(document, str):
            if document.startswith('http'):
                content.url = document
            else:
                content.file_path = document
        elif isinstance(document, bytes):
            content.binary_content = document
        elif isinstance(document, Path):
            content.file_path = str(document)
        elif hasattr(document, 'read'):
            content.binary_content = document.read()
        
        self.add_content(content)
        return content
    
    def add_text(self, text: str, **kwargs) -> MultimodalContent:
        """Add text content"""
        content = MultimodalContent(
            modality=ModalityType.TEXT,
            text_content=text,
            media_type=MediaType.TEXT_PLAIN,
            **kwargs
        )
        self.add_content(content)
        return content


@dataclass
class MultimodalResponse:
    """Response from multimodal processing"""
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    success: bool = True
    error: Optional[str] = None
    
    # Processing results
    content_analysis: Dict[str, Any] = field(default_factory=dict)
    extracted_content: Dict[str, Any] = field(default_factory=dict)
    cross_modal_insights: Dict[str, Any] = field(default_factory=dict)
    
    # Generated content
    generated_text: Optional[str] = None
    generated_content: List[MultimodalContent] = field(default_factory=list)
    
    # Metadata
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_analysis(self, content_id: str, analysis: Dict[str, Any]) -> None:
        """Add analysis results for specific content"""
        self.content_analysis[content_id] = analysis
    
    def add_extracted_content(self, content_id: str, extracted: Any) -> None:
        """Add extracted content for specific content"""
        self.extracted_content[content_id] = extracted
    
    def add_cross_modal_insight(self, insight_type: str, insight: Any) -> None:
        """Add cross-modal insight"""
        self.cross_modal_insights[insight_type] = insight


class IMultimodalProcessor(ABC):
    """Interface for multimodal content processors"""
    
    @property
    @abstractmethod
    def supported_modalities(self) -> List[ModalityType]:
        """List of supported modalities"""
        pass
    
    @property
    @abstractmethod
    def supported_media_types(self) -> List[MediaType]:
        """List of supported media types"""
        pass
    
    @property
    @abstractmethod
    def supported_processing_modes(self) -> List[ProcessingMode]:
        """List of supported processing modes"""
        pass
    
    @abstractmethod
    async def process_content(
        self,
        request: MultimodalRequest
    ) -> MultimodalResponse:
        """Process multimodal content"""
        pass
    
    @abstractmethod
    async def analyze_image(
        self,
        image: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze image content"""
        pass
    
    @abstractmethod
    async def analyze_video(
        self,
        video: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze video content"""
        pass
    
    @abstractmethod
    async def analyze_audio(
        self,
        audio: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze audio content"""
        pass
    
    @abstractmethod
    async def analyze_document(
        self,
        document: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze document content"""
        pass
    
    @abstractmethod
    async def extract_text(
        self,
        content: MultimodalContent
    ) -> str:
        """Extract text from any supported content type"""
        pass
    
    @abstractmethod
    async def cross_modal_reasoning(
        self,
        contents: List[MultimodalContent],
        question: str
    ) -> Dict[str, Any]:
        """Perform cross-modal reasoning across multiple content types"""
        pass


class IMultimodalAgent(ABC):
    """Interface for agents with multimodal capabilities"""
    
    @property
    @abstractmethod
    def multimodal_processor(self) -> IMultimodalProcessor:
        """Get the multimodal processor"""
        pass
    
    @abstractmethod
    async def chat_multimodal(
        self,
        message: str,
        attachments: List[MultimodalContent] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> 'IAgentResponse':
        """Send a multimodal chat message"""
        pass
    
    @abstractmethod
    async def process_multimodal(
        self,
        request: MultimodalRequest,
        session_id: Optional[str] = None
    ) -> MultimodalResponse:
        """Process multimodal content directly"""
        pass
    
    @abstractmethod
    async def describe_image(
        self,
        image: ImageType,
        prompt: str = "Describe this image in detail",
        session_id: Optional[str] = None
    ) -> str:
        """Describe an image"""
        pass
    
    @abstractmethod
    async def analyze_document(
        self,
        document: DocumentType,
        questions: List[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a document and answer questions"""
        pass
    
    @abstractmethod
    async def transcribe_audio(
        self,
        audio: AudioType,
        language: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Transcribe audio to text"""
        pass
    
    @abstractmethod
    async def understand_video(
        self,
        video: VideoType,
        questions: List[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze video content and answer questions"""
        pass
    
    @abstractmethod
    async def compare_content(
        self,
        content1: MultimodalContent,
        content2: MultimodalContent,
        comparison_aspects: List[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare two pieces of multimodal content"""
        pass
    
    @abstractmethod
    async def search_in_content(
        self,
        content: MultimodalContent,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for specific information within content"""
        pass


# Helper functions for content creation
def create_image_content(
    image: ImageType,
    instructions: Optional[str] = None,
    **kwargs
) -> MultimodalContent:
    """Create image content from various input types"""
    content = MultimodalContent(
        modality=ModalityType.IMAGE,
        processing_hints={"instructions": instructions} if instructions else {},
        **kwargs
    )
    
    if isinstance(image, str):
        if image.startswith('http'):
            content.url = image
        elif image.startswith('data:'):
            header, data = image.split(',', 1)
            content.base64_content = data
            mime_type = header.split(';')[0].split(':')[1]
            try:
                content.media_type = MediaType(mime_type)
            except ValueError:
                pass
        else:
            content.file_path = image
    elif isinstance(image, bytes):
        content.binary_content = image
    elif isinstance(image, Path):
        content.file_path = str(image)
    elif hasattr(image, 'read'):
        content.binary_content = image.read()
    
    content.__post_init__()
    return content


def create_video_content(
    video: VideoType,
    instructions: Optional[str] = None,
    **kwargs
) -> MultimodalContent:
    """Create video content from various input types"""
    content = MultimodalContent(
        modality=ModalityType.VIDEO,
        processing_hints={"instructions": instructions} if instructions else {},
        **kwargs
    )
    
    if isinstance(video, str):
        if video.startswith('http'):
            content.url = video
        else:
            content.file_path = video
    elif isinstance(video, bytes):
        content.binary_content = video
    elif isinstance(video, Path):
        content.file_path = str(video)
    elif hasattr(video, 'read'):
        content.binary_content = video.read()
    
    content.__post_init__()
    return content


def create_audio_content(
    audio: AudioType,
    instructions: Optional[str] = None,
    **kwargs
) -> MultimodalContent:
    """Create audio content from various input types"""
    content = MultimodalContent(
        modality=ModalityType.AUDIO,
        processing_hints={"instructions": instructions} if instructions else {},
        **kwargs
    )
    
    if isinstance(audio, str):
        if audio.startswith('http'):
            content.url = audio
        else:
            content.file_path = audio
    elif isinstance(audio, bytes):
        content.binary_content = audio
    elif isinstance(audio, Path):
        content.file_path = str(audio)
    elif hasattr(audio, 'read'):
        content.binary_content = audio.read()
    
    content.__post_init__()
    return content


def create_document_content(
    document: DocumentType,
    instructions: Optional[str] = None,
    **kwargs
) -> MultimodalContent:
    """Create document content from various input types"""
    content = MultimodalContent(
        modality=ModalityType.DOCUMENT,
        processing_hints={"instructions": instructions} if instructions else {},
        **kwargs
    )
    
    if isinstance(document, str):
        if document.startswith('http'):
            content.url = document
        else:
            content.file_path = document
    elif isinstance(document, bytes):
        content.binary_content = document
    elif isinstance(document, Path):
        content.file_path = str(document)
    elif hasattr(document, 'read'):
        content.binary_content = document.read()
    
    content.__post_init__()
    return content


# Content validation utilities
def validate_media_type(content: MultimodalContent) -> bool:
    """Validate that content matches its declared media type"""
    if not content.get_content_bytes():
        return False
    
    # Add validation logic based on content inspection
    # This would include checking file headers, magic numbers, etc.
    return True


def get_content_info(content: MultimodalContent) -> Dict[str, Any]:
    """Get comprehensive information about multimodal content"""
    info = {
        "content_id": content.content_id,
        "modality": content.modality.value,
        "media_type": content.media_type.value,
        "has_content": bool(content.get_content_bytes()),
        "content_size": len(content.get_content_bytes()) if content.get_content_bytes() else 0,
        "metadata": content.metadata.__dict__,
        "processing_hints": content.processing_hints,
        "has_analysis": bool(content.analysis_results),
        "has_extracted_text": bool(content.extracted_text)
    }
    return info
