from langswarm.core.utils.misc import StripTags, SafeMap


def test_strip_tags_removes_html():
    parser = StripTags()
    html = "<html><body><h1>Header</h1><p>This is a <b>test</b>.</p></body></html>"
    parser.feed(html)
    output = parser.get_data()
    assert "Header" in output
    assert "test" in output
    assert "<" not in output and ">" not in output


def test_safe_map_returns_key_as_placeholder():
    data = SafeMap({"name": "Alice"})
    assert data["name"] == "Alice"
    assert data["missing_key"] == "{missing_key}"
