#!/usr/bin/env python3
"""
MemoryPro Feature Demonstration
===============================

This script demonstrates all MemoryPro Pro features including:
- Dual-mode memory management (internal vs external)
- AI-powered memory analysis and insights
- Action discovery from memory content
- Real-time webhook notifications
- Memory lifecycle management
- Pattern analysis and evolution tracking

Usage:
    python demo_memorypro.py

Environment Variables:
    MEMORYPRO_ENABLED=true          # Enable external MemoryPro
    MEMORYPRO_API_URL=              # MemoryPro API URL
    MEMORYPRO_API_KEY=              # API key (lsp_xxx format)
    MEMORYPRO_API_SECRET=           # API secret
    MEMORYPRO_WEBHOOK_URL=          # Webhook URL
    MEMORYPRO_WEBHOOK_SECRET=       # Webhook secret
"""

import os
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import MemoryPro components
from langswarm.memory.adapters.memorypro import MemoryProAdapter, create_memorypro_adapter
from langswarm.core.actions.action_discovery import discover_actions_from_content
from langswarm.core.actions.action_queue import ActionQueue, get_action_queue
from langswarm.core.webhooks.memorypro_webhooks import MemoryProWebhookHandler
from langswarm.core.config import MemoryConfig


class MemoryProDemo:
    """Comprehensive MemoryPro demonstration class"""
    
    def __init__(self):
        """Initialize the demo"""
        self.setup_demo_environment()
        self.adapter = self.create_adapter()
        self.action_queue = get_action_queue()
        self.webhook_handler = MemoryProWebhookHandler(
            webhook_secret=os.getenv("MEMORYPRO_WEBHOOK_SECRET", "demo_secret")
        )
        
        print("🚀 MemoryPro Demo Initialized")
        print(f"   Mode: {self.adapter.mode}")
        print(f"   External configured: {self.adapter._is_external_configured()}")
        print()
    
    def setup_demo_environment(self):
        """Setup demo environment variables"""
        # Set demo environment variables if not already set
        demo_vars = {
            "MEMORYPRO_ENABLED": "true",
            "MEMORYPRO_MODE": "internal",  # Use internal for demo
            "MEMORYPRO_WEBHOOK_SECRET": "demo_secret_123",
            "LANGSWARM_ACTIONS_DB": "demo_actions.db"
        }
        
        for key, value in demo_vars.items():
            if not os.getenv(key):
                os.environ[key] = value
    
    def create_adapter(self) -> MemoryProAdapter:
        """Create MemoryPro adapter based on configuration"""
        # Check if external mode is configured
        external_configured = all([
            os.getenv("MEMORYPRO_API_URL"),
            os.getenv("MEMORYPRO_API_KEY"),
            os.getenv("MEMORYPRO_API_SECRET")
        ])
        
        if external_configured and os.getenv("MEMORYPRO_ENABLED", "").lower() == "true":
            print("🌐 Using external MemoryPro mode")
            mode = "external"
        else:
            print("🏠 Using internal MemoryPro mode")
            mode = "internal"
        
        return create_memorypro_adapter(mode=mode)
    
    def demo_memory_configuration(self):
        """Demonstrate MemoryPro configuration options"""
        print("📋 MemoryPro Configuration Demo")
        print("=" * 50)
        
        # Internal mode configuration
        internal_config = MemoryConfig(
            enabled=True,
            memorypro_enabled=True,
            memorypro_mode="internal"
        )
        
        print("Internal Mode Configuration:")
        print(f"   External mode: {internal_config.is_external_memorypro()}")
        print(f"   Config: {internal_config.get_memorypro_config()}")
        print()
        
        # External mode configuration
        external_config = MemoryConfig(
            enabled=True,
            memorypro_enabled=True,
            memorypro_mode="external",
            memorypro_api_url="https://api.memorypro.com",
            memorypro_api_key="lsp_demo_key",
            memorypro_api_secret="demo_secret"
        )
        
        print("External Mode Configuration:")
        print(f"   External mode: {external_config.is_external_memorypro()}")
        print(f"   Config: {external_config.get_memorypro_config()}")
        print()
    
    def demo_memory_storage_and_analysis(self):
        """Demonstrate memory storage with AI analysis"""
        print("🧠 Memory Storage & Analysis Demo")
        print("=" * 50)
        
        # Test conversations with different complexity levels
        test_conversations = [
            {
                "content": "We need to schedule a meeting with the client by Friday to discuss the new project requirements. This is urgent!",
                "user_id": "demo_user_1",
                "session_id": "session_1"
            },
            {
                "content": "I was thinking we should eventually look into optimizing the database queries for better performance.",
                "user_id": "demo_user_1", 
                "session_id": "session_1"
            },
            {
                "content": "The team decided to implement the new authentication system. We must finish this by the end of the week.",
                "user_id": "demo_user_2",
                "session_id": "session_2"
            },
            {
                "content": "Had a great conversation about machine learning applications. Very interesting insights shared.",
                "user_id": "demo_user_1",
                "session_id": "session_1"
            }
        ]
        
        stored_memories = []
        
        for i, conv in enumerate(test_conversations):
            print(f"Storing memory {i+1}: {conv['content'][:50]}...")
            
            document = {
                "text": conv["content"],
                "metadata": {
                    "user_id": conv["user_id"],
                    "session_id": conv["session_id"],
                    "timestamp": datetime.utcnow().isoformat()
                },
                "key": f"demo_memory_{i+1}"
            }
            
            result = self.adapter.add_documents([document])
            
            if result["results"] and result["results"][0]["status"] == "success":
                analysis = result["results"][0]["analysis"]
                
                print(f"   ✅ Stored successfully")
                print(f"   📊 Priority Score: {analysis.priority_score:.2f}")
                print(f"   🎯 Relevance Score: {analysis.relevance_score:.2f}")
                print(f"   🏷️  Themes: {', '.join(analysis.themes)}")
                print(f"   🎬 Actions: {len(analysis.extracted_actions)}")
                
                stored_memories.append({
                    "memory_id": result["results"][0]["memory_id"],
                    "content": conv["content"],
                    "analysis": analysis
                })
            else:
                print(f"   ❌ Storage failed")
            
            print()
        
        return stored_memories
    
    def demo_memory_recall(self):
        """Demonstrate enhanced memory recall"""
        print("🔍 Memory Recall Demo")
        print("=" * 50)
        
        # Test different query types
        test_queries = [
            "project requirements",
            "urgent tasks",
            "database optimization",
            "machine learning",
            "authentication system"
        ]
        
        for query in test_queries:
            print(f"Searching for: '{query}'")
            
            result = self.adapter.query(
                query=query,
                n=3,
                user_id="demo_user_1",
                weight_recent=True,
                include_analysis=True
            )
            
            if result.get("status") == "success":
                memories = result.get("memories", [])
                analysis = result.get("analysis", {})
                
                print(f"   📊 Found {len(memories)} memories")
                print(f"   🔍 Searched {analysis.get('total_memories_searched', 0)} total")
                
                for i, memory in enumerate(memories[:2]):  # Show top 2
                    print(f"   {i+1}. {memory.get('content', '')[:60]}...")
                    print(f"      Relevance: {memory.get('relevance_score', 0):.2f}")
                
                # Show discovered actions
                discovered_actions = result.get("discovered_actions", [])
                if discovered_actions:
                    print(f"   🎬 Discovered {len(discovered_actions)} actions:")
                    for action in discovered_actions[:2]:
                        print(f"      - {action.get('type', 'unknown')}: {action.get('title', 'Untitled')}")
            else:
                print(f"   ❌ Query failed")
            
            print()
    
    def demo_action_discovery(self):
        """Demonstrate action discovery from memory content"""
        print("🎯 Action Discovery Demo")
        print("=" * 50)
        
        # Test different types of action-rich content
        test_contents = [
            "We need to schedule a meeting with the marketing team by Thursday to review the campaign.",
            "I should remember to follow up with the client about their feedback on the proposal.",
            "We must decide on the database architecture before the sprint planning session.",
            "Let's research the best practices for API security implementation.",
            "Don't forget to review the code changes before the release deadline.",
            "We should eventually optimize the search functionality for better user experience."
        ]
        
        all_discovered_actions = []
        
        for i, content in enumerate(test_contents):
            print(f"Analyzing content {i+1}: {content[:50]}...")
            
            actions = discover_actions_from_content(
                content=content,
                user_id="demo_user",
                memory_id=f"demo_memory_{i+1}",
                context={"source": "demo", "index": i+1}
            )
            
            print(f"   🎬 Discovered {len(actions)} actions:")
            
            for action in actions:
                print(f"      - {action.type.upper()}: {action.title}")
                print(f"        Priority: {action.priority.value}")
                if action.due_date:
                    print(f"        Due: {action.due_date.strftime('%Y-%m-%d %H:%M')}")
                
                # Add to queue
                self.action_queue.add_action(action)
                all_discovered_actions.append(action)
            
            print()
        
        return all_discovered_actions
    
    def demo_action_queue_management(self):
        """Demonstrate action queue management"""
        print("📋 Action Queue Management Demo")
        print("=" * 50)
        
        # Get pending actions
        pending_actions = self.action_queue.get_pending_actions("demo_user")
        print(f"📌 Pending actions: {len(pending_actions)}")
        
        for i, action in enumerate(pending_actions[:5]):  # Show top 5
            print(f"   {i+1}. [{action.type.upper()}] {action.title}")
            print(f"      Priority: {action.priority.value} | Created: {action.created_at.strftime('%H:%M:%S')}")
        
        print()
        
        # Demonstrate filtering
        from langswarm.core.actions.action_queue import ActionPriority
        
        high_priority_actions = self.action_queue.get_actions(
            priority=ActionPriority.HIGH,
            user_id="demo_user"
        )
        print(f"🔥 High priority actions: {len(high_priority_actions)}")
        
        # Demonstrate status updates
        if pending_actions:
            action_to_complete = pending_actions[0]
            print(f"✅ Completing action: {action_to_complete.title}")
            
            from langswarm.core.actions.action_queue import ActionStatus
            success = self.action_queue.update_action_status(
                action_to_complete.id,
                ActionStatus.COMPLETED
            )
            print(f"   Status update: {'✅ Success' if success else '❌ Failed'}")
        
        print()
    
    def demo_memory_insights(self):
        """Demonstrate memory insights and analytics"""
        print("📊 Memory Insights Demo")
        print("=" * 50)
        
        insights = self.adapter.get_insights("demo_user")
        
        print(f"🧠 Memory Health Score: {insights.memory_health_score:.2f}")
        print(f"📝 Total Memories: {insights.total_memories}")
        print(f"⭐ High Priority Count: {insights.high_priority_count}")
        print()
        
        print("🔍 Discovered Patterns:")
        for pattern in insights.patterns:
            print(f"   - {pattern.get('pattern_type', 'Unknown')}: {pattern.get('description', 'No description')}")
            print(f"     Frequency: {pattern.get('frequency', 0)} | Trend: {pattern.get('trend', 'unknown')}")
        
        print()
        
        if insights.lifecycle_recommendations:
            print("🔄 Lifecycle Recommendations:")
            for rec in insights.lifecycle_recommendations:
                action = rec.get("action", "unknown")
                reason = rec.get("reason", "No reason provided")
                memory_count = len(rec.get("memory_ids", []))
                print(f"   - {action.upper()}: {memory_count} memories - {reason}")
        
        print()
        
        if insights.evolution_updates:
            print("🧬 Evolution Updates:")
            for update in insights.evolution_updates:
                insight = update.get("insight", "No insight")
                confidence = update.get("confidence", 0.0)
                recommendation = update.get("recommendation", "No recommendation")
                print(f"   - {insight} (confidence: {confidence:.2f})")
                print(f"     Recommendation: {recommendation}")
        
        print()
    
    async def demo_webhook_integration(self):
        """Demonstrate webhook integration"""
        print("🪝 Webhook Integration Demo")
        print("=" * 50)
        
        # Simulate different webhook events
        webhook_events = [
            {
                "event_type": "memory_insights",
                "user_id": "demo_user",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "insights": {
                        "memory_health_score": 0.87,
                        "new_patterns": [
                            {"description": "Increased focus on project deadlines", "frequency": 8}
                        ]
                    }
                }
            },
            {
                "event_type": "action_discoveries",
                "user_id": "demo_user",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "actions": [
                        {
                            "type": "reminder",
                            "title": "Check project status",
                            "priority": "medium"
                        }
                    ]
                }
            },
            {
                "event_type": "lifecycle_recommendations",
                "user_id": "demo_user",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "recommendations": [
                        {
                            "action": "archive",
                            "memory_ids": ["mem_1", "mem_2"],
                            "reason": "Old conversations, low relevance"
                        }
                    ]
                }
            }
        ]
        
        for event in webhook_events:
            print(f"Processing webhook: {event['event_type']}")
            
            payload = json.dumps(event).encode()
            result = await self.webhook_handler.handle_webhook(payload, "")
            
            print(f"   Status: {'✅ Success' if result.get('status') == 'success' else '❌ Failed'}")
            
            # Show queued actions after webhook processing
            webhook_actions = self.webhook_handler.get_pending_actions("demo_user")
            if webhook_actions:
                print(f"   🎬 Queued {len(webhook_actions)} actions from webhook")
        
        print()
    
    def demo_pattern_analysis(self):
        """Demonstrate pattern analysis capabilities"""
        print("🔬 Pattern Analysis Demo")
        print("=" * 50)
        
        from langswarm.core.actions.action_discovery import get_action_discovery_engine
        
        engine = get_action_discovery_engine()
        
        # Analyze different content types
        test_contents = [
            "We need to fix the critical bug in production immediately!",
            "I was thinking about improving the user interface design eventually.",
            "Let's schedule weekly team meetings to track project progress.",
            "We should research machine learning applications for our platform."
        ]
        
        for i, content in enumerate(test_contents):
            print(f"Content {i+1}: {content[:50]}...")
            
            analysis = engine.analyze_content_patterns(content)
            
            print(f"   Action Indicators: {analysis['action_indicators']}")
            print(f"   Priority Indicators: {analysis['priority_indicators']}")
            print(f"   Time Indicators: {analysis['time_indicators']}")
            print(f"   Sentiment: {analysis['sentiment']}")
            print(f"   Complexity: {analysis['complexity']}")
            print(f"   Confidence: {analysis['confidence']:.2f}")
            print()
    
    def demo_integration_workflow(self):
        """Demonstrate complete integration workflow"""
        print("🔄 Complete Integration Workflow Demo")
        print("=" * 50)
        
        # Complete workflow: Memory → Analysis → Actions → Queue → Insights
        workflow_content = """
        Project meeting notes:
        - We need to finalize the API design by Wednesday
        - The team should review security requirements urgently  
        - Schedule follow-up with stakeholders next week
        - Research competitor features for benchmarking
        - Don't forget to update project documentation
        """
        
        print("1. Storing memory with rich content...")
        
        # Step 1: Store memory
        document = {
            "text": workflow_content,
            "metadata": {
                "user_id": "workflow_demo_user",
                "session_id": "workflow_session",
                "meeting_type": "project_planning"
            },
            "key": "workflow_demo_memory"
        }
        
        memory_result = self.adapter.add_documents([document])
        print(f"   ✅ Memory stored with analysis")
        
        # Step 2: Discover actions
        print("2. Discovering actions from content...")
        actions = discover_actions_from_content(
            content=workflow_content,
            user_id="workflow_demo_user",
            memory_id="workflow_demo_memory"
        )
        print(f"   🎬 Discovered {len(actions)} actions")
        
        # Step 3: Queue actions
        print("3. Adding actions to queue...")
        for action in actions:
            self.action_queue.add_action(action)
        print(f"   📋 Queued {len(actions)} actions")
        
        # Step 4: Generate insights
        print("4. Generating insights...")
        insights = self.adapter.get_insights("workflow_demo_user")
        print(f"   📊 Health score: {insights.memory_health_score:.2f}")
        
        # Step 5: Show final state
        print("5. Final workflow state:")
        pending_actions = self.action_queue.get_pending_actions("workflow_demo_user")
        print(f"   📌 Total pending actions: {len(pending_actions)}")
        
        for action in pending_actions[-3:]:  # Show last 3 actions
            print(f"      - {action.title} ({action.priority.value})")
        
        print()
    
    def cleanup_demo(self):
        """Clean up demo data"""
        print("🧹 Cleaning up demo data...")
        
        # Clear completed actions older than 0 days (all completed actions)
        cleared_count = self.action_queue.clear_completed_actions(days_old=0)
        print(f"   🗑️  Cleared {cleared_count} completed actions")
        
        print("   ✅ Demo cleanup complete")
    
    async def run_full_demo(self):
        """Run the complete MemoryPro demonstration"""
        print("🌟 MemoryPro Pro Features - Complete Demonstration")
        print("=" * 80)
        print()
        
        # Run all demo sections
        self.demo_memory_configuration()
        self.demo_memory_storage_and_analysis()
        self.demo_memory_recall()
        self.demo_action_discovery()
        self.demo_action_queue_management()
        self.demo_memory_insights()
        await self.demo_webhook_integration()
        self.demo_pattern_analysis()
        self.demo_integration_workflow()
        
        print("🎉 Demo completed successfully!")
        print()
        print("Next steps:")
        print("1. Set environment variables for external MemoryPro mode")
        print("2. Configure webhooks for real-time notifications")
        print("3. Integrate with your application's action queue system")
        print("4. Monitor memory insights for optimization opportunities")
        print()
        
        self.cleanup_demo()


async def main():
    """Main demo function"""
    try:
        demo = MemoryProDemo()
        await demo.run_full_demo()
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting MemoryPro Pro Features Demo...")
    print("   This demo showcases all MemoryPro capabilities")
    print("   Press Ctrl+C to stop at any time")
    print()
    
    # Run the demo
    asyncio.run(main()) 