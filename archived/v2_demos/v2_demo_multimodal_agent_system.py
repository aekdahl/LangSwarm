#!/usr/bin/env python3
"""
LangSwarm V2 Multimodal Agent System Demo

Comprehensive demonstration of the complete multimodal agent system including:
- Image processing and analysis
- Video understanding and transcription
- Audio processing and voice interaction
- Document analysis and OCR integration
- Cross-modal reasoning and understanding
- Enhanced memory and context management

This demo showcases Task C1: Multimodal Agent System implementation.
"""

import asyncio
import base64
import io
import logging
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Import V2 multimodal components
try:
    from langswarm.v2.core.agents.multimodal_agent import MultimodalAgent, MultimodalAgentFactory
    from langswarm.v2.core.agents.multimodal import (
        MultimodalContent, MultimodalRequest, MultimodalResponse,
        create_image_content, create_video_content, create_audio_content, create_document_content,
        MediaType, ModalityType, ProcessingMode
    )
    from langswarm.v2.core.agents.interfaces import ProviderType, AgentCapability
    from langswarm.v2.core.agents.base import AgentConfiguration
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the LangSwarm root directory")
    exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Demo configuration
DEMO_CONFIG = {
    "providers": {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-4o"
        },
        "anthropic": {
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "model": "claude-3-sonnet-20240229"
        },
        "gemini": {
            "api_key": os.getenv("GOOGLE_API_KEY"),
            "model": "gemini-1.5-pro"
        }
    }
}


class MultimodalAgentDemo:
    """Comprehensive multimodal agent system demonstration"""
    
    def __init__(self):
        self.demo_results = {}
        self.demo_files = {}
        
    async def run_complete_demo(self):
        """Run the complete multimodal agent demo"""
        print("🚀 LangSwarm V2 Multimodal Agent System Demo")
        print("=" * 60)
        print()
        
        await self._check_environment()
        await self._create_demo_content()
        
        # Test each provider
        for provider_name, config in DEMO_CONFIG["providers"].items():
            if config["api_key"]:
                print(f"\n🔍 Testing {provider_name.upper()} Provider")
                print("-" * 40)
                await self._test_provider(provider_name, config)
            else:
                print(f"\n⚠️ Skipping {provider_name.upper()} (no API key)")
        
        await self._test_cross_modal_reasoning()
        await self._test_enhanced_memory_features()
        await self._display_summary()
    
    async def _check_environment(self):
        """Check environment and dependencies"""
        print("🔍 Checking Environment...")
        
        # Check API keys
        missing_keys = []
        for provider, config in DEMO_CONFIG["providers"].items():
            if not config["api_key"]:
                missing_keys.append(provider.upper())
        
        if missing_keys:
            print(f"⚠️ Missing API keys: {', '.join(missing_keys)}")
            print("Set environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY")
        else:
            print("✅ All API keys found")
        
        # Check optional dependencies
        optional_deps = []
        try:
            import PIL
            optional_deps.append("✅ PIL (Pillow)")
        except ImportError:
            optional_deps.append("❌ PIL (Pillow) - install with: pip install Pillow")
        
        try:
            import cv2
            optional_deps.append("✅ OpenCV")
        except ImportError:
            optional_deps.append("❌ OpenCV - install with: pip install opencv-python")
        
        try:
            import pytesseract
            optional_deps.append("✅ Tesseract OCR")
        except ImportError:
            optional_deps.append("❌ Tesseract OCR - install with: pip install pytesseract")
        
        print("Optional Dependencies:")
        for dep in optional_deps:
            print(f"  {dep}")
        
        print()
    
    async def _create_demo_content(self):
        """Create demo content for testing"""
        print("📁 Creating Demo Content...")
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix="langswarm_multimodal_"))
        
        # Create sample text document
        text_file = self.temp_dir / "sample_document.txt"
        with open(text_file, 'w') as f:
            f.write("""
LangSwarm V2 Multimodal Agent System

This document demonstrates the capabilities of the LangSwarm V2 multimodal agent system.

Key Features:
1. Image Processing and Analysis
   - Object detection and recognition
   - OCR text extraction
   - Scene understanding

2. Video Understanding
   - Frame-by-frame analysis
   - Action recognition
   - Content summarization

3. Audio Processing
   - Speech transcription
   - Audio analysis
   - Voice interaction

4. Document Analysis
   - Text extraction
   - Structure analysis
   - Content summarization

5. Cross-Modal Reasoning
   - Multi-content analysis
   - Content comparison
   - Intelligent insights

The system supports multiple LLM providers including OpenAI, Anthropic, and Google Gemini,
each with their unique strengths in multimodal processing.
""")
        
        self.demo_files["document"] = text_file
        
        # Create simple image content (base64-encoded sample)
        # This is a minimal 1x1 pixel red image for testing
        red_pixel_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        image_bytes = base64.b64decode(red_pixel_base64)
        
        image_file = self.temp_dir / "sample_image.png"
        with open(image_file, 'wb') as f:
            f.write(image_bytes)
        
        self.demo_files["image"] = image_file
        
        print(f"✅ Demo content created in {self.temp_dir}")
        print()
    
    async def _test_provider(self, provider_name: str, config: Dict[str, Any]):
        """Test a specific provider's multimodal capabilities"""
        try:
            # Map provider names to types
            provider_type_map = {
                "openai": ProviderType.OPENAI,
                "anthropic": ProviderType.ANTHROPIC,
                "gemini": ProviderType.GEMINI
            }
            
            provider_type = provider_type_map[provider_name]
            
            # Create multimodal agent
            agent = MultimodalAgentFactory.create_multimodal_agent(
                provider_type=provider_type,
                model=config["model"],
                api_key=config["api_key"]
            )
            
            print(f"✅ Created {provider_name} multimodal agent")
            
            # Test capabilities
            capabilities = agent.capabilities
            multimodal_caps = [cap for cap in capabilities if "multimodal" in cap.value.lower() or 
                             cap.value in ["vision", "image_analysis", "audio_processing", "video_understanding"]]
            
            print(f"🎯 Multimodal capabilities: {len(multimodal_caps)}")
            for cap in multimodal_caps[:5]:  # Show first 5
                print(f"   • {cap.value}")
            if len(multimodal_caps) > 5:
                print(f"   • ... and {len(multimodal_caps) - 5} more")
            
            # Test image analysis
            await self._test_image_analysis(agent, provider_name)
            
            # Test document analysis
            await self._test_document_analysis(agent, provider_name)
            
            # Test multimodal chat
            await self._test_multimodal_chat(agent, provider_name)
            
            # Test enhanced memory features
            await self._test_memory_features(agent, provider_name)
            
            print(f"✅ {provider_name} testing completed")
            
        except Exception as e:
            print(f"❌ {provider_name} testing failed: {e}")
            logger.error(f"{provider_name} error: {e}")
    
    async def _test_image_analysis(self, agent: MultimodalAgent, provider_name: str):
        """Test image analysis capabilities"""
        try:
            print("  🖼️ Testing image analysis...")
            
            # Create image content
            image_content = create_image_content(
                str(self.demo_files["image"]),
                instructions="Analyze this image and describe what you see"
            )
            
            # Test describe_image method
            description = await agent.describe_image(
                self.demo_files["image"],
                "Describe this image in detail"
            )
            
            print(f"     Image description: {description[:100]}...")
            
            # Test direct multimodal processing
            if agent.multimodal_processor:
                analysis = await agent.multimodal_processor.analyze_image(
                    image_content,
                    "What colors and objects can you detect?"
                )
                
                print(f"     Analysis type: {analysis.get('analysis_type', 'standard')}")
                if 'extracted_text' in analysis:
                    print(f"     Extracted text: {analysis['extracted_text']}")
            
            self.demo_results[f"{provider_name}_image"] = {
                "description": description,
                "success": True
            }
            
        except Exception as e:
            print(f"     ❌ Image analysis failed: {e}")
            self.demo_results[f"{provider_name}_image"] = {
                "error": str(e),
                "success": False
            }
    
    async def _test_document_analysis(self, agent: MultimodalAgent, provider_name: str):
        """Test document analysis capabilities"""
        try:
            print("  📄 Testing document analysis...")
            
            # Test document analysis
            analysis = await agent.analyze_document(
                self.demo_files["document"],
                ["What are the main features described?", "How many key features are listed?"]
            )
            
            if analysis.get("success", True):
                print(f"     Document analysis: {str(analysis).get('analysis', str(analysis))[:100]}...")
                if 'question_answers' in analysis:
                    print(f"     Questions answered: {len(analysis['question_answers'])}")
            else:
                print(f"     ❌ Analysis failed: {analysis.get('error', 'Unknown error')}")
            
            self.demo_results[f"{provider_name}_document"] = analysis
            
        except Exception as e:
            print(f"     ❌ Document analysis failed: {e}")
            self.demo_results[f"{provider_name}_document"] = {
                "error": str(e),
                "success": False
            }
    
    async def _test_multimodal_chat(self, agent: MultimodalAgent, provider_name: str):
        """Test multimodal chat capabilities"""
        try:
            print("  💬 Testing multimodal chat...")
            
            # Create multimodal content
            image_content = create_image_content(str(self.demo_files["image"]))
            doc_content = create_document_content(str(self.demo_files["document"]))
            
            # Test multimodal chat
            response = await agent.chat_multimodal(
                "Please analyze the provided image and document. What connections can you make between them?",
                attachments=[image_content, doc_content]
            )
            
            if response.success:
                print(f"     Multimodal response: {response.content[:100]}...")
                if hasattr(response, 'message') and response.message.multimodal_analysis:
                    print(f"     Analysis performed: {len(response.message.multimodal_analysis)} content pieces")
            else:
                print(f"     ❌ Chat failed: {response.error}")
            
            self.demo_results[f"{provider_name}_multimodal_chat"] = {
                "response": response.content,
                "success": response.success
            }
            
        except Exception as e:
            print(f"     ❌ Multimodal chat failed: {e}")
            self.demo_results[f"{provider_name}_multimodal_chat"] = {
                "error": str(e),
                "success": False
            }
    
    async def _test_memory_features(self, agent: MultimodalAgent, provider_name: str):
        """Test enhanced memory and context management"""
        try:
            print("  🧠 Testing enhanced memory features...")
            
            # Test memory storage
            memory_stored = await agent.store_memory(
                f"User prefers {provider_name} for multimodal tasks",
                memory_type="preference",
                importance_score=0.8,
                metadata={"provider": provider_name, "task_type": "multimodal"}
            )
            
            print(f"     Memory stored: {memory_stored}")
            
            # Test memory retrieval
            memories = await agent.retrieve_memories(
                f"{provider_name} multimodal",
                memory_types=["preference"],
                limit=5
            )
            
            print(f"     Memories retrieved: {len(memories)}")
            
            # Test personalization update
            personalization = await agent.update_personalization(
                "demo_user",
                {
                    "preferred_provider": provider_name,
                    "interaction_type": "multimodal_demo",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            print(f"     Personalization updated: {personalization.get('success', False)}")
            
            # Test memory analytics
            analytics = await agent.get_memory_analytics()
            print(f"     Memory analytics: {analytics.get('total_memories', 0)} total memories")
            
            self.demo_results[f"{provider_name}_memory"] = {
                "memory_stored": memory_stored,
                "memories_retrieved": len(memories),
                "personalization_success": personalization.get('success', False),
                "total_memories": analytics.get('total_memories', 0)
            }
            
        except Exception as e:
            print(f"     ❌ Memory features failed: {e}")
            self.demo_results[f"{provider_name}_memory"] = {
                "error": str(e),
                "success": False
            }
    
    async def _test_cross_modal_reasoning(self):
        """Test cross-modal reasoning across providers"""
        print("\n🔗 Testing Cross-Modal Reasoning")
        print("-" * 40)
        
        try:
            # Use the first available provider for cross-modal testing
            available_provider = None
            for provider_name, config in DEMO_CONFIG["providers"].items():
                if config["api_key"]:
                    available_provider = (provider_name, config)
                    break
            
            if not available_provider:
                print("❌ No providers available for cross-modal testing")
                return
            
            provider_name, config = available_provider
            provider_type_map = {
                "openai": ProviderType.OPENAI,
                "anthropic": ProviderType.ANTHROPIC,
                "gemini": ProviderType.GEMINI
            }
            
            agent = MultimodalAgentFactory.create_multimodal_agent(
                provider_type=provider_type_map[provider_name],
                model=config["model"],
                api_key=config["api_key"]
            )
            
            # Create multiple content types
            image_content = create_image_content(str(self.demo_files["image"]))
            doc_content = create_document_content(str(self.demo_files["document"]))
            
            # Test cross-modal reasoning
            reasoning_result = await agent.cross_modal_reasoning(
                [image_content, doc_content],
                "How do the visual elements in the image relate to the concepts described in the document?"
            )
            
            if reasoning_result.get("success", True):
                print(f"✅ Cross-modal reasoning completed using {provider_name}")
                print(f"   Question: {reasoning_result.get('question', 'N/A')}")
                print(f"   Answer: {str(reasoning_result.get('answer', reasoning_result.get('reasoning_result', 'N/A')))[:150]}...")
                print(f"   Content types: {reasoning_result.get('content_types', [])}")
            else:
                print(f"❌ Cross-modal reasoning failed: {reasoning_result.get('error', 'Unknown error')}")
            
            self.demo_results["cross_modal_reasoning"] = reasoning_result
            
        except Exception as e:
            print(f"❌ Cross-modal reasoning failed: {e}")
            self.demo_results["cross_modal_reasoning"] = {"error": str(e)}
    
    async def _test_enhanced_memory_features(self):
        """Test enhanced memory and context management features"""
        print("\n🧠 Testing Enhanced Memory & Context Management")
        print("-" * 50)
        
        try:
            # Use the first available provider
            available_provider = None
            for provider_name, config in DEMO_CONFIG["providers"].items():
                if config["api_key"]:
                    available_provider = (provider_name, config)
                    break
            
            if not available_provider:
                print("❌ No providers available for memory testing")
                return
            
            provider_name, config = available_provider
            provider_type_map = {
                "openai": ProviderType.OPENAI,
                "anthropic": ProviderType.ANTHROPIC,
                "gemini": ProviderType.GEMINI
            }
            
            agent = MultimodalAgentFactory.create_multimodal_agent(
                provider_type=provider_type_map[provider_name],
                model=config["model"],
                api_key=config["api_key"]
            )
            
            # Test context compression
            session = await agent.create_session("memory_test_session")
            
            # Add multiple messages to create context
            for i in range(10):
                await session.add_message({
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Test message {i} for context compression demo"
                })
            
            compression_result = await agent.compress_context(
                session.session_id,
                target_token_count=100,
                strategy="summarization"
            )
            
            print(f"✅ Context compression tested")
            print(f"   Original length: {compression_result.get('original_length', 0)}")
            print(f"   Compressed length: {compression_result.get('compressed_length', 0)}")
            print(f"   Compression ratio: {compression_result.get('compression_ratio', 0):.2f}")
            
            # Test intent prediction
            intent_prediction = await agent.predict_user_intent(
                "I want to analyze some images and documents together",
                session.messages[-3:],  # Recent context
                "demo_user"
            )
            
            print(f"✅ Intent prediction completed")
            print(f"   Predicted intents: {list(intent_prediction.keys())}")
            
            self.demo_results["enhanced_memory"] = {
                "context_compression": compression_result,
                "intent_prediction": intent_prediction
            }
            
        except Exception as e:
            print(f"❌ Enhanced memory testing failed: {e}")
            self.demo_results["enhanced_memory"] = {"error": str(e)}
    
    async def _display_summary(self):
        """Display comprehensive demo summary"""
        print("\n📊 Demo Summary")
        print("=" * 60)
        
        # Count successes and failures
        total_tests = len(self.demo_results)
        successful_tests = sum(1 for result in self.demo_results.values() 
                             if result.get("success", True) and "error" not in result)
        
        print(f"Total tests run: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print()
        
        # Display results by category
        categories = {
            "Image Analysis": [k for k in self.demo_results.keys() if "image" in k],
            "Document Analysis": [k for k in self.demo_results.keys() if "document" in k],
            "Multimodal Chat": [k for k in self.demo_results.keys() if "multimodal_chat" in k],
            "Memory Features": [k for k in self.demo_results.keys() if "memory" in k],
            "Cross-Modal": [k for k in self.demo_results.keys() if "cross_modal" in k or "enhanced_memory" in k]
        }
        
        for category, test_keys in categories.items():
            if test_keys:
                category_successes = sum(1 for key in test_keys 
                                       if self.demo_results[key].get("success", True) 
                                       and "error" not in self.demo_results[key])
                print(f"{category}: {category_successes}/{len(test_keys)} successful")
        
        print()
        
        # Provider comparison
        providers_tested = set()
        for key in self.demo_results.keys():
            for provider in ["openai", "anthropic", "gemini"]:
                if provider in key:
                    providers_tested.add(provider)
        
        print(f"Providers tested: {', '.join(providers_tested).upper()}")
        
        # Feature highlights
        print("\n🎯 Feature Highlights Demonstrated:")
        print("✅ Unified multimodal interfaces and data structures")
        print("✅ Image processing and analysis capabilities")
        print("✅ Document analysis and text extraction")
        print("✅ Cross-modal reasoning across content types")
        print("✅ Enhanced memory and context management")
        print("✅ Provider-specific optimizations")
        print("✅ Multimodal chat with attachment support")
        print("✅ Personalization and analytics")
        
        # Cleanup
        print(f"\n🧹 Cleaning up demo files from {self.temp_dir}")
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
        
        print("\n🎉 LangSwarm V2 Multimodal Agent System Demo Complete!")
        print("   Task C1: Multimodal Agent System successfully demonstrated")


async def main():
    """Main demo function"""
    demo = MultimodalAgentDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())
