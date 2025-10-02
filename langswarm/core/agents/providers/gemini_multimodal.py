"""
Google Gemini Multimodal Provider Implementation for LangSwarm V2

Enhanced Gemini integration with comprehensive multimodal capabilities including:
- Vision (Gemini Pro Vision)
- Video understanding
- Audio processing
- Document analysis
- Cross-modal reasoning
"""

import asyncio
import base64
import io
import logging
from typing import Dict, Any, List, Optional

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None
    HarmCategory = None
    HarmBlockThreshold = None

try:
    from PIL import Image
except ImportError:
    Image = None

from ..interfaces import (
    IAgentProvider, IAgentConfiguration, AgentCapability, ProviderType
)
from ..multimodal import (
    IMultimodalProcessor, MultimodalContent, MultimodalRequest, MultimodalResponse,
    MediaType, ModalityType, ProcessingMode
)
from ..multimodal_processor import BaseMultimodalProcessor

logger = logging.getLogger(__name__)


class GeminiMultimodalProcessor(BaseMultimodalProcessor):
    """Gemini-specific multimodal processor with comprehensive capabilities"""
    
    def __init__(self, api_key: str):
        super().__init__()
        if not genai:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
        
        genai.configure(api_key=api_key)
        self.api_key = api_key
    
    @property
    def supported_modalities(self) -> List[ModalityType]:
        """Gemini supported modalities"""
        return [
            ModalityType.TEXT,
            ModalityType.IMAGE,
            ModalityType.VIDEO,
            ModalityType.AUDIO,
            ModalityType.DOCUMENT
        ]
    
    @property
    def supported_media_types(self) -> List[MediaType]:
        """Gemini supported media types"""
        return [
            # Images
            MediaType.IMAGE_JPEG,
            MediaType.IMAGE_PNG,
            MediaType.IMAGE_WEBP,
            
            # Video
            MediaType.VIDEO_MP4,
            MediaType.VIDEO_AVI,
            MediaType.VIDEO_MOV,
            MediaType.VIDEO_WEBM,
            
            # Audio
            MediaType.AUDIO_MP3,
            MediaType.AUDIO_WAV,
            MediaType.AUDIO_AAC,
            MediaType.AUDIO_OGG,
            
            # Documents
            MediaType.DOCUMENT_PDF,
            MediaType.TEXT_PLAIN
        ]
    
    async def analyze_image(
        self,
        image: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze image using Gemini Pro Vision"""
        try:
            # Prepare image
            image_data = await self._prepare_image_for_api(image)
            if not image_data:
                return {"error": "Failed to prepare image for analysis"}
            
            # Default instructions
            if not instructions:
                instructions = "Analyze this image in detail. Describe what you see, including objects, people, text, colors, composition, and any other notable features."
            
            # Create model
            model = genai.GenerativeModel('gemini-pro-vision')
            
            # Create content
            content = [instructions, image_data]
            
            # Generate response
            response = await asyncio.to_thread(model.generate_content, content)
            
            analysis = {
                "description": response.text,
                "model_used": "gemini-pro-vision",
                "confidence": "high",
                "analysis_type": "gemini_vision"
            }
            
            # Extract text if requested
            if "text" in instructions.lower() or "ocr" in instructions.lower():
                ocr_content = ["Extract all readable text from this image. Return only the text content.", image_data]
                ocr_response = await asyncio.to_thread(model.generate_content, ocr_content)
                
                extracted_text = ocr_response.text.strip()
                if extracted_text:
                    analysis["extracted_text"] = extracted_text
            
            return analysis
            
        except Exception as e:
            logger.error(f"Gemini image analysis failed: {e}")
            return {"error": f"Gemini image analysis failed: {str(e)}"}
    
    async def analyze_video(
        self,
        video: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze video using Gemini"""
        try:
            if not video.file_path:
                return {"error": "Video file path required for Gemini analysis"}
            
            # Upload video file to Gemini
            video_file = await asyncio.to_thread(
                genai.upload_file, 
                path=video.file_path
            )
            
            # Wait for processing
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(2)
                video_file = await asyncio.to_thread(genai.get_file, video_file.name)
            
            if video_file.state.name == "FAILED":
                return {"error": "Video processing failed"}
            
            # Create model
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Default instructions
            if not instructions:
                instructions = "Analyze this video comprehensively. Describe the scenes, actions, objects, people, and any text or audio content you can detect."
            
            # Analyze video
            response = await asyncio.to_thread(
                model.generate_content,
                [instructions, video_file]
            )
            
            analysis = {
                "description": response.text,
                "model_used": "gemini-1.5-pro",
                "video_duration": video_file.video_metadata.duration if hasattr(video_file, 'video_metadata') else None,
                "confidence": "high",
                "analysis_type": "gemini_video"
            }
            
            # Clean up uploaded file
            await asyncio.to_thread(genai.delete_file, video_file.name)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Gemini video analysis failed: {e}")
            return {"error": f"Gemini video analysis failed: {str(e)}"}
    
    async def analyze_audio(
        self,
        audio: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze audio using Gemini"""
        try:
            if not audio.file_path:
                return {"error": "Audio file path required for Gemini analysis"}
            
            # Upload audio file to Gemini
            audio_file = await asyncio.to_thread(
                genai.upload_file,
                path=audio.file_path
            )
            
            # Wait for processing
            while audio_file.state.name == "PROCESSING":
                await asyncio.sleep(1)
                audio_file = await asyncio.to_thread(genai.get_file, audio_file.name)
            
            if audio_file.state.name == "FAILED":
                return {"error": "Audio processing failed"}
            
            # Create model
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Default instructions
            if not instructions:
                instructions = "Transcribe this audio and analyze its content. Provide the transcription and describe the audio characteristics, speakers, emotions, and any other notable features."
            
            # Analyze audio
            response = await asyncio.to_thread(
                model.generate_content,
                [instructions, audio_file]
            )
            
            analysis = {
                "transcription_and_analysis": response.text,
                "model_used": "gemini-1.5-pro",
                "confidence": "high",
                "analysis_type": "gemini_audio"
            }
            
            # Try to extract just transcription
            transcription_response = await asyncio.to_thread(
                model.generate_content,
                ["Transcribe this audio file. Provide only the spoken text.", audio_file]
            )
            
            analysis["transcription"] = transcription_response.text.strip()
            
            # Clean up uploaded file
            await asyncio.to_thread(genai.delete_file, audio_file.name)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Gemini audio analysis failed: {e}")
            return {"error": f"Gemini audio analysis failed: {str(e)}"}
    
    async def analyze_document(
        self,
        document: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze document using Gemini"""
        try:
            # For text documents, read directly
            if document.media_type == MediaType.TEXT_PLAIN:
                text_content = document.get_content_text()
                if not text_content:
                    return {"error": "No text content available"}
                
                model = genai.GenerativeModel('gemini-pro')
                
                analysis_prompt = f"Analyze this document based on the following instructions: {instructions or 'Provide a comprehensive analysis of this document, including its structure, key points, and content summary.'}\n\nDocument content:\n{text_content}"
                
                response = await asyncio.to_thread(model.generate_content, analysis_prompt)
                
                return {
                    "analysis": response.text,
                    "document_type": "text",
                    "model_used": "gemini-pro",
                    "word_count": len(text_content.split()),
                    "character_count": len(text_content)
                }
            
            # For PDF documents, could upload to Gemini
            elif document.media_type == MediaType.DOCUMENT_PDF and document.file_path:
                try:
                    # Upload PDF to Gemini
                    pdf_file = await asyncio.to_thread(
                        genai.upload_file,
                        path=document.file_path
                    )
                    
                    # Wait for processing
                    while pdf_file.state.name == "PROCESSING":
                        await asyncio.sleep(2)
                        pdf_file = await asyncio.to_thread(genai.get_file, pdf_file.name)
                    
                    if pdf_file.state.name == "FAILED":
                        return {"error": "PDF processing failed"}
                    
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    
                    analysis_prompt = instructions or "Analyze this PDF document comprehensively. Extract key information, summarize the content, and identify important sections."
                    
                    response = await asyncio.to_thread(
                        model.generate_content,
                        [analysis_prompt, pdf_file]
                    )
                    
                    analysis = {
                        "analysis": response.text,
                        "document_type": "pdf",
                        "model_used": "gemini-1.5-pro"
                    }
                    
                    # Clean up uploaded file
                    await asyncio.to_thread(genai.delete_file, pdf_file.name)
                    
                    return analysis
                    
                except Exception as e:
                    logger.warning(f"PDF upload failed, falling back to base implementation: {e}")
                    return await super().analyze_document(document, instructions)
            
            # Fall back to base implementation
            return await super().analyze_document(document, instructions)
            
        except Exception as e:
            logger.error(f"Gemini document analysis failed: {e}")
            return {"error": f"Gemini document analysis failed: {str(e)}"}
    
    async def cross_modal_reasoning(
        self,
        contents: List[MultimodalContent],
        question: str
    ) -> Dict[str, Any]:
        """Perform cross-modal reasoning using Gemini"""
        try:
            # Create model
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Prepare content for analysis
            content_parts = [f"Analyze the following content and answer this question: {question}\n\nContent provided:"]
            
            # Process each content piece
            for i, content in enumerate(contents):
                if content.modality == ModalityType.IMAGE:
                    image_data = await self._prepare_image_for_api(content)
                    if image_data:
                        content_parts.append(f"Image {i+1}:")
                        content_parts.append(image_data)
                
                elif content.modality == ModalityType.TEXT:
                    text = content.get_content_text()
                    if text:
                        content_parts.append(f"Text content {i+1}: {text[:1000]}")
                
                elif content.modality == ModalityType.VIDEO and content.file_path:
                    # Upload video
                    video_file = await asyncio.to_thread(genai.upload_file, path=content.file_path)
                    
                    # Wait for processing
                    while video_file.state.name == "PROCESSING":
                        await asyncio.sleep(2)
                        video_file = await asyncio.to_thread(genai.get_file, video_file.name)
                    
                    if video_file.state.name != "FAILED":
                        content_parts.append(f"Video {i+1}:")
                        content_parts.append(video_file)
                
                elif content.modality == ModalityType.AUDIO and content.file_path:
                    # Upload audio
                    audio_file = await asyncio.to_thread(genai.upload_file, path=content.file_path)
                    
                    # Wait for processing
                    while audio_file.state.name == "PROCESSING":
                        await asyncio.sleep(1)
                        audio_file = await asyncio.to_thread(genai.get_file, audio_file.name)
                    
                    if audio_file.state.name != "FAILED":
                        content_parts.append(f"Audio {i+1}:")
                        content_parts.append(audio_file)
                
                elif content.modality == ModalityType.DOCUMENT:
                    text = await self.extract_text(content)
                    if text:
                        content_parts.append(f"Document content {i+1}: {text[:1000]}")
            
            # Add final instruction
            content_parts.append(f"\n\nPlease provide a comprehensive answer to the question: {question}")
            
            # Generate response
            response = await asyncio.to_thread(model.generate_content, content_parts)
            
            return {
                "question": question,
                "answer": response.text,
                "model_used": "gemini-1.5-pro",
                "content_types": [content.modality.value for content in contents],
                "reasoning_method": "gemini_multimodal"
            }
            
        except Exception as e:
            logger.error(f"Gemini cross-modal reasoning failed: {e}")
            return {"error": f"Cross-modal reasoning failed: {str(e)}"}
    
    async def _prepare_image_for_api(self, image: MultimodalContent):
        """Prepare image for Gemini API"""
        try:
            # Get image bytes
            image_bytes = image.get_content_bytes()
            if not image_bytes:
                return None
            
            # Create PIL Image
            if Image:
                pil_image = Image.open(io.BytesIO(image_bytes))
                return pil_image
            else:
                # Create a simple image object for Gemini
                return {
                    'mime_type': image.media_type.value if image.media_type else 'image/jpeg',
                    'data': image_bytes
                }
            
        except Exception as e:
            logger.error(f"Failed to prepare image for Gemini API: {e}")
            return None


class GeminiMultimodalProvider(IAgentProvider):
    """Enhanced Gemini provider with comprehensive multimodal capabilities"""
    
    def __init__(self):
        if not genai:
            raise ImportError("Google Generative AI package not installed. Run: pip install google-generativeai")
        
        self._processor_cache: Dict[str, GeminiMultimodalProcessor] = {}
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GEMINI
    
    @property
    def supported_models(self) -> List[str]:
        """Gemini models with multimodal capabilities"""
        return [
            "gemini-1.5-pro",       # Latest with best multimodal support
            "gemini-1.5-flash",     # Fast multimodal model
            "gemini-pro",           # Text and some vision
            "gemini-pro-vision",    # Vision-specific
            "gemini-ultra"          # Most capable (when available)
        ]
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        """Enhanced Gemini capabilities"""
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.FUNCTION_CALLING,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.VISION,
            AgentCapability.SYSTEM_PROMPTS,
            AgentCapability.CONVERSATION_HISTORY,
            AgentCapability.MULTIMODAL,
            
            # Enhanced multimodal capabilities
            AgentCapability.IMAGE_ANALYSIS,
            AgentCapability.VIDEO_UNDERSTANDING,
            AgentCapability.AUDIO_PROCESSING,
            AgentCapability.DOCUMENT_ANALYSIS,
            AgentCapability.OCR,
            AgentCapability.SPEECH_TO_TEXT,
            AgentCapability.CROSS_MODAL_REASONING,
            AgentCapability.CONTENT_TRANSFORMATION
        ]
    
    def get_multimodal_processor(self, config: IAgentConfiguration) -> GeminiMultimodalProcessor:
        """Get multimodal processor for this configuration"""
        cache_key = config.api_key[:10] if config.api_key else "default"
        
        if cache_key not in self._processor_cache:
            self._processor_cache[cache_key] = GeminiMultimodalProcessor(config.api_key)
        
        return self._processor_cache[cache_key]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate Gemini configuration with multimodal support"""
        if config.model not in self.supported_models:
            raise ValueError(f"Model {config.model} not supported by Gemini provider")
        
        if not config.api_key:
            raise ValueError("API key required for Gemini provider")
        
        # Test API connection
        try:
            genai.configure(api_key=config.api_key)
            model = genai.GenerativeModel('gemini-pro')
            await asyncio.to_thread(model.generate_content, "Test")
            return True
        except Exception as e:
            raise ValueError(f"Failed to validate Gemini configuration: {e}")
    
    # ... (implement other IAgentProvider methods as needed)
