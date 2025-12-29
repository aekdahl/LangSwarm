
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import json
from datetime import datetime
import sys
import logging

# Configure logging to see errors
logging.basicConfig(level=logging.DEBUG)

# Mock asyncpg if not available
sys.modules["asyncpg"] = MagicMock()

from langswarm_memory.backends import PostgresBackend, PostgresSession
from langswarm_memory.interfaces import SessionMetadata, SessionStatus, Message, MessageRole

class TestPostgresBackend(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config = {
            "url": "postgresql://user:pass@localhost:5432/db",
            "table_prefix": "test_"
        }
        self.backend = PostgresBackend(self.config)
        
        # Setup pool mock correctly for async context manager
        # async with pool.acquire() as conn:
        self.connection = AsyncMock()
        
        self.pool_context = MagicMock()
        self.pool_context.__aenter__.return_value = self.connection
        self.pool_context.__aexit__.return_value = None
        
        self.pool_mock = MagicMock()
        self.pool_mock.acquire.return_value = self.pool_context
        self.pool_mock.close = AsyncMock()
        
        self.backend._pool = self.pool_mock

    async def test_connect_creates_pool_and_tables(self):
        # We need to mock create_pool to return our pre-configured pool mock
        with patch("langswarm_memory.backends.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_create_pool.return_value = self.pool_mock
            
            result = await self.backend.connect()
            
            self.assertTrue(result)
            mock_create_pool.assert_called_once()
            
            # Verify table creation calls
            # connection.execute should have been called multiple times
            self.assertTrue(self.connection.execute.call_count >= 3)
            
            # Check for CREATE TABLE statements
            calls = self.connection.execute.call_args_list
            table_creation_calls = [str(c) for c in calls if "CREATE TABLE" in str(c)]
            self.assertGreaterEqual(len(table_creation_calls), 3)

    async def test_create_session(self):
        metadata = SessionMetadata(
            session_id="test-session",
            user_id="user1",
            agent_id="agent1",
            status=SessionStatus.ACTIVE
        )
        
        # Mock connection behavior just in case
        self.connection.execute.return_value = None
        
        session = await self.backend.create_session(metadata)
        
        self.assertIsInstance(session, PostgresSession)
        self.assertEqual(session.session_id, "test-session")
        
        # Verify insert
        self.connection.execute.assert_called()
        # Check that one of the calls was INSERT INTO sessions
        found = False
        for call in self.connection.execute.call_args_list:
            args, _ = call
            if "INSERT INTO public.test_sessions" in args[0]:
                self.assertEqual(args[1], "test-session")
                found = True
                break
        self.assertTrue(found, "Session insert not found")

    async def test_persist_message(self):
        # Setup session
        metadata = SessionMetadata(session_id="test-session")
        session = PostgresSession(metadata, self.backend)
        
        message = Message(
            role=MessageRole.USER,
            content="Hello world",
            message_id="msg1"
        )
        
        await session._persist_message(message)
        
        # Verify insert
        found = False
        for call in self.connection.execute.call_args_list:
            args, _ = call
            if "INSERT INTO public.test_messages" in args[0]:
                self.assertEqual(args[1], "msg1") # message_id
                self.assertEqual(args[3], "user") # role value
                self.assertEqual(args[4], "Hello world") # content
                found = True
                break
        self.assertTrue(found, "Message insert not found")

    async def test_vector_search_logic(self):
        # Enable vector search
        self.backend._enable_vector = True
        self.backend.embedding_provider = AsyncMock()
        self.backend.embedding_provider.embed_text.return_value = [0.1, 0.2, 0.3]
        
        # Mock fetch return (for search_messages)
        # Note: search_messages uses `conn.fetch`
        self.connection.fetch.return_value = [
            {
                "message_id": "msg1",
                "role": "assistant",
                "content": "Response",
                "timestamp": datetime.now(),
                "metadata": None,
                "function_call": None,
                "tool_calls": None
            }
        ]
        
        results = await self.backend.search_messages("query", session_id="sess1")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Response")
        
        # Verify embedding generation
        self.backend.embedding_provider.embed_text.assert_called_with("query")
        
        # Verify SQL contains vector operator
        found = False
        for call in self.connection.fetch.call_args_list:
            args, _ = call
            if "ORDER BY embedding <=>" in args[0]:
                found = True
                break
        self.assertTrue(found, "Vector search SQL not found")

if __name__ == "__main__":
    unittest.main()
