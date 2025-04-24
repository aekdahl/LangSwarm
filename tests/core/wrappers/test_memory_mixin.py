# tests/test_memory_mixin.py

import pytest
from unittest.mock import MagicMock

from langswarm.core.wrappers.memory_mixin import MemoryMixin


class DummyAgent:
    def __init__(self, memory=None):
        self.memory = memory


class DummyMemory:
    def __init__(self, with_chat_memory=True):
        self.chat_memory = MagicMock() if with_chat_memory else None
        self.load_memory_variables = MagicMock()
        self.save_context = MagicMock()


@pytest.fixture
def mixin():
    return MemoryMixin()


def test_initialize_memory_from_agent(mixin):
    dummy_memory = DummyMemory()
    agent = DummyAgent(memory=dummy_memory)
    memory = mixin._initialize_memory(agent, None, [])
    assert memory is dummy_memory


def test_initialize_memory_from_input(mixin):
    dummy_memory = DummyMemory()
    agent = DummyAgent()
    memory = mixin._initialize_memory(agent, dummy_memory, [])
    assert memory is dummy_memory


def test_initialize_memory_invalid_input(mixin):
    agent = DummyAgent()
    invalid_memory = object()
    with pytest.raises(ValueError):
        mixin._initialize_memory(agent, invalid_memory, [])


def test_add_user_message(mixin):
    dummy_memory = DummyMemory()
    mixin.memory = dummy_memory
    mixin.add_user_message("Hello")
    dummy_memory.chat_memory.add_user_message.assert_called_once_with("Hello")


def test_add_user_message_raises_if_invalid(mixin):
    mixin.memory = object()
    with pytest.raises(ValueError):
        mixin.add_user_message("Hello")


def test_add_ai_message(mixin):
    dummy_memory = DummyMemory()
    mixin.memory = dummy_memory
    mixin.add_ai_message("Hi")
    dummy_memory.chat_memory.add_ai_message.assert_called_once_with("Hi")


def test_add_ai_message_raises_if_invalid(mixin):
    mixin.memory = object()
    with pytest.raises(ValueError):
        mixin.add_ai_message("Hi")
