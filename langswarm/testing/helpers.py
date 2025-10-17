"""
Testing utilities for LangSwarm applications.

Provides mock agents and helpers for testing without making real API calls.
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
from datetime import datetime
import uuid


class MockAgent:
    """Mock agent for testing without API calls.
    
    Example:
        >>> agent = MockAgent(["Hello!", "How can I help?"])
        >>> response = await agent.chat("Hi")
        >>> assert response == "Hello!"
        >>> assert agent.history[0]["user"] == "Hi"
    """
    
    def __init__(
        self, 
        responses: Optional[List[str]] = None,
        model: str = "mock-model",
        raise_on_exhausted: bool = True
    ):
        """Initialize mock agent.
        
        Args:
            responses: List of responses to return in order
            model: Model name for testing
            raise_on_exhausted: Raise error when responses exhausted
        """
        self.responses = responses or ["Mock response"]
        self.response_iter = iter(self.responses)
        self.model = model
        self.provider = "mock"
        self.raise_on_exhausted = raise_on_exhausted
        
        # Tracking
        self.history: List[Dict[str, Any]] = []
        self._usage_stats = {
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "request_count": 0
        }
        
        # Memory simulation
        self.memory_enabled = False
        self._conversation_history = []
    
    async def chat(self, message: str) -> str:
        """Simulate chat interaction."""
        # Record the interaction
        self.history.append({
            "timestamp": datetime.now(),
            "user": message,
            "id": str(uuid.uuid4())
        })
        
        # Update stats
        self._usage_stats["request_count"] += 1
        self._usage_stats["total_tokens"] += len(message.split()) * 2  # Rough estimate
        
        # Get response
        try:
            response = next(self.response_iter)
        except StopIteration:
            if self.raise_on_exhausted:
                raise ValueError(f"No more mock responses available (used {len(self.history)})")
            response = "No more responses configured"
        
        # Record response
        self.history[-1]["assistant"] = response
        
        # Handle memory if enabled
        if self.memory_enabled:
            self._conversation_history.append({"role": "user", "content": message})
            self._conversation_history.append({"role": "assistant", "content": response})
        
        # Simulate some delay
        await asyncio.sleep(0.01)
        
        return response
    
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        """Simulate streaming chat."""
        response = await self.chat(message)
        
        # Stream the response word by word
        words = response.split()
        for i, word in enumerate(words):
            if i > 0:
                yield " "
            yield word
            await asyncio.sleep(0.01)  # Simulate streaming delay
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return self._usage_stats.copy()
    
    def reset(self):
        """Reset the mock agent."""
        self.response_iter = iter(self.responses)
        self.history = []
        self._usage_stats = {
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "request_count": 0
        }
        self._conversation_history = []


class ConversationRecorder:
    """Record conversations for testing and debugging.
    
    Example:
        >>> recorder = ConversationRecorder()
        >>> agent = recorder.wrap(real_agent)
        >>> await agent.chat("Hello")
        >>> recorder.save("test_conversation.json")
    """
    
    def __init__(self):
        self.conversations: List[Dict[str, Any]] = []
        self.current_conversation: Optional[Dict[str, Any]] = None
    
    def wrap(self, agent):
        """Wrap an agent to record its conversations."""
        original_chat = agent.chat
        recorder = self
        
        async def recorded_chat(message: str) -> str:
            start_time = datetime.now()
            
            # Start new conversation if needed
            if not recorder.current_conversation:
                recorder.start_conversation(agent.model)
            
            # Call original method
            response = await original_chat(message)
            
            # Record the interaction
            recorder.record_interaction(
                message=message,
                response=response,
                duration=(datetime.now() - start_time).total_seconds()
            )
            
            return response
        
        agent.chat = recorded_chat
        return agent
    
    def start_conversation(self, model: str):
        """Start recording a new conversation."""
        self.current_conversation = {
            "id": str(uuid.uuid4()),
            "model": model,
            "started_at": datetime.now().isoformat(),
            "interactions": []
        }
        self.conversations.append(self.current_conversation)
    
    def record_interaction(self, message: str, response: str, duration: float):
        """Record a single interaction."""
        if not self.current_conversation:
            raise ValueError("No conversation started")
        
        self.current_conversation["interactions"].append({
            "timestamp": datetime.now().isoformat(),
            "user": message,
            "assistant": response,
            "duration": duration
        })
    
    def save(self, filepath: str):
        """Save recorded conversations to a file."""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.conversations, f, indent=2)
    
    def load_as_mock(self, filepath: str) -> MockAgent:
        """Load a recorded conversation as a mock agent."""
        import json
        with open(filepath) as f:
            data = json.load(f)
        
        # Extract all responses
        responses = []
        for conversation in data:
            for interaction in conversation["interactions"]:
                responses.append(interaction["assistant"])
        
        return MockAgent(responses)


def create_mock_agent(responses: Optional[List[str]] = None, **kwargs) -> MockAgent:
    """Create a mock agent for testing.
    
    Args:
        responses: List of responses to return in order
        **kwargs: Additional agent configuration
    
    Returns:
        MockAgent instance
    """
    return MockAgent(responses, **kwargs)


def assert_chat_contains(response: str, *expected_phrases: str):
    """Assert that a chat response contains expected phrases.
    
    Args:
        response: The response to check
        *expected_phrases: Phrases that should be in the response
        
    Raises:
        AssertionError: If any phrase is missing
    """
    for phrase in expected_phrases:
        assert phrase.lower() in response.lower(), \
            f"Expected phrase '{phrase}' not found in response: {response}"


def assert_conversation_flow(agent: MockAgent, expected_flow: List[tuple[str, str]]):
    """Assert that a conversation followed the expected flow.
    
    Args:
        agent: The mock agent with conversation history
        expected_flow: List of (user_message, expected_response) tuples
    """
    assert len(agent.history) >= len(expected_flow), \
        f"Expected {len(expected_flow)} interactions, but only {len(agent.history)} occurred"
    
    for i, (expected_user, expected_response) in enumerate(expected_flow):
        actual_user = agent.history[i]["user"]
        actual_response = agent.history[i]["assistant"]
        
        assert expected_user == actual_user, \
            f"Interaction {i}: Expected user message '{expected_user}', got '{actual_user}'"
        
        if expected_response:  # Allow None to skip response check
            assert expected_response in actual_response, \
                f"Interaction {i}: Expected response to contain '{expected_response}', got '{actual_response}'"