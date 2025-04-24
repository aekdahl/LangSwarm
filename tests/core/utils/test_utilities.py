import pytest
from unittest.mock import patch
from langswarm.core.utils.utilities import Utils


@pytest.fixture
def utils():
    return Utils()


def test_generate_short_uuid_length(utils):
    short_id = utils.generate_short_uuid(10)
    assert short_id.startswith("z")
    assert len(short_id) == 10


def test_generate_md5_hash(utils):
    assert utils.generate_md5_hash("test") == "098f6bcd4621d373cade4e832627b4f6"


def test_get_api_key_from_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "env_key")
    assert Utils()._get_api_key("openai", "") == "env_key"


def test_get_api_key_fallback_direct():
    assert Utils()._get_api_key("openai", "direct_key") == "direct_key"


def test_get_api_key_missing_raises():
    with pytest.raises(ValueError):
        Utils()._get_api_key("openai", "")


def test_bot_log_stores_entries(utils):
    utils.bot_log("bot1", "Started")
    utils.bot_log("bot2", "Completed")
    assert utils.bot_logs[0] == ("bot1", "Started")
    assert len(utils.bot_logs) == 2


@patch("tiktoken.encoding_for_model")
def test_price_tokens_with_tiktoken(mock_encoding):
    mock_encoding.return_value.encode.return_value = list(range(123))
    tokens, price = Utils().price_tokens_from_string("dummy", price_per_million=1)
    assert tokens == 123
    assert round(price, 4) == 0.0001


@patch("tiktoken.encoding_for_model", side_effect=Exception("simulate failure"))
def test_truncate_text_fallback(mock_encoding):
    truncated = Utils().truncate_text_to_tokens("This is some long text", max_tokens=5)
    assert isinstance(truncated, str)
