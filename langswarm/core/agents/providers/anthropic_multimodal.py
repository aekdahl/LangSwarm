"""
Anthropic Multimodal Provider Implementation for LangSwarm V2

Enhanced Anthropic integration with multimodal capabilities including:
- Vision (Claude 3 Vision)
- Document analysis
- Cross-modal reasoning
"""

import asyncio
import base64
import io
import logging
from typing import Dict, Any, List, Optional

try:
    import anthropic
    from anthropic import AsyncAnthropic
except ImportError:
    anthropic = None
    AsyncAnthropic = None

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


class AnthropicMultimodalProcessor(BaseMultimodalProcessor):
    """Anthropic-specific multimodal processor using Claude Vision"""
    
    def __init__(self, client: AsyncAnthropic):
        super().__init__()
        self.client = client
    
    @property
    def supported_modalities(self) -> List[ModalityType]:
        """Anthropic supported modalities"""
        return [
            ModalityType.TEXT,
            ModalityType.IMAGE,
            ModalityType.DOCUMENT  # Through vision for images of documents
        ]
    
    @property
    def supported_media_types(self) -> List[MediaType]:
        """Anthropic supported media types"""
        return [
            # Images (Claude 3 Vision)
            MediaType.IMAGE_JPEG,
            MediaType.IMAGE_PNG,
            MediaType.IMAGE_GIF,
            MediaType.IMAGE_WEBP,
            
            # Documents (via vision)
            MediaType.DOCUMENT_PDF,
            MediaType.TEXT_PLAIN
        ]
    
    async def analyze_image(
        self,
        image: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze image using Claude Vision"""
        try:
            # Prepare image for Anthropic API
            image_data = await self._prepare_image_for_api(image)
            if not image_data:
                return {"error": "Failed to prepare image for analysis"}
            
            # Default instructions if none provided
            if not instructions:
                instructions = "Analyze this image in detail. Describe what you see, including objects, people, text, colors, composition, and any other notable features."
            
            # Create vision request for Claude
            message = {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_data["media_type"],
                            "data": image_data["data"]
                        }
                    },
                    {
                        "type": "text",
                        "text": instructions
                    }
                ]
            }
            
            # Call Claude Vision API
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",  # Use Claude 3 Sonnet for vision
                max_tokens=1000,
                messages=[message]
            )
            
            analysis = {
                "description": response.content[0].text,
                "model_used": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "confidence": "high",
                "analysis_type": "claude_vision"
            }
            
            # Extract text if specifically requested
            if "text" in instructions.lower() or "ocr" in instructions.lower():
                text_extraction_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_data["media_type"],
                                "data": image_data["data"]
                            }
                        },
                        {
                            "type": "text",
                            "text": "Extract all readable text from this image. Return only the text content, preserving formatting where possible."
                        }
                    ]
                }
                
                text_response = await self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=500,
                    messages=[text_extraction_message]
                )
                
                extracted_text = text_response.content[0].text
                if extracted_text and len(extracted_text.strip()) > 0:
                    analysis["extracted_text"] = extracted_text.strip()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Claude image analysis failed: {e}")
            return {"error": f"Claude image analysis failed: {str(e)}"}
    
    async def analyze_audio(
        self,
        audio: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze audio - Claude doesn't have native audio processing"""
        return {
            "error": "Claude does not support direct audio processing",
            "suggestion": "Convert audio to text first using a speech recognition service"
        }
    
    async def analyze_document(
        self,
        document: MultimodalContent,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze document using Claude"""
        try:
            # For text documents, read directly
            if document.media_type == MediaType.TEXT_PLAIN:
                text_content = document.get_content_text()
                if not text_content:
                    return {"error": "No text content available"}
                
                analysis_prompt = f"Analyze this document based on the following instructions: {instructions or 'Provide a comprehensive analysis of this document, including its structure, key points, and content summary.'}\n\nDocument content:\n{text_content}"
                
                response = await self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": analysis_prompt}]
                )
                
                return {
                    "analysis": response.content[0].text,
                    "document_type": "text",
                    "model_used": response.model,
                    "word_count": len(text_content.split()),
                    "character_count": len(text_content)
                }
            
            # For PDF and other documents, use base implementation
            return await super().analyze_document(document, instructions)
            
        except Exception as e:
            logger.error(f"Claude document analysis failed: {e}")
            return {"error": f"Claude document analysis failed: {str(e)}"}
    
    async def cross_modal_reasoning(
        self,
        contents: List[MultimodalContent],
        question: str
    ) -> Dict[str, Any]:
        """Perform cross-modal reasoning using Claude"""
        try:
            # Prepare content for analysis
            message_content = []
            
            # Add the question first
            message_content.append({
                "type": "text",
                "text": f"Analyze the following content and answer this question: {question}\n\nContent provided:"
            })
            
            text_parts = []
            
            # Process each content piece
            for i, content in enumerate(contents):
                if content.modality == ModalityType.IMAGE:
                    image_data = await self._prepare_image_for_api(content)
                    if image_data:
                        message_content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_data["media_type"],
                                "data": image_data["data"]
                            }
                        })
                        message_content.append({
                            "type": "text",
                            "text": f"Image {i+1} (above)"
                        })
                
                elif content.modality == ModalityType.TEXT:
                    text = content.get_content_text()
                    if text:
                        text_parts.append(f"Text content {i+1}: {text[:1000]}")
                
                elif content.modality == ModalityType.DOCUMENT:
                    # Extract text from document
                    text = await self.extract_text(content)
                    if text:
                        text_parts.append(f"Document content {i+1}: {text[:1000]}")
            
            # Add text content
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
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                messages=[{"role": "user", "content": message_content}]
            )
            
            return {
                "question": question,
                "answer": response.content[0].text,
                "model_used": response.model,
                "content_types": [content.modality.value for content in contents],
                "reasoning_method": "claude_multimodal",
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Claude cross-modal reasoning failed: {e}")
            return {"error": f"Cross-modal reasoning failed: {str(e)}"}
    
    async def _prepare_image_for_api(self, image: MultimodalContent) -> Optional[Dict[str, str]]:
        """Prepare image for Claude API (base64 format)"""
        try:
            # Get image bytes
            image_bytes = image.get_content_bytes()
            if not image_bytes:
                return None
            
            # Validate and resize image if needed
            if Image:
                try:
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    
                    # Claude has size limits, resize if needed
                    max_size = 1568  # Claude's max dimension
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
            
            return {
                "media_type": mime_type,
                "data": base64_image
            }
            
        except Exception as e:
            logger.error(f"Failed to prepare image for Claude API: {e}")
            return None


# Enhanced Anthropic Provider with multimodal support
class AnthropicMultimodalProvider(IAgentProvider):
    """Enhanced Anthropic provider with multimodal capabilities"""
    
    def __init__(self):
        if not anthropic:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
        
        self._client_cache: Dict[str, AsyncAnthropic] = {}
        self._processor_cache: Dict[str, AnthropicMultimodalProcessor] = {}
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.ANTHROPIC
    
    @property
    def supported_models(self) -> List[str]:
        """Anthropic models with multimodal capabilities"""
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",  # Latest Claude 3.5
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
    
    @property
    def supported_capabilities(self) -> List[AgentCapability]:
        """Enhanced Anthropic capabilities"""
        return [
            AgentCapability.TEXT_GENERATION,
            AgentCapability.FUNCTION_CALLING,
            AgentCapability.TOOL_USE,
            AgentCapability.STREAMING,
            AgentCapability.VISION,  # Claude 3 Vision
            AgentCapability.SYSTEM_PROMPTS,
            AgentCapability.CONVERSATION_HISTORY,
            AgentCapability.MULTIMODAL,
            
            # Enhanced multimodal capabilities
            AgentCapability.IMAGE_ANALYSIS,
            AgentCapability.DOCUMENT_ANALYSIS,
            AgentCapability.OCR,
            AgentCapability.CROSS_MODAL_REASONING,
            AgentCapability.CONTENT_TRANSFORMATION
        ]
    
    def get_multimodal_processor(self, config: IAgentConfiguration) -> AnthropicMultimodalProcessor:
        """Get multimodal processor for this configuration"""
        cache_key = f"{config.api_key[:10]}_{config.base_url or 'default'}"
        
        if cache_key not in self._processor_cache:
            client = self._get_client(config)
            self._processor_cache[cache_key] = AnthropicMultimodalProcessor(client)
        
        return self._processor_cache[cache_key]
    
    def _get_client(self, config: IAgentConfiguration) -> AsyncAnthropic:
        """Get or create Anthropic client"""
        cache_key = f"{config.api_key[:10]}_{config.base_url or 'default'}"
        
        if cache_key not in self._client_cache:
            client_kwargs = {"api_key": config.api_key}
            if config.base_url:
                client_kwargs["base_url"] = config.base_url
            
            self._client_cache[cache_key] = AsyncAnthropic(**client_kwargs)
        
        return self._client_cache[cache_key]
    
    async def validate_configuration(self, config: IAgentConfiguration) -> bool:
        """Validate Anthropic configuration with multimodal support"""
        if config.model not in self.supported_models:
            raise ValueError(f"Model {config.model} not supported by Anthropic provider")
        
        if not config.api_key:
            raise ValueError("API key required for Anthropic provider")
        
        return True
    
    # ... (implement other IAgentProvider methods as needed)
