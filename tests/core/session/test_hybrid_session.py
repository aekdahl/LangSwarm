
import unittest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime
from uuid import uuid4

# Imports assumed to be available based on project structure
from langswarm.core.session.base import SessionManager, BaseSession, SessionBackend, SessionContext
from langswarm.core.session.providers import BaseStatelessProviderSession, IProviderSession, SessionMessage, MessageRole
from langswarm.core.session.storage import InMemorySessionStorage
from langswarm.core.session.interfaces import SessionStatus

class MockClaudeSession(BaseStatelessProviderSession):
    """Mock stateless provider for testing"""
    async def send_message(self, provider_session_id, message, role=MessageRole.USER):
        if provider_session_id not in self._conversations:
            raise Exception("Session not found")
        await self._add_to_history(provider_session_id, "user", message)
        response_content = f"Echo: {message}"
        await self._add_to_history(provider_session_id, "assistant", response_content)
        return SessionMessage(
            id=f"msg_mock_{uuid4().hex}", 
            role=MessageRole.ASSISTANT, 
            content=response_content,
            timestamp=datetime.now(),
            metadata={}
        )

class TestHybridSession(unittest.IsolatedAsyncioTestCase):
    async def test_hybrid_flow(self):
        print("\n--- Testing Hybrid Session Flow ---")
        
        # Setup
        storage = InMemorySessionStorage()
        provider_session = MockClaudeSession()
        manager = SessionManager(storage=storage)
        manager.add_provider_session("claude", provider_session)
        
        # 1. Create HYBRID session
        print("1. Creating Session...")
        session = await manager.create_session(
            user_id="user1", 
            provider="claude", 
            model="claude-3-opus", 
            backend=SessionBackend.HYBRID
        )
        self.assertEqual(session.context.backend, SessionBackend.HYBRID)
        provider_id = session.context.provider_session_id
        print(f"   Created Session ID: {session.session_id}")
        print(f"   Provider Session ID: {provider_id}")
        
        # 2. Send message
        print("2. Sending Message...")
        response = await session.send_message("Hello Hybrid")
        self.assertEqual(response.content, "Echo: Hello Hybrid")
        print("   Message sent and response received.")
        
        # Verify persistence
        print("3. Verifying Persistence...")
        # InMemorySessionStorage.load_session returns (messages, context)
        loaded_data = await storage.load_session(session.session_id)
        self.assertIsNotNone(loaded_data)
        
        stored_msgs, stored_context = loaded_data
        
        self.assertEqual(len(stored_msgs), 2) # User + Assistant
        print(f"   Storage has {len(stored_msgs)} messages.")
        
        # Verify provider memory
        self.assertIn(provider_id, provider_session._conversations)
        self.assertEqual(len(provider_session._conversations[provider_id]), 2)
        print("   Provider memory updated.")
        
        # 3. Simulate Restart (New Manager, Empty Provider Session)
        print("4. Simulating App Restart (Empty Memory)...")
        new_provider_session = MockClaudeSession()
        new_manager = SessionManager(storage=storage) # Re-use persist storage
        new_manager.add_provider_session("claude", new_provider_session) # New empty provider session
        
        # Ensure new provider session is empty
        self.assertNotIn(provider_id, new_provider_session._conversations)
        
        # 4. Load Session
        print("5. Loading Session from Storage...")
        loaded_session = await new_manager.get_session(session.session_id)
        self.assertIsNotNone(loaded_session)
        
        # Verify Hydration
        print("6. Verifying Hydration...")
        # New provider session should now have the conversation
        self.assertIn(provider_id, new_provider_session._conversations)
        self.assertEqual(len(new_provider_session._conversations[provider_id]), 2)
        messages = new_provider_session._conversations[provider_id]
        self.assertEqual(messages[0]["content"], "Hello Hybrid")
        self.assertEqual(messages[1]["content"], "Echo: Hello Hybrid")
        
        print("✅ Hydration successful! stateless provider restored from storage.")

if __name__ == "__main__":
    unittest.main()
