#!/usr/bin/env python3
"""
BigQuery Session Storage Example
================================

This example demonstrates how to use BigQuery for session storage with the append-only pattern.
"""

import os
from datetime import datetime
from langswarm.core.session.storage import SessionStorageFactory
from langswarm.core.session.models import SessionControl

def main():
    """Example of using BigQuery session storage"""
    
    # Configure BigQuery storage
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
    
    print("🔧 Setting up BigQuery session storage...")
    try:
        # Create BigQuery session storage
        storage = SessionStorageFactory.create_storage(
            storage_type="bigquery",
            project_id=project_id,
            dataset_id="langswarm_sessions",
            table_id="session_events"
        )
        print(f"✅ BigQuery storage created for project: {project_id}")
        
        # Example: Create a session manager with BigQuery storage
        from langswarm.core.session.manager import LangSwarmSessionManager
        
        session_manager = LangSwarmSessionManager(
            storage=storage,
            default_session_control=SessionControl.HYBRID
        )
        
        print("✅ Session manager created with BigQuery storage")
        
        # Create a test session
        session = session_manager.create_session(
            user_id="test_user_123",
            provider="openai",
            model="gpt-4o",
            session_control=SessionControl.HYBRID
        )
        
        print(f"✅ Session created: {session.session_id}")
        
        # Add some messages
        session_manager.add_message(
            session.session_id,
            role="user",
            content="Hello! Can you help me with BigQuery?"
        )
        
        session_manager.add_message(
            session.session_id,
            role="assistant", 
            content="Of course! I'd be happy to help you with BigQuery questions."
        )
        
        print("✅ Messages added to session")
        
        # Update session status
        session_manager.update_session_status(
            session.session_id,
            status="completed"
        )
        
        print("✅ Session status updated")
        
        # List user sessions
        user_sessions = session_manager.list_user_sessions("test_user_123")
        print(f"✅ User has {len(user_sessions)} sessions")
        
        print("\n🎉 BigQuery session storage demo completed successfully!")
        print("\n📊 Benefits of BigQuery append-only pattern:")
        print("   • No streaming buffer update conflicts")
        print("   • Complete audit trail of all session events")
        print("   • Efficient querying with partitioning and clustering")
        print("   • Scales to handle millions of sessions")
        
    except ImportError as e:
        print(f"❌ BigQuery not available: {e}")
        print("💡 Install with: pip install google-cloud-bigquery")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure GOOGLE_CLOUD_PROJECT is set and you have BigQuery access")


if __name__ == "__main__":
    main()
