"""
OpenAI Multimodal Provider Implementation for LangSwarm V2

Enhanced OpenAI integration with complete multimodal capabilities including:
- Vision (GPT-4V, GPT-4o)
- Image generation (DALL-E)
- Audio transcription (Whisper)
- Text-to-speech (TTS)
- Document analysis
- Cross-modal reasoning
"""

import asyncio
import base64
import io
import logging
import mimetypes
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    openai = None
    AsyncOpenAI = None

try:
    from PIL import Image
except ImportError:
    Image = None

from ..interfaces import (
    IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, ProviderType
)
from ..base import AgentResponse, AgentSession
from ..multimodal import (
    IMultimodalProcessor, MultimodalContent, MultimodalRequest, MultimodalResponse,
    MediaType, ModalityType, ProcessingMode, create_image_content, create_audio_content
)
from ..multimodal_processor import BaseMultimodalProcessor

logger = logging.getLogger(__name__)


class OpenAIMultimodalProcessor(BaseMultimodalProcessor):
    """OpenAI-specific multimodal processor using OpenAI APIs"""
    
    def __init__(self, client: AsyncOpenAI):
        super().__init__()
        self.client = client
    
    @property
    def supported_modalities(self) -> List[ModalityType]:
        """OpenAI supported modalities"""
        return [
            ModalityType.TEXT,
            ModalityType.IMAGE,
            ModalityType.AUDIO,
            ModalityType.DOCUMENT  # Through vision for images of documents
        ]
    
    @property
    def supported_media_types(self) -> List[MediaType]:
        """OpenAI supported media types"""
        return [
            # Images
            MediaType.IMAGE_JPEG,
            MediaType.IMAGE_PNG,
            MediaType.IMAGE_GIF,
            MediaType.IMAGE_WEBP,
            
            # Audio
            MediaType.AUDIO_MP3,
            MediaType.AUDIO_WAV,
            MediaType.AUDIO_AAC,
            MediaType.AUDIO_M4A,
            MediaType.AUDIO_OGG,
            MediaType.AUDIO_FLAC,
            
            # Documents (via vision)
            MediaType.DOCUMENT_PDF,
            MediaType.TEXT_PLAIN
        ]
    
    async def analyze_image(
        self,
        image: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze image using OpenAI Vision API"""
        try:
            # Prepare image for OpenAI API
            image_url = await self._prepare_image_for_api(image)
            if not image_url:
                return {"error": "Failed to prepare image for analysis"}
            
            # Default instructions if none provided
            if not instructions:
                instructions = "Analyze this image in detail. Describe what you see, including objects, people, text, colors, composition, and any other notable features."
            
            # Create vision request
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": instructions
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ]
            
            # Call OpenAI Vision API
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Use gpt-4o for best vision capabilities
                messages=messages,
                max_tokens=1000
            )
            
            analysis = {
                "description": response.choices[0].message.content,
                "model_used": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "confidence": "high",  # OpenAI generally provides high-quality results
                "analysis_type": "openai_vision"
            }
            
            # Extract additional structured information if possible
            if "text" in instructions.lower() or "ocr" in instructions.lower():
                # Try to extract text specifically
                text_extraction_messages = [
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all readable text from this image. Return only the text content, preserving formatting where possible."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ]
                
                text_response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=text_extraction_messages,
                    max_tokens=500
                )
                
                extracted_text = text_response.choices[0].message.content
                if extracted_text and len(extracted_text.strip()) > 0:
                    analysis["extracted_text"] = extracted_text.strip()
            
            return analysis
            
        except Exception as e:
            logger.error(f"OpenAI image analysis failed: {e}")
            return {"error": f"OpenAI image analysis failed: {str(e)}"}
    
    async def analyze_audio(
        self,
        audio: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze audio using OpenAI Whisper API"""
        try:
            # Get audio file
            audio_path = audio.file_path
            audio_bytes = audio.get_content_bytes()
            
            if not audio_path and not audio_bytes:
                return {"error": "No audio data available"}
            
            # Transcribe with Whisper
            if audio_path:
                with open(audio_path, 'rb') as audio_file:
                    transcription = await self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json"
                    )
            else:
                # Create a file-like object from bytes
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = "audio.mp3"  # Whisper needs a filename
                
                transcription = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            analysis = {
                "transcription": transcription.text,
                "language": transcription.language,
                "duration": transcription.duration,
                "model_used": "whisper-1",
                "confidence": "high",
                "analysis_type": "openai_whisper"
            }
            
            # Add segment information if available
            if hasattr(transcription, 'segments') and transcription.segments:
                analysis["segments"] = [
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text
                    }
                    for segment in transcription.segments
                ]
            
            # Additional analysis based on instructions
            if instructions and transcription.text:
                analysis_prompt = f"Analyze this transcribed audio content based on the following instructions: {instructions}\n\nTranscription: {transcription.text}"
                
                analysis_response = await self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": analysis_prompt}],
                    max_tokens=500
                )
                
                analysis["content_analysis"] = analysis_response.choices[0].message.content
            
            return analysis
            
        except Exception as e:
            logger.error(f"OpenAI audio analysis failed: {e}")
            return {"error": f"OpenAI audio analysis failed: {str(e)}"}
    
    async def analyze_document(
        self,
        document: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze document using OpenAI (convert to image for vision if needed)"""
        try:
            # For text documents, read directly
            if document.media_type == MediaType.TEXT_PLAIN:
                text_content = document.get_content_text()
                if not text_content:
                    return {"error": "No text content available"}
                
                analysis_prompt = f"Analyze this document based on the following instructions: {instructions or 'Provide a comprehensive analysis of this document, including its structure, key points, and content summary.'}\n\nDocument content:\n{text_content[:4000]}"  # Limit to 4000 chars
                
                response = await self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": analysis_prompt}],
                    max_tokens=1000
                )
                
                return {
                    "analysis": response.choices[0].message.content,
                    "document_type": "text",
                    "model_used": response.model,
                    "word_count": len(text_content.split()),
                    "character_count": len(text_content)
                }
            
            # For PDF and other documents, would need to convert to images
            # This is a simplified implementation
            return await super().analyze_document(document, instructions)
            
        except Exception as e:
            logger.error(f"OpenAI document analysis failed: {e}")
            return {"error": f"OpenAI document analysis failed: {str(e)}"}
    
    async def cross_modal_reasoning(
        self,
        contents: List[MultimodalContent],
        question: str
    ) -> Dict[str, Any]:
        """Perform cross-modal reasoning using OpenAI models"""
        try:
            # Prepare content for analysis
            message_content = [
                {
                    "type": "text",
                    "text": f"Analyze the following content and answer this question: {question}\n\nContent provided:"
                }
            ]
            
            text_parts = []
            
            # Process each content piece
            for i, content in enumerate(contents):
                if content.modality == ModalityType.IMAGE:
                    image_url = await self._prepare_image_for_api(content)
                    if image_url:
                        message_content.append({
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        })
                        message_content.append({
                            "type": "text", 
                            "text": f"Image {i+1} (above)"
                        })
                
                elif content.modality == ModalityType.TEXT:
                    text = content.get_content_text()
                    if text:
                        text_parts.append(f"Text content {i+1}: {text[:1000]}")
                
                elif content.modality == ModalityType.AUDIO:
                    # First transcribe the audio
                    audio_analysis = await self.analyze_audio(content)
                    if "transcription" in audio_analysis:
                        text_parts.append(f"Audio transcription {i+1}: {audio_analysis['transcription']}")
                
                elif content.modality == ModalityType.DOCUMENT:
                    # Extract text from document
                    text = await self.extract_text(content)
                    if text:
                        text_parts.append(f"Document content {i+1}: {text[:1000]}")
            
            # Add text content to message
            if text_parts:
                message_content.append({
                    "type": "text",
                    "text": "\n\n".join(text_parts)
                })
            
            # Add final instruction
            message_content.append({
                "type": "text",
                "text": f"\n\nPlease provide a comprehensive answer to the question: {question}"
            })
            
            # Make API call
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Use gpt-4o for best multimodal reasoning
                messages=[{"role": "user", "content": message_content}],
                max_tokens=1500
            )
            
            return {
                "question": question,
                "answer": response.choices[0].message.content,
                "model_used": response.model,
                "content_types": [content.modality.value for content in contents],
                "reasoning_method": "openai_multimodal",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"OpenAI cross-modal reasoning failed: {e}")
            return {"error": f"Cross-modal reasoning failed: {str(e)}"}
    
    async def generate_image(
        self,
        prompt: str,
        style: str = "natural",
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> MultimodalContent:
        """Generate image using DALL-E"""
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1
            )
            
            image_url = response.data[0].url
            revised_prompt = response.data[0].revised_prompt
            
            # Create multimodal content
            image_content = create_image_content(
                image_url,
                instructions=f"Generated image for prompt: {prompt}"
            )
            
            image_content.metadata.title = "DALL-E Generated Image"
            image_content.metadata.author = "OpenAI DALL-E 3"
            image_content.analysis_results = {
                "generation_prompt": prompt,
                "revised_prompt": revised_prompt,
                "model": "dall-e-3",
                "style": style,
                "size": size,
                "quality": quality
            }
            
            return image_content
            
        except Exception as e:
            logger.error(f"DALL-E image generation failed: {e}")
            raise Exception(f"Image generation failed: {str(e)}")
    
    async def text_to_speech(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1"
    ) -> MultimodalContent:
        """Convert text to speech using OpenAI TTS"""
        try:
            response = await self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            
            # Get audio bytes
            audio_bytes = response.content
            
            # Create multimodal content
            audio_content = create_audio_content(
                audio_bytes,
                instructions=f"Generated speech for text: {text[:100]}..."
            )
            
            audio_content.media_type = MediaType.AUDIO_MP3
            audio_content.metadata.title = "OpenAI TTS Generated Audio"
            audio_content.metadata.author = "OpenAI TTS"
            audio_content.analysis_results = {
                "source_text": text,
                "voice": voice,
                "model": model,
                "generation_method": "openai_tts"
            }
            
            return audio_content
            
        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            raise Exception(f"Text-to-speech failed: {str(e)}")
    
    async def _prepare_image_for_api(self, image: MultimodalContent) -> Optional[str]:
        """Prepare image for OpenAI API (base64 or URL)"""
        try:
            # If it's already a URL, return it
            if image.url:
                return image.url
            
            # Get image bytes
            image_bytes = image.get_content_bytes()
            if not image_bytes:
                return None
            
            # Validate and resize image if needed
            if Image:
                try:
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    
                    # OpenAI has size limits, resize if needed
                    max_size = 2048
                    if pil_image.width > max_size or pil_image.height > max_size:
                        pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                        
                        # Convert back to bytes
                        output = io.BytesIO()
                        format = pil_image.format or 'JPEG'
                        pil_image.save(output, format=format)
                        image_bytes = output.getvalue()
                except Exception as e:
                    logger.warning(f"Image processing failed, using original: {e}")
            
            # Convert to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Determine MIME type
            mime_type = image.media_type.value if image.media_type else "image/jpeg"
            
            # Return data URL
            return f"data:{mime_type};base64,{base64_image}"
            
        except Exception as e:
            logger.error(f"Failed to prepare image for API: {e}")
            return None


class OpenAIMultimodalProvider(IAgentProvider):
    """Enhanced OpenAI provider with full multimodal capabilities"""
    
    def __init__(self):
        if not openai:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        self._client_cache: Dict[str, AsyncOpenAI] = {}
        self._processor_cache: Dict[str, OpenAIMultimodalProcessor] = {}
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI
    
    @property
    def supported_models(self) -> List[str]:
        """OpenAI models with enhanced multimodal capabilities"""
        return [
            "gpt-4o",           # Best multimodal model
            "gpt-4o-mini",      # Cost-effective multimodal
            "gpt-4-turbo",      # High performance
            "gpt-4",            # Standard
            "gpt-4-vision-preview",  # Legacy vision
            "gpt-3.5-turbo",    # Basic text
            "dall-e-3",         # Image generation
            "dall-e-2",         # Image generation
            "whisper-1",        # Audio transcription
            "tts-1",            # Text-to-speech
            "tts-1-hd"          # High-quality TTS
        ]
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        """Enhanced OpenAI capabilities"""
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.FUNCTION_CALLING,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.VISION,
            AgentCapability.IMAGE_GENERATION,
            AgentCapability.SYSTEM_PROMPTS,
            AgentCapability.CONVERSATION_HISTORY,
            AgentCapability.REALTIME_VOICE,
            AgentCapability.MULTIMODAL,
            
            # Enhanced multimodal capabilities
            AgentCapability.IMAGE_ANALYSIS,
            AgentCapability.AUDIO_PROCESSING,
            AgentCapability.DOCUMENT_ANALYSIS,
            AgentCapability.OCR,
            AgentCapability.SPEECH_TO_TEXT,
            AgentCapability.TEXT_TO_SPEECH,
            AgentCapability.CROSS_MODAL_REASONING,
            AgentCapability.CONTENT_GENERATION
        ]
    
    def get_multimodal_processor(self, config: IAgentConfiguration) -> OpenAIMultimodalProcessor:
        """Get multimodal processor for this configuration"""
        cache_key = f"{config.api_key[:10]}_{config.base_url or 'default'}"
        
        if cache_key not in self._processor_cache:
            client = self._get_client(config)
            self._processor_cache[cache_key] = OpenAIMultimodalProcessor(client)
        
        return self._processor_cache[cache_key]
    
    def _get_client(self, config: IAgentConfiguration) -> AsyncOpenAI:
        """Get or create OpenAI client"""
        cache_key = f"{config.api_key[:10]}_{config.base_url or 'default'}"
        
        if cache_key not in self._client_cache:
            client_kwargs = {"api_key": config.api_key}
            if config.base_url:
                client_kwargs["base_url"] = config.base_url
            
            self._client_cache[cache_key] = AsyncOpenAI(**client_kwargs)
        
        return self._client_cache[cache_key]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate OpenAI configuration with multimodal support"""
        if config.model not in self.supported_models:
            raise ValueError(f"Model {config.model} not supported by OpenAI provider")
        
        if not config.api_key:
            raise ValueError("API key required for OpenAI provider")
        
        # Test API connection
        try:
            client = self._get_client(config)
            await client.models.list()
            return True
        except Exception as e:
            raise ValueError(f"Failed to validate OpenAI configuration: {e}")
    
    # ... (implement other IAgentProvider methods as needed)
    # This would include the existing OpenAI provider methods plus multimodal enhancements
