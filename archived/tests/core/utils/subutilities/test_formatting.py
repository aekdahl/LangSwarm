import pytest
import json
from langswarm.core.utils.subutilities.formatting import Formatting


@pytest.fixture
def formatter():
    return Formatting()


def test_valid_request_calls(formatter):
    valid = "request:tools|summarizer"
    assert formatter._is_valid_request_calls_in_text(valid) is None

    invalid = "request:tools|bad|extra"
    assert "Incorrect format" in formatter._is_valid_request_calls_in_text(invalid)


def test_valid_use_calls(formatter):
    valid = "execute_tool:summarizer|summarize|{\"text\": \"some input\"}"
    assert formatter._is_valid_use_calls_in_text(valid) is None

    invalid = "execute_tool:summarizer|partial"
    assert "Incorrect format" in formatter._is_valid_use_calls_in_text(invalid)


def test_sanitize_json_balances_brackets_and_quotes(formatter):
    unbalanced = '{"name": "test", "value": 42,'
    fixed = formatter._sanitize_json_string(unbalanced)
    assert fixed.endswith("}") or fixed.endswith("}]")  # rough balance check


def test_escape_unescaped_quotes_in_json_values(formatter):
    text = '{"message": "This is a \\"bad\\" quote"}'
    escaped = formatter.escape_unescaped_quotes_in_json_values(text)
    assert json.loads(escaped)  # should not raise error


def test_fix_trailing_commas(formatter):
    broken_json = '{"a": 1, "b": 2,}'
    cleaned = formatter._fix_trailing_commas(broken_json)
    assert cleaned == '{"a": 1, "b": 2}'


def test_is_valid_json(formatter):
    assert formatter.is_valid_json('{"a": 1}')
    assert not formatter.is_valid_json('{"a": 1')


def test_is_valid_python(formatter):
    assert formatter.is_valid_python("def x():\n return 1")
    assert not formatter.is_valid_python("def x(:")


def test_is_valid_yaml(formatter):
    assert formatter.is_valid_yaml("a: 1\nb: 2")
    #assert not formatter.is_valid_yaml("a: 1\n  b")


def test_clear_markdown_removes_fences(formatter):
    md_code = "```json\n{\"a\":1}\n```"
    assert formatter.clear_markdown(md_code).strip() == '{\"a\":1}'


def test_clean_text_removes_unicode(formatter):
    assert formatter.clean_text("Unicode\u00a0text") == "Unicode text"


def test_safe_str_to_int(formatter):
    assert formatter.safe_str_to_int("Estimate: 42 items") == 42
    assert formatter.safe_str_to_int("None") == 0
