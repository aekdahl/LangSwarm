"""
LangSwarm V2 Multimodal Agent Implementation

Enhanced agent implementation with complete multimodal capabilities including:
- Image processing and analysis
- Video understanding and transcription
- Audio processing and voice interaction
- Document analysis and OCR integration
- Cross-modal reasoning and understanding
- Enhanced memory and context management
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator

from .interfaces import (
    IAgent, IAgentProvider, IAgentConfiguration, IAgentSession, IAgentResponse,
    AgentMessage, AgentUsage, AgentCapability, AgentStatus, ProviderType
)
from .base import BaseAgent, AgentResponse
from .multimodal import (
    MultimodalContent, MultimodalRequest, MultimodalResponse, IMultimodalProcessor,
    ProcessingMode, ModalityType, create_image_content, create_video_content,
    create_audio_content, create_document_content
)

logger = logging.getLogger(__name__)


class MultimodalAgent(BaseAgent):
    """
    Enhanced agent with comprehensive multimodal capabilities.
    
    Extends the base agent with:
    - Full multimodal content processing
    - Cross-modal reasoning
    - Enhanced memory and context management
    - Personalization and analytics
    """
    
    def __init__(
        self,
        configuration: IAgentConfiguration,
        provider: IAgentProvider,
        agent_id: Optional[str] = None,
        name: Optional[str] = None
    ):
        super().__init__(configuration, provider, agent_id, name)
        self._multimodal_processor: Optional[IMultimodalProcessor] = None
        
        # Enhanced capabilities tracking
        self._enhanced_capabilities = self._detect_enhanced_capabilities()
    
    def _detect_enhanced_capabilities(self) -> List[AgentCapability]:
        """Detect enhanced capabilities based on provider and configuration"""
        capabilities = []
        
        # Check if provider has multimodal processor
        if hasattr(self.provider, 'get_multimodal_processor'):
            capabilities.extend([
                AgentCapability.MULTIMODAL,
                AgentCapability.IMAGE_ANALYSIS,
                AgentCapability.CROSS_MODAL_REASONING
            ])
            
            # Provider-specific capabilities
            if self.configuration.provider == ProviderType.OPENAI:
                capabilities.extend([
                    AgentCapability.VISION,
                    AgentCapability.AUDIO_PROCESSING,
                    AgentCapability.SPEECH_TO_TEXT,
                    AgentCapability.TEXT_TO_SPEECH,
                    AgentCapability.IMAGE_GENERATION,
                    AgentCapability.DOCUMENT_ANALYSIS,
                    AgentCapability.OCR
                ])
            
            elif self.configuration.provider == ProviderType.ANTHROPIC:
                capabilities.extend([
                    AgentCapability.VISION,
                    AgentCapability.DOCUMENT_ANALYSIS,
                    AgentCapability.OCR
                ])
            
            elif self.configuration.provider == ProviderType.GEMINI:
                capabilities.extend([
                    AgentCapability.VISION,
                    AgentCapability.VIDEO_UNDERSTANDING,
                    AgentCapability.AUDIO_PROCESSING,
                    AgentCapability.DOCUMENT_ANALYSIS
                ])
            
            elif self.configuration.provider == ProviderType.COHERE:
                capabilities.extend([
                    AgentCapability.DOCUMENT_ANALYSIS,
                    AgentCapability.CONTENT_TRANSFORMATION
                ])
        
        # Enhanced memory capabilities
        if self.configuration.memory_enabled:
            capabilities.extend([
                AgentCapability.PERSISTENT_MEMORY,
                AgentCapability.CONTEXT_COMPRESSION,
                AgentCapability.MEMORY_RETRIEVAL,
                AgentCapability.PERSONALIZATION,
                AgentCapability.MEMORY_ANALYTICS
            ])
        
        return capabilities
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        """Get all capabilities including enhanced ones"""
        base_capabilities = super().capabilities
        return list(set(base_capabilities + self._enhanced_capabilities))
    
    @property
    def multimodal_processor(self) -> Optional[IMultimodalProcessor]:
        """Get the multimodal processor"""
        if self._multimodal_processor is None and hasattr(self.provider, 'get_multimodal_processor'):
            self._multimodal_processor = self.provider.get_multimodal_processor(self.configuration)
        return self._multimodal_processor
    
    # Multimodal capabilities implementation
    async def chat_multimodal(
        self,
        message: str,
        attachments: Optional[List[MultimodalContent]] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> IAgentResponse:
        """Send a multimodal chat message with attachments"""
        try:
            # Get or create session
            session = await self._get_or_create_session(session_id)
            
            # Create agent message with multimodal content
            agent_message = AgentMessage(
                role="user",
                content=message,
                multimodal_content=attachments or []
            )
            
            # Add to session
            await session.add_message(agent_message)
            
            # Process multimodal content if present
            if attachments and self.multimodal_processor:
                multimodal_request = MultimodalRequest(
                    content=attachments,
                    processing_mode=ProcessingMode.ANALYZE,
                    instructions=message,
                    cross_modal_context=True
                )
                
                multimodal_response = await self.multimodal_processor.process_content(multimodal_request)
                
                # Add multimodal analysis to message
                agent_message.multimodal_analysis = multimodal_response.content_analysis
                agent_message.extracted_content = multimodal_response.extracted_content
            
            # Get response from provider
            response = await self.provider.send_message(agent_message, session, self.configuration)
            
            # Add response to session
            if response.success:
                await session.add_message(response.message)
            
            return response
            
        except Exception as e:
            logger.error(f"Multimodal chat failed: {e}")
            return AgentResponse(
                content=f"Failed to process multimodal message: {str(e)}",
                success=False,
                error=e
            )
    
    async def process_multimodal(
        self,
        request: MultimodalRequest,
        session_id: Optional[str] = None
    ) -> MultimodalResponse:
        """Process multimodal content directly"""
        if not self.multimodal_processor:
            return MultimodalResponse(
                success=False,
                error="Multimodal processing not available for this provider"
            )
        
        try:
            return await self.multimodal_processor.process_content(request)
        except Exception as e:
            logger.error(f"Multimodal processing failed: {e}")
            return MultimodalResponse(
                success=False,
                error=str(e)
            )
    
    async def describe_image(
        self,
        image: Any,
        prompt: str = "Describe this image in detail",
        session_id: Optional[str] = None
    ) -> str:
        """Describe an image"""
        try:
            # Create image content
            if not isinstance(image, MultimodalContent):
                image_content = create_image_content(image, instructions=prompt)
            else:
                image_content = image
            
            # Use multimodal processor if available
            if self.multimodal_processor:
                analysis = await self.multimodal_processor.analyze_image(image_content, prompt)
                return analysis.get("description", analysis.get("analysis", "Unable to analyze image"))
            
            # Fallback to chat with image
            response = await self.chat_multimodal(prompt, [image_content], session_id)
            return response.content
            
        except Exception as e:
            logger.error(f"Image description failed: {e}")
            return f"Failed to describe image: {str(e)}"
    
    async def analyze_document(
        self,
        document: Any,
        questions: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze a document and answer questions"""
        try:
            # Create document content
            if not isinstance(document, MultimodalContent):
                doc_content = create_document_content(document)
            else:
                doc_content = document
            
            # Use multimodal processor if available
            if self.multimodal_processor:
                analysis = await self.multimodal_processor.analyze_document(doc_content)
                
                # Answer specific questions if provided
                if questions:
                    question_answers = {}
                    for question in questions:
                        reasoning_result = await self.multimodal_processor.cross_modal_reasoning(
                            [doc_content], question
                        )
                        question_answers[question] = reasoning_result.get("answer", "Unable to answer")
                    
                    analysis["question_answers"] = question_answers
                
                return analysis
            
            # Fallback to chat-based analysis
            analysis_prompt = "Analyze this document comprehensively."
            if questions:
                analysis_prompt += f" Please answer these specific questions: {', '.join(questions)}"
            
            response = await self.chat_multimodal(analysis_prompt, [doc_content], session_id)
            
            return {
                "analysis": response.content,
                "method": "chat_based",
                "success": response.success
            }
            
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            return {"error": str(e), "success": False}
    
    async def transcribe_audio(
        self,
        audio: Any,
        language: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Transcribe audio to text"""
        try:
            # Create audio content
            if not isinstance(audio, MultimodalContent):
                audio_content = create_audio_content(audio)
            else:
                audio_content = audio
            
            # Use multimodal processor if available
            if self.multimodal_processor:
                analysis = await self.multimodal_processor.analyze_audio(audio_content)
                return analysis.get("transcription", "Unable to transcribe audio")
            
            # Fallback to chat-based transcription
            response = await self.chat_multimodal("Transcribe this audio", [audio_content], session_id)
            return response.content
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return f"Failed to transcribe audio: {str(e)}"
    
    async def understand_video(
        self,
        video: Any,
        questions: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze video content and answer questions"""
        try:
            # Create video content
            if not isinstance(video, MultimodalContent):
                video_content = create_video_content(video)
            else:
                video_content = video
            
            # Use multimodal processor if available
            if self.multimodal_processor:
                analysis = await self.multimodal_processor.analyze_video(video_content)
                
                # Answer specific questions if provided
                if questions:
                    question_answers = {}
                    for question in questions:
                        reasoning_result = await self.multimodal_processor.cross_modal_reasoning(
                            [video_content], question
                        )
                        question_answers[question] = reasoning_result.get("answer", "Unable to answer")
                    
                    analysis["question_answers"] = question_answers
                
                return analysis
            
            # Fallback to chat-based analysis
            analysis_prompt = "Analyze this video content."
            if questions:
                analysis_prompt += f" Please answer these questions: {', '.join(questions)}"
            
            response = await self.chat_multimodal(analysis_prompt, [video_content], session_id)
            
            return {
                "analysis": response.content,
                "method": "chat_based",
                "success": response.success
            }
            
        except Exception as e:
            logger.error(f"Video understanding failed: {e}")
            return {"error": str(e), "success": False}
    
    async def compare_content(
        self,
        content1: MultimodalContent,
        content2: MultimodalContent,
        comparison_aspects: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare two pieces of multimodal content"""
        try:
            # Build comparison prompt
            prompt = "Compare these two pieces of content"
            if comparison_aspects:
                prompt += f" focusing on: {', '.join(comparison_aspects)}"
            
            # Use cross-modal reasoning if available
            if self.multimodal_processor:
                return await self.multimodal_processor.cross_modal_reasoning(
                    [content1, content2], prompt
                )
            
            # Fallback to chat-based comparison
            response = await self.chat_multimodal(prompt, [content1, content2], session_id)
            
            return {
                "comparison": response.content,
                "method": "chat_based",
                "success": response.success
            }
            
        except Exception as e:
            logger.error(f"Content comparison failed: {e}")
            return {"error": str(e), "success": False}
    
    async def search_in_content(
        self,
        content: MultimodalContent,
        query: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for specific information within content"""
        try:
            search_prompt = f"Search for the following information in this content: {query}"
            
            # Use cross-modal reasoning if available
            if self.multimodal_processor:
                return await self.multimodal_processor.cross_modal_reasoning([content], search_prompt)
            
            # Fallback to chat-based search
            response = await self.chat_multimodal(search_prompt, [content], session_id)
            
            return {
                "search_results": response.content,
                "query": query,
                "method": "chat_based",
                "success": response.success
            }
            
        except Exception as e:
            logger.error(f"Content search failed: {e}")
            return {"error": str(e), "success": False}
    
    async def cross_modal_reasoning(
        self,
        contents: List[MultimodalContent],
        question: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform cross-modal reasoning across multiple content types"""
        try:
            # Use multimodal processor if available
            if self.multimodal_processor:
                return await self.multimodal_processor.cross_modal_reasoning(contents, question)
            
            # Fallback to chat-based reasoning
            response = await self.chat_multimodal(question, contents, session_id)
            
            return {
                "reasoning_result": response.content,
                "question": question,
                "content_types": [content.modality.value for content in contents],
                "method": "chat_based",
                "success": response.success
            }
            
        except Exception as e:
            logger.error(f"Cross-modal reasoning failed: {e}")
            return {"error": str(e), "success": False}
    
    # Enhanced Memory & Context Management (implementing the new interface methods)
    async def store_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        importance_score: float = 0.5,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store information in persistent memory"""
        try:
            # This would integrate with the V2 memory system
            # For now, implement basic storage in session metadata
            if not hasattr(self, '_persistent_memories'):
                self._persistent_memories = []
            
            memory_entry = {
                "content": content,
                "memory_type": memory_type,
                "importance_score": importance_score,
                "timestamp": datetime.now(),
                "session_id": session_id,
                "metadata": metadata or {}
            }
            
            self._persistent_memories.append(memory_entry)
            logger.info(f"Stored memory: {memory_type} - {content[:100]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False
    
    async def retrieve_memories(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on query"""
        try:
            if not hasattr(self, '_persistent_memories'):
                return []
            
            # Simple text-based matching for now
            # In production, this would use semantic search
            relevant_memories = []
            
            for memory in self._persistent_memories:
                if memory_types and memory["memory_type"] not in memory_types:
                    continue
                
                # Simple keyword matching
                if any(word.lower() in memory["content"].lower() for word in query.split()):
                    relevant_memories.append(memory)
            
            # Sort by importance score and recency
            relevant_memories.sort(
                key=lambda x: (x["importance_score"], x["timestamp"]),
                reverse=True
            )
            
            return relevant_memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    async def get_personalized_context(
        self,
        base_context: List[AgentMessage],
        user_id: str,
        session_id: Optional[str] = None
    ) -> List[AgentMessage]:
        """Get personalized conversation context for user"""
        try:
            # Retrieve user-specific memories
            user_memories = await self.retrieve_memories(
                f"user:{user_id}",
                memory_types=["preference", "behavior", "context"],
                limit=5
            )
            
            # Create personalized context by adding relevant memories
            personalized_context = base_context.copy()
            
            if user_memories:
                memory_summary = "User context: " + "; ".join([
                    memory["content"] for memory in user_memories
                ])
                
                system_message = AgentMessage(
                    role="system",
                    content=memory_summary,
                    metadata={"type": "personalization", "user_id": user_id}
                )
                
                # Insert at the beginning after any existing system messages
                system_messages = [msg for msg in personalized_context if msg.role == "system"]
                other_messages = [msg for msg in personalized_context if msg.role != "system"]
                
                personalized_context = system_messages + [system_message] + other_messages
            
            return personalized_context
            
        except Exception as e:
            logger.error(f"Failed to get personalized context: {e}")
            return base_context
    
    async def compress_context(
        self,
        session_id: str,
        target_token_count: int,
        strategy: str = "summarization"
    ) -> Dict[str, Any]:
        """Compress conversation context to fit token limits"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            messages = session.messages
            if not messages:
                return {"compressed_context": [], "compression_ratio": 0}
            
            # Simple summarization strategy
            if strategy == "summarization":
                # Keep first and last few messages, summarize the middle
                keep_start = 3
                keep_end = 3
                
                if len(messages) <= keep_start + keep_end:
                    return {"compressed_context": messages, "compression_ratio": 1.0}
                
                start_messages = messages[:keep_start]
                end_messages = messages[-keep_end:]
                middle_messages = messages[keep_start:-keep_end]
                
                # Create summary of middle messages
                middle_content = "\n".join([
                    f"{msg.role}: {msg.content}" for msg in middle_messages
                ])
                
                summary_prompt = f"Summarize this conversation in 2-3 sentences:\n{middle_content}"
                summary_response = await self.chat(summary_prompt)
                
                summary_message = AgentMessage(
                    role="system",
                    content=f"Summary of previous conversation: {summary_response.content}",
                    metadata={"type": "context_compression", "original_messages": len(middle_messages)}
                )
                
                compressed_context = start_messages + [summary_message] + end_messages
                compression_ratio = len(compressed_context) / len(messages)
                
                return {
                    "compressed_context": compressed_context,
                    "compression_ratio": compression_ratio,
                    "original_length": len(messages),
                    "compressed_length": len(compressed_context),
                    "strategy": strategy
                }
            
            else:
                return {"error": f"Unknown compression strategy: {strategy}"}
            
        except Exception as e:
            logger.error(f"Context compression failed: {e}")
            return {"error": str(e)}
    
    async def get_memory_analytics(
        self,
        user_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """Get memory usage analytics and insights"""
        try:
            if not hasattr(self, '_persistent_memories'):
                return {"total_memories": 0, "memory_types": {}, "insights": []}
            
            memories = self._persistent_memories
            
            # Filter by user_id if provided
            if user_id:
                memories = [m for m in memories if m.get("metadata", {}).get("user_id") == user_id]
            
            # Filter by time range if provided
            if time_range:
                start_time, end_time = time_range
                memories = [m for m in memories if start_time <= m["timestamp"] <= end_time]
            
            # Calculate analytics
            total_memories = len(memories)
            memory_types = {}
            importance_scores = []
            
            for memory in memories:
                memory_type = memory["memory_type"]
                memory_types[memory_type] = memory_types.get(memory_type, 0) + 1
                importance_scores.append(memory["importance_score"])
            
            avg_importance = sum(importance_scores) / len(importance_scores) if importance_scores else 0
            
            # Generate insights
            insights = []
            if total_memories > 100:
                insights.append("High memory usage detected. Consider memory cleanup.")
            
            most_common_type = max(memory_types.items(), key=lambda x: x[1])[0] if memory_types else None
            if most_common_type:
                insights.append(f"Most common memory type: {most_common_type}")
            
            return {
                "total_memories": total_memories,
                "memory_types": memory_types,
                "average_importance": avg_importance,
                "insights": insights,
                "time_range": time_range,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Memory analytics failed: {e}")
            return {"error": str(e)}
    
    async def update_personalization(
        self,
        user_id: str,
        interaction_data: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update user personalization based on interaction"""
        try:
            # Extract personalization insights from interaction
            personalization_content = f"User {user_id} interaction patterns: {interaction_data}"
            
            # Store as personalization memory
            success = await self.store_memory(
                content=personalization_content,
                memory_type="personalization",
                importance_score=0.7,
                session_id=session_id,
                metadata={
                    "user_id": user_id,
                    "interaction_type": interaction_data.get("type", "general"),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "success": success,
                "user_id": user_id,
                "updated_aspects": list(interaction_data.keys()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Personalization update failed: {e}")
            return {"error": str(e), "success": False}
    
    async def predict_user_intent(
        self,
        user_message: str,
        context: List[AgentMessage],
        user_id: str
    ) -> Dict[str, float]:
        """Predict user intent from message and context"""
        try:
            # Build intent prediction prompt
            context_text = "\n".join([f"{msg.role}: {msg.content}" for msg in context[-5:]])
            
            intent_prompt = f"""
            Analyze the user's intent based on their message and conversation context.
            
            User ID: {user_id}
            Current Message: {user_message}
            
            Recent Context:
            {context_text}
            
            Predict the user's intent and provide confidence scores (0-1) for these categories:
            - information_seeking
            - task_completion
            - creative_assistance
            - problem_solving
            - casual_conversation
            - technical_support
            
            Respond in JSON format with intent names and confidence scores.
            """
            
            response = await self.chat(intent_prompt)
            
            # Try to parse JSON response
            try:
                import json
                intent_scores = json.loads(response.content)
                return intent_scores
            except json.JSONDecodeError:
                # Fallback to simple analysis
                return {
                    "information_seeking": 0.5,
                    "general_assistance": 0.5
                }
            
        except Exception as e:
            logger.error(f"Intent prediction failed: {e}")
            return {"unknown": 1.0}


class MultimodalAgentFactory:
    """Factory for creating multimodal agents"""
    
    @staticmethod
    def create_multimodal_agent(
        provider_type: ProviderType,
        model: str,
        api_key: str,
        **kwargs
    ) -> MultimodalAgent:
        """Create a multimodal agent with the specified provider"""
        from .providers.openai_multimodal import OpenAIMultimodalProvider
        from .providers.anthropic import AnthropicProvider
        from .providers.gemini import GeminiProvider
        from .providers.cohere import CohereProvider
        from .base import AgentConfiguration
        
        # Create configuration
        config = AgentConfiguration(
            provider=provider_type,
            model=model,
            api_key=api_key,
            memory_enabled=True,
            tools_enabled=True,
            **kwargs
        )
        
        # Create provider
        if provider_type == ProviderType.OPENAI:
            provider = OpenAIMultimodalProvider()
        elif provider_type == ProviderType.ANTHROPIC:
            provider = AnthropicProvider()
        elif provider_type == ProviderType.GEMINI:
            provider = GeminiProvider()
        elif provider_type == ProviderType.COHERE:
            provider = CohereProvider()
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        # Create and return multimodal agent
        return MultimodalAgent(config, provider)
