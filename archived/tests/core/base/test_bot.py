import pytest
from types import SimpleNamespace
from langswarm.core.base.bot import LLM


class DummyUtils:
    def __init__(self):
        self.logs = []

    def _get_api_key(self, provider, api_key):
        return api_key or "dummy-key"

    def bot_log(self, bot, message):
        self.logs.append((bot, message))

    def clean_text(self, text, remove_linebreaks=False):
        return text

    def update_price_tokens_use_estimates(self, *args, **kwargs):
        pass


@pytest.fixture
def utils():
    return DummyUtils()


def test_llm_initialization_with_wrapper(utils):
    bot = LLM(name="test_bot", provider="wrapper", model="dummy", utils=utils)
    assert bot.name == "test_bot"
    assert bot.provider == "wrapper"


def test_add_message_and_get_last_memory(utils):
    bot = LLM(name="test_bot", provider="wrapper", model="dummy", utils=utils)
    bot.add_message("Hi there", role="user")
    assert bot.get_last_in_memory() == "Hi there"
    assert bot.in_memory[-1]["role"] == "user"


def test_reset_clears_memory(utils):
    bot = LLM(name="test_bot", provider="wrapper", model="dummy", utils=utils)
    bot.add_message("A message")
    bot.reset(clear=True)
    assert bot.in_memory == []


def test_remove_deletes_latest(utils):
    bot = LLM(name="test_bot", provider="wrapper", model="dummy", utils=utils)
    bot.add_message("User", role="user")
    bot.add_message("Assistant", role="assistant")
    bot.remove()
    assert len(bot.in_memory) == 1


def test_set_memory(utils):
    bot = LLM(name="test_bot", provider="wrapper", model="dummy", utils=utils)
    bot.set_memory([{"role": "assistant", "content": "Mem test"}])
    assert bot.in_memory[-1]["content"] == "Mem test"


def test_get_memory(utils):
    bot = LLM(name="test_bot", provider="wrapper", model="dummy", utils=utils)
    bot.set_memory([{"role": "assistant", "content": "Line 1"}, {"role": "user", "content": "Line 2"}])
    result = bot.get_memory()
    assert isinstance(result, list)
